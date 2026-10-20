"""Avatar uploads: only the caller's own uploaded image asset may become the avatar."""
import base64

import pytest

from test_mobile_client import auth, client  # noqa: F401
from app.core import file_urls

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII="
)
MP4 = b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 16


@pytest.fixture
def uploads(monkeypatch, tmp_path):
    from app.api import ai_workshop
    root = tmp_path / "uploads"
    root.mkdir()
    monkeypatch.setattr(ai_workshop, "STATIC_UPLOADS_DIR", str(root))
    return root


def upload(client, user, name="avatar.png", content=PNG):
    response = client.post("/api/ai/assets/upload", headers=user, files={"file": (name, content, "image/png")})
    assert response.status_code == 200, response.text
    return response.json()["data"]["file_url"]


def save_profile(client, user, avatar_url):
    return client.put("/api/mobile/me/profile", headers=user,
                      json={"nickname": "非遗小传人", "avatar_url": avatar_url})


def test_uploaded_avatar_is_saved_and_returned_by_me(client, uploads):
    file_url = upload(client, auth())
    assert (uploads / file_url.rsplit("/", 1)[-1]).read_bytes() == PNG
    saved = save_profile(client, auth(), file_url)
    assert saved.status_code == 200, saved.text
    assert saved.json()["data"]["avatar_url"] == file_url
    me = client.get("/api/auth/me", headers=auth()).json()["data"]
    assert me["avatar_url"] == file_url and me["nickname"] == "非遗小传人"


def test_avatar_cannot_reference_another_users_asset(client, uploads):
    other_url = upload(client, auth(4))
    rejected = save_profile(client, auth(), other_url)
    assert rejected.status_code == 404 and rejected.json()["message"] == "头像资源无效"
    assert client.get("/api/auth/me", headers=auth()).json()["data"]["avatar_url"] is None
    assert save_profile(client, auth(4), other_url).status_code == 200


@pytest.mark.parametrize("bad_url", [
    "/static/generated/avatar.svg",
    file_urls.signed_url("/static/generated/avatar.svg"),
    "/static/uploads/not-uploaded.png",
    "/static/images/default_avatar.svg",
])
def test_avatar_rejects_generated_signed_or_foreign_paths(client, uploads, bad_url):
    rejected = save_profile(client, auth(), bad_url)
    assert rejected.status_code >= 400 and rejected.status_code < 500, rejected.text
    assert client.get("/api/auth/me", headers=auth()).json()["data"]["avatar_url"] is None


def test_avatar_rejects_own_uploaded_video(client, uploads):
    video_url = upload(client, auth(), name="clip.mp4", content=MP4)
    assert video_url.endswith(".mp4")
    rejected = save_profile(client, auth(), video_url)
    assert rejected.status_code == 404 and rejected.json()["message"] == "头像资源无效"
    assert client.get("/api/auth/me", headers=auth()).json()["data"]["avatar_url"] is None
