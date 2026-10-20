import re
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree

from defusedxml.ElementTree import fromstring
from defusedxml.common import DefusedXmlException
from fastapi import HTTPException

STATIC_DIR = Path(__file__).resolve().parents[2] / "static"
SVG_ELEMENTS = {
    "svg", "g", "path", "rect", "circle", "ellipse", "line", "polyline", "polygon",
    "text", "tspan", "defs", "linearGradient", "radialGradient", "stop", "pattern",
    "clipPath", "mask", "filter", "feDropShadow", "feGaussianBlur", "feOffset",
    "feBlend", "feComposite", "feColorMatrix", "feMerge", "feMergeNode", "symbol",
    "use", "title", "desc",
}
SVG_ATTRIBUTES = set("""id x y x1 x2 y1 y2 cx cy r rx ry d points width height viewBox
    fill fill-opacity fill-rule stroke stroke-width stroke-opacity stroke-linecap
    stroke-linejoin stroke-dasharray stroke-dashoffset opacity transform
    font-size font-family font-weight font-style text-anchor letter-spacing
    dominant-baseline dx dy gradientUnits gradientTransform offset stop-color
    stop-opacity patternUnits patternTransform clip-path clipPathUnits mask
    maskUnits filter filterUnits stdDeviation flood-color flood-opacity in in2
    result mode operator type values preserveAspectRatio href version color
    xmlns textLength lengthAdjust spreadMethod fr fx fy""".split())


def sanitize_svg(content: bytes | str) -> str:
    if len(content) > 5 * 1024 * 1024:
        raise ValueError("SVG 文件过大")
    try:
        root = fromstring(content)
    except (ElementTree.ParseError, DefusedXmlException, ValueError) as exc:
        raise ValueError("SVG 格式无效") from exc
    if root.tag != "{http://www.w3.org/2000/svg}svg":
        raise ValueError("文件必须是 SVG 文档")
    for node in root.iter():
        if not node.tag.startswith("{http://www.w3.org/2000/svg}"):
            raise ValueError("SVG 包含不支持的命名空间")
        if node.tag.rsplit("}", 1)[-1] not in SVG_ELEMENTS:
            raise ValueError("SVG 包含不允许的元素")
        for name, value in node.attrib.items():
            local = name.rsplit("}", 1)[-1]
            if local not in SVG_ATTRIBUTES:
                raise ValueError("SVG 包含不允许的属性")
            if name.startswith("{") and not name.startswith("{http://www.w3.org/1999/xlink}"):
                raise ValueError("SVG 属性命名空间不受支持")
            if local == "href" and not re.fullmatch(r"#[A-Za-z_][\w.-]*", value):
                raise ValueError("SVG 不允许外部引用")
            if "url" in value.lower() and not re.fullmatch(r"url\(#[A-Za-z_][\w.-]*\)", value):
                raise ValueError("SVG 不允许外部资源")
    ElementTree.register_namespace("", "http://www.w3.org/2000/svg")
    return ElementTree.tostring(root, encoding="unicode", short_empty_elements=False)


def resolve_static_file(url: str, require_signature: bool = False) -> Path:
    parsed = urlsplit(url)
    path = unquote(parsed.path)
    if parsed.scheme or parsed.netloc or parsed.fragment or not path.startswith("/static/"):
        raise HTTPException(400, "仅支持本地静态资源")
    if require_signature and path.startswith("/static/generated/"):
        from app.core.file_urls import verify
        if not verify(path, parsed.query):
            raise HTTPException(403, "作品文件链接无效或已过期，请重新打开作品")
    if "\\" in path or "\x00" in path:
        raise HTTPException(400, "资源路径无效")
    base = STATIC_DIR.resolve()
    candidate = (base / path[len("/static/"):]).resolve()
    if not candidate.is_relative_to(base) or not candidate.is_file():
        raise HTTPException(404, "资源不存在")
    return candidate
