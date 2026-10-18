"""Image generation uses only the connection configured in the management UI."""
import base64
import binascii
import io
import ipaddress
import json
import socket
from pathlib import Path
from urllib.parse import urlsplit
from typing import Literal

import httpx
from openai import OpenAI, APIStatusError, APITimeoutError, APIConnectionError
from openai.types import ImagesResponse
from PIL import Image
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.core.files import resolve_static_file
from app.models.entities import Asset, SysConfig

MAX_IMAGE_BYTES = 20 * 1024 * 1024
MAX_IMAGE_PIXELS = 16_777_216
GENERATED_DIR = Path(__file__).resolve().parents[2] / "static" / "generated"
KEY_MASK = "********"


class ImageSettings(BaseModel):
    enabled: bool = False
    use_text_connection: bool = True
    api_base: str = Field(default="", max_length=500)
    api_key: str | None = Field(default=None, max_length=4096)
    model_name: str = Field(default="", max_length=128)
    supports_edit: bool = False
    edit_transport: Literal["multipart", "json_images"] = "multipart"
    size: str = Field(default="1024x1024", pattern=r"^(auto|1024x1024|1536x1024|1024x1536|512x512|256x256)$")
    response_format: str = Field(default="auto", pattern=r"^(auto|b64_json|url)$")
    timeout_seconds: int = Field(default=120, ge=30, le=180)

    @field_validator("api_base", "model_name", "api_key")
    @classmethod
    def strip_text(cls, value):
        return value.strip() if isinstance(value, str) else value


class ImageGenerationError(Exception):
    """Only safe messages may reach users; never include upstream bodies or keys."""


def read_settings(db: Session) -> dict:
    row = db.query(SysConfig).filter_by(config_key="llm_settings").first()
    try:
        value = json.loads(row.config_value) if row else {}
        return value if isinstance(value, dict) else {}
    except (TypeError, ValueError):
        return {}


def resolve_connection(settings: dict) -> dict:
    cfg = ImageSettings.model_validate(settings.get("image_generation") or {})
    connection = settings if cfg.use_text_connection else cfg.model_dump()
    base = str(connection.get("api_base") or "").strip().rstrip("/")
    for suffix in ("/images/generations", "/images/edits"):
        if base.endswith(suffix):
            base = base[:-len(suffix)]
    key = str(connection.get("api_key") or "").strip()
    parsed = urlsplit(base)
    if (not cfg.enabled or not cfg.model_name or not key or "*" in key
            or parsed.scheme not in {"http", "https"} or not parsed.hostname
            or parsed.username or parsed.password or parsed.query or parsed.fragment):
        raise ImageGenerationError("生图服务尚未完整配置，请联系管理员在“AI 大模型与多模态接入”中设置")
    if parsed.scheme != "https" and parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise ImageGenerationError("生图服务地址须使用 HTTPS；本机测试可使用 HTTP")
    return cfg.model_dump() | {"api_base": base, "api_key": key}


def capabilities(db: Session) -> dict:
    try:
        cfg = resolve_connection(read_settings(db))
        return {"image_generation": True, "image_edit": cfg["supports_edit"]}
    except (ImageGenerationError, ValueError, TypeError):
        return {"image_generation": False, "image_edit": False}


def validate_image(data: bytes) -> tuple[str, str]:
    if not data or len(data) > MAX_IMAGE_BYTES:
        raise ImageGenerationError("图片为空或超过 20MB，请使用较小的图片")
    try:
        with Image.open(io.BytesIO(data)) as image:
            if image.format not in {"PNG", "JPEG", "WEBP"} or image.width * image.height > MAX_IMAGE_PIXELS:
                raise ImageGenerationError("仅支持不超过 1600 万像素的 PNG、JPEG 或 WebP 图片")
            fmt = image.format
            image.verify()
        # verify() is not a full pixel decode for every format.
        with Image.open(io.BytesIO(data)) as image:
            image.load()
    except ImageGenerationError:
        raise
    except Exception:
        raise ImageGenerationError("图片内容损坏或格式不受支持") from None
    return {"PNG": ("png", "image/png"), "JPEG": ("jpg", "image/jpeg"), "WEBP": ("webp", "image/webp")}[fmt]


def owned_reference(db: Session, url: str, user_id: int) -> tuple[bytes, str, str]:
    asset = db.query(Asset).filter_by(file_url=url, created_by=user_id).first()
    if not asset:
        raise ImageGenerationError("参考图不存在或不属于当前账号")
    path = resolve_static_file(url)
    if path.stat().st_size > MAX_IMAGE_BYTES:
        raise ImageGenerationError("参考图不能超过 20MB")
    data = path.read_bytes()
    extension, mime = validate_image(data)
    return data, extension, mime


def download_result(url: str) -> bytes:
    # Image URLs are untrusted provider output. Never forward the provider API key.
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ImageGenerationError("服务返回的图片下载地址无效")
    try:
        addresses = socket.getaddrinfo(parsed.hostname, parsed.port or 443, type=socket.SOCK_STREAM)
        if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
            raise ImageGenerationError("服务返回的图片地址不可访问")
        with httpx.Client(timeout=30, follow_redirects=False, trust_env=False) as client:
            with client.stream("GET", url) as response:
                response.raise_for_status()
                chunks, length = [], 0
                for chunk in response.iter_bytes():
                    length += len(chunk)
                    if length > MAX_IMAGE_BYTES:
                        raise ImageGenerationError("生成图片超过 20MB")
                    chunks.append(chunk)
                return b"".join(chunks)
    except ImageGenerationError:
        raise
    except Exception:
        raise ImageGenerationError("生成图片下载失败，请稍后重试") from None


def generate_image(cfg: dict, prompt: str, reference=None) -> bytes:
    if reference and not cfg["supports_edit"]:
        raise ImageGenerationError("当前生图模型未启用图片编辑，请移除参考图或由管理员开启图片编辑")
    parameters = {"model": cfg["model_name"], "prompt": prompt, "n": 1, "size": cfg["size"]}
    if cfg["response_format"] != "auto":
        parameters["response_format"] = cfg["response_format"]
    try:
        # No automatic retries: a timed-out paid generation may already have run.
        with OpenAI(api_key=cfg["api_key"], base_url=cfg["api_base"],
                    timeout=cfg["timeout_seconds"], max_retries=0) as client:
            if reference:
                data, extension, mime = reference
                if cfg.get("edit_transport") == "json_images":
                    image_url = f"data:{mime};base64," + base64.b64encode(data).decode("ascii")
                    response = client.post("/images/edits", cast_to=ImagesResponse, body=parameters | {"images": [{"image_url": image_url}]})
                else:
                    response = client.images.edit(image=("reference." + extension, data, mime), **parameters)
            else:
                response = client.images.generate(**parameters)
        values = response.get("data") if isinstance(response, dict) else response.data
        if not values:
            raise ImageGenerationError("模型没有返回图片，请检查模型是否支持图像生成")
        result = values[0]
        encoded = result.get("b64_json") if isinstance(result, dict) else result.b64_json
        url = result.get("url") if isinstance(result, dict) else result.url
        if encoded:
            if len(encoded) > MAX_IMAGE_BYTES * 4 // 3 + 8:
                raise ImageGenerationError("生成图片超过 20MB")
            data = base64.b64decode(encoded, validate=True)
        elif url:
            data = download_result(url)
        else:
            raise ImageGenerationError("模型没有返回有效图片")
        validate_image(data)
        return data
    except ImageGenerationError:
        raise
    except (APITimeoutError, APIConnectionError):
        raise ImageGenerationError("生图服务连接超时或中断，可先查询任务状态，再决定是否重新生成") from None
    except APIStatusError as exc:
        message = {401: "生图服务鉴权失败，请管理员检查密钥", 403: "生图服务拒绝访问，请管理员检查模型权限",
                   429: "生图服务额度不足或请求过于频繁，请稍后重试"}.get(exc.status_code,
                   "生图服务拒绝了请求，请检查模型、尺寸与图片编辑能力配置")
        raise ImageGenerationError(message) from None
    except (ValueError, binascii.Error):
        raise ImageGenerationError("模型返回的图片数据无效") from None


def build_prompt(tool: str, payload: dict) -> str:
    craft = {"BRONZE": "青铜器装饰纹样", "SHADOW_PUPPET": "中国传统皮影角色",
             "LACQUER": "漆艺装饰纹样", "EMBROIDERY": "刺绣与漆艺装饰纹样"}[tool]
    controls = {key: payload[key] for key in ("role_type", "face_style", "pattern_type", "style", "local_pattern", "color_palette") if key in payload}
    reference = "保留参考草图的主要轮廓与构图，按照文字要求完成细节与上色。" if payload.get("sketch_url") else "生成一张完整的二维设计参考图。"
    return (f"创作主题：{craft}。{reference}\n用户要求：{payload['prompt'].strip()}\n"
            f"设计参数：{json.dumps(controls, ensure_ascii=False)}\n"
            "画面清晰，避免水印、署名和无关文字。此图用于美育创意参考，不是经过验证的切割纸样或三维模型。")
