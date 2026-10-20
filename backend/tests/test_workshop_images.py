"""Exercise real SDK HTTP serialization with isolated DB/assets; no paid calls."""
import base64
import io
import json
from datetime import datetime, timedelta

import httpx
import pytest
from openai import OpenAI
from PIL import Image

from test_mobile_client import client, auth
from asset_urls import generated_file
from app.api import ai_workshop
from app.core import files, image_generation
from app.models.entities import AiTask, Asset, GrowthEvent, SysConfig, UserGrowth


def png(color="green"):
    output = io.BytesIO()
    Image.new("RGB", (32, 32), color).save(output, format="PNG")
    return output.getvalue()


@pytest.fixture
def gateway(client, monkeypatch, tmp_path):
    (tmp_path / "generated").mkdir()
    (tmp_path / "uploads").mkdir()
    monkeypatch.setattr(files, "STATIC_DIR", tmp_path)
    monkeypatch.setattr(image_generation, "GENERATED_DIR", tmp_path / "generated")
    monkeypatch.setattr(ai_workshop, "SessionLocal", client.sessions)
    requests = []
    def respond(request):
        requests.append(request)
        return httpx.Response(200, json={"created": 123, "data": [{"b64_json": base64.b64encode(png()).decode()}]})
    def sdk(**kwargs):
        return OpenAI(**kwargs, http_client=httpx.Client(transport=httpx.MockTransport(respond)))
    monkeypatch.setattr(image_generation, "OpenAI", sdk)
    cfg = {"api_key": "existing-text-secret", "api_base": "https://text.invalid/v1", "model_name": "text-model",
           "image_generation": image_generation.ImageSettings(enabled=True, use_text_connection=False,
               api_base="https://image.invalid/v1", api_key="test-image-secret", model_name="image-model",
               supports_edit=True, response_format="b64_json").model_dump()}
    with client.sessions() as db:
        db.add(SysConfig(config_key="llm_settings", config_value=json.dumps(cfg)))
        db.commit()
    return requests, cfg, tmp_path


def create(client, tool="BRONZE", **changes):
    body = {"tool_type": tool, "generation_mode": "AI", "request_id": "test-image-request-0001",
            "input_payload": {"prompt": "云雷纹，铜绿与金色", "color_palette": ["#226644"]}}
    return client.post("/api/ai/tasks", headers=auth(), json=body | changes)


@pytest.mark.parametrize("tool", ["BRONZE", "SHADOW_PUPPET", "LACQUER", "EMBROIDERY"])
def test_real_sdk_contract_save_collect_read_publish_and_retry_once(client, gateway, tool):
    requests, cfg, root = gateway
    response = create(client, tool)
    assert response.status_code == 200, response.text
    task_id = response.json()["data"]["task_id"]
    result = client.get(f"/api/ai/tasks/{task_id}", headers=auth()).json()["data"]
    assert result["status"] == "SUCCESS", result
    assert result["result"]["generation_method"] == "ai_image"
    assert result["result"]["image_model"] == "image-model"
    assert result["result"]["vector_svg_url"] is None
    assert result["result"]["print_template_url"] is None
    url = result["result"]["colored_image_url"]
    assert generated_file(root / "generated", url).read_bytes() == png()
    for _ in range(2):
        assert create(client, tool).json()["data"]["task_id"] == task_id
        assert client.post(f"/api/ai/tasks/{task_id}/favorite", headers=auth(), json={"collected": True}).json()["data"]["collected"]
    collections = client.get("/api/mobile/me/collections", headers=auth()).json()["data"]
    assert collections[0]["task_id"] == task_id
    assert client.get("/api/mobile/me/collections", headers=auth(4)).json()["data"] == []
    assert client.get(f"/api/ai/tasks/{task_id}", headers=auth(4)).json()["code"] != 0
    post = client.post("/api/community/posts", headers=auth(), json={"title": "纹样作品", "content": "我的创作",
        "category": tool, "source_task_id": task_id, "cover_url": url, "gallery": [url]})
    assert post.status_code == 200 and post.json()["code"] == 0, post.text
    assert len(requests) == 1
    assert str(requests[0].url) == "https://image.invalid/v1/images/generations"
    assert requests[0].headers["authorization"] == "Bearer test-image-secret"
    assert json.loads(requests[0].content)["model"] == "image-model"
    with client.sessions() as db:
        assert db.query(AiTask).count() == 1
        assert db.query(GrowthEvent).filter_by(event_type="AI_CREATE").count() == 1
        assert db.get(UserGrowth, 3).energy_value >= 120


@pytest.mark.parametrize("transport", ["multipart", "json_images"])
def test_reference_image_reaches_editor_in_supported_transport(client, gateway, transport):
    requests, cfg, root = gateway
    (root / "uploads" / "sketch.png").write_bytes(png("red"))
    cfg["image_generation"]["edit_transport"] = transport
    with client.sessions() as db:
        db.query(SysConfig).first().config_value = json.dumps(cfg)
        db.add(Asset(asset_type="IMAGE", file_url="/static/uploads/sketch.png", object_key="uploads/sketch.png", mime_type="image/png", created_by=3))
        db.commit()
    response = create(client, "EMBROIDERY", input_payload={"prompt": "保留轮廓，改成绿色刺绣", "sketch_url": "/static/uploads/sketch.png"})
    task_id = response.json()["data"]["task_id"]
    detail = client.get("/api/ai/tasks/" + task_id, headers=auth()).json()["data"]
    assert detail["status"] == "SUCCESS", detail.get("error_message")
    assert detail["result"]["completed_sketch_url"] == detail["result"]["colored_image_url"]
    assert len(requests) == 1 and requests[0].url.path.endswith("/images/edits")
    if transport == "json_images":
        ref = json.loads(requests[0].content)["images"][0]["image_url"]
        assert ref.startswith("data:image/png;base64,")
        assert base64.b64decode(ref.split(",")[1]) == png("red")
    else:
        assert "multipart/form-data" in requests[0].headers["content-type"]
        assert png("red") in requests[0].content


def test_admin_masks_keys_preserves_omitted_image_settings_and_can_clear(client, gateway):
    requests, cfg, root = gateway
    assert client.get("/api/admin/settings", headers=auth(2, "TEACHER")).status_code == 403
    settings = client.get("/api/admin/settings", headers=auth(1, "ADMIN")).json()["data"]
    assert settings["llm_settings"]["api_key"] == "********"
    assert settings["llm_settings"]["image_generation"]["api_key"] == "********"
    assert "test-image-secret" not in json.dumps(settings)
    result = client.post("/api/admin/settings", headers=auth(1, "ADMIN"), json=settings)
    assert result.status_code == 200, result.text
    settings["llm_settings"].pop("image_generation")
    assert client.post("/api/admin/settings", headers=auth(1, "ADMIN"), json=settings).status_code == 200
    with client.sessions() as db:
        saved = image_generation.read_settings(db)
        assert saved["api_key"] == cfg["api_key"]
        assert saved["image_generation"]["api_key"] == "test-image-secret"
    settings["llm_settings"]["image_generation"] = {"enabled": False, "api_key": ""}
    assert client.post("/api/admin/settings", headers=auth(1, "ADMIN"), json=settings).status_code == 200
    with client.sessions() as db:
        assert image_generation.read_settings(db)["image_generation"]["api_key"] == ""
    assert requests == []


def test_model_access_probe_does_not_generate_or_claim_verified_generation(client, gateway):
    settings = client.get("/api/admin/settings", headers=auth(1, "ADMIN")).json()["data"]["llm_settings"]
    result = client.post("/api/admin/settings/test-image", headers=auth(1, "ADMIN"), json=settings)
    assert result.status_code == 200 and result.json()["data"]["verified_generation"] is False
    assert len(gateway[0]) == 1 and gateway[0][0].method == "GET"
    with client.sessions() as db:
        assert db.query(AiTask).count() == 0


def test_unsupported_probe_is_explicitly_unverified(client, gateway, monkeypatch):
    def unsupported(**kwargs):
        raise RuntimeError("Upstream body may contain secrets; do not expose it")
    monkeypatch.setattr(image_generation, "OpenAI", unsupported)
    settings = client.get("/api/admin/settings", headers=auth(1, "ADMIN")).json()["data"]["llm_settings"]
    data = client.post("/api/admin/settings/test-image", headers=auth(1, "ADMIN"), json=settings).json()["data"]
    assert data["model_access_verified"] is False and data["verified_generation"] is False
    assert "不代表生图不可用" in data["message"]
    assert "secrets" not in json.dumps(data)


def test_unconfigured_ai_rejects_without_task_or_reward_and_local_survives(client):
    assert client.get("/api/ai/capabilities").json()["data"]["image_generation"] is False
    assert create(client).status_code == 503
    with client.sessions() as db:
        assert db.query(AiTask).count() == 0
        assert db.query(GrowthEvent).count() == 0


def test_explicit_local_template_does_not_call_a_configured_model(client, gateway, monkeypatch):
    def unexpected(*args, **kwargs):
        raise AssertionError("A local-only request must not invoke the language model")
    monkeypatch.setattr(ai_workshop, "get_llm_client_and_config", unexpected)
    monkeypatch.setattr(ai_workshop, "save_generated_asset", lambda name, content: "/static/generated/" + name)
    response = create(client, generation_mode="LOCAL")
    task_id = response.json()["data"]["task_id"]
    detail = client.get("/api/ai/tasks/" + task_id, headers=auth()).json()["data"]
    assert detail["status"] == "SUCCESS"
    assert detail["result"].get("generation_method") != "ai_image"
    assert gateway[0] == []


def test_failed_response_is_safe_and_retry_identity_does_not_recall_provider(client, gateway, monkeypatch):
    requests, cfg, root = gateway
    def fail(*args, **kwargs):
        raise image_generation.ImageGenerationError("生图服务额度不足或请求过于频繁，请稍后重试")
    monkeypatch.setattr(image_generation, "generate_image", fail)
    task_id = create(client).json()["data"]["task_id"]
    assert create(client).json()["data"]["task_id"] == task_id
    changed = create(client, input_payload={"prompt": "修改后的提示词"})
    assert changed.status_code == 409
    task = client.get("/api/ai/tasks/" + task_id, headers=auth()).json()["data"]
    assert task["status"] == "FAILED" and "额度" in task["error_message"]
    with client.sessions() as db:
        assert db.query(GrowthEvent).count() == 0
        assert db.query(Asset).filter_by(created_by=3).count() == 0


def test_cancel_during_upstream_call_drops_result_and_reward(client, gateway, monkeypatch):
    def cancel(*args, **kwargs):
        with client.sessions() as db:
            task = db.query(AiTask).first()
            task.status = "CANCELLED"
            db.commit()
        return png()
    monkeypatch.setattr(image_generation, "generate_image", cancel)
    task_id = create(client).json()["data"]["task_id"]
    assert client.get("/api/ai/tasks/" + task_id, headers=auth()).json()["data"]["status"] == "CANCELLED"
    with client.sessions() as db:
        assert db.query(GrowthEvent).count() == 0
        assert db.query(Asset).filter_by(created_by=3).count() == 0
    assert list(gateway[2].joinpath("generated").iterdir()) == []


def test_interrupted_tasks_expire_without_automatic_provider_retry(client, gateway):
    with client.sessions() as db:
        db.add(AiTask(task_id="a" * 32, user_id=3, tool_type="BRONZE", status="RUNNING",
            input_json={"_generation_mode": "AI", "prompt": "旧任务"}, updated_at=datetime.utcnow() - timedelta(minutes=11)))
        db.commit()
    task = client.get("/api/ai/tasks/" + "a" * 32, headers=auth()).json()["data"]
    assert task["status"] == "FAILED" and "中断" in task["error_message"]
    assert gateway[0] == []


@pytest.mark.parametrize("payload", [b"<svg>fake</svg>", b"not-an-image", b"\x89PNG\r\n\x1a\n"])
def test_invalid_image_bytes_are_rejected(payload):
    with pytest.raises(image_generation.ImageGenerationError):
        image_generation.validate_image(payload)


@pytest.mark.parametrize("url", ["http://example.com/test.png", "https://127.0.0.1/x", "https://[::1]/x", "file:///etc/passwd"])
def test_untrusted_result_urls_cannot_read_private_resources(url):
    with pytest.raises(image_generation.ImageGenerationError):
        image_generation.download_result(url)
