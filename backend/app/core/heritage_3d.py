"""Curated CC0 heritage models served by the AI workshop 3D lab.

The models are finished GLB assets from Poly Haven (CC0) and the Khronos
glTF Sample Assets repository. The demo returns one at random instead of
running a real reconstruction pipeline.
"""
from pathlib import Path
import random

MODEL_DIR = Path(__file__).resolve().parents[2] / "static" / "models" / "heritage3d"

CATALOG = [
    {
        "id": "panlong",
        "file": "panlong.glb",
        "name": "琉璃蟠龙",
        "subtitle": "琥珀琉璃 · 鎏金鳞脊",
        "category": "琉璃雕塑",
        "era": "清 · 宫廷陈设",
        "craft": "琉璃烧制",
        "material": "琥珀琉璃 / 鎏金铜脊",
        "description": "蟠龙昂首回望，龙身蜿蜒成环，通体呈琥珀琉璃质感。",
        "tags": ["蟠龙", "琉璃", "鎏金"],
        "palette": ["#B45309", "#F59E0B", "#451A03"],
        "triangles": 134995,
        "meshes": 2,
        "materials": 3,
        "license": "CC0 1.0",
        "source": "Khronos glTF Sample Assets · DragonAttenuation",
        "source_url": "https://github.com/KhronosGroup/glTF-Sample-Assets/tree/main/Models/DragonAttenuation",
    },
    {
        "id": "gongdeng",
        "file": "chandelier.glb",
        "name": "六方宫灯",
        "subtitle": "绢面花鸟 · 流苏垂金",
        "category": "灯彩扎制",
        "era": "清 · 津门灯会",
        "craft": "宫灯扎制",
        "material": "硬木 / 绢纱 / 铜饰",
        "description": "六方宫灯骨架起脊，绢面绘折枝花鸟，六角垂红流苏。",
        "tags": ["宫灯", "绢画", "流苏"],
        "palette": ["#7F1D1D", "#D4A373", "#F5EDE4"],
        "triangles": 7828,
        "meshes": 1,
        "materials": 1,
        "license": "CC0 1.0",
        "source": "Poly Haven · Chinese Chandelier",
        "source_url": "https://polyhaven.com/a/chinese_chandelier",
    },
    {
        "id": "screen",
        "file": "screen.glb",
        "name": "雀羽屏风",
        "subtitle": "髹漆描金 · 双扇透景",
        "category": "髹漆木作",
        "era": "明 · 文人居所",
        "craft": "髹漆描金",
        "material": "硬木 / 大漆 / 金箔",
        "description": "双扇屏风髹黑漆为底，金线描绘孔雀玉兰，边框起线利落。",
        "tags": ["屏风", "描金", "孔雀"],
        "palette": ["#1C1917", "#CA8A04", "#E7E5E4"],
        "triangles": 784,
        "meshes": 2,
        "materials": 1,
        "license": "CC0 1.0",
        "source": "Poly Haven · Chinese Screen Panels",
        "source_url": "https://polyhaven.com/a/chinese_screen_panels",
    },
    {
        "id": "vase",
        "file": "vase.glb",
        "name": "青花瓷韵",
        "subtitle": "釉下青花 · 缠枝莲纹",
        "category": "陶瓷烧制",
        "era": "明 · 景德镇窑",
        "craft": "青花瓷绘",
        "material": "高岭土 / 钴蓝釉下彩",
        "description": "梅瓶小口丰肩，釉面温润，青花缠枝莲纹随器身转折自然收放。",
        "tags": ["青花", "梅瓶", "缠枝莲"],
        "palette": ["#1E3A8A", "#F8FAFC", "#93C5FD"],
        "triangles": 9408,
        "meshes": 1,
        "materials": 1,
        "license": "CC0 1.0",
        "source": "Poly Haven · Antique Ceramic Vase 01",
        "source_url": "https://polyhaven.com/a/antique_ceramic_vase_01",
    },
    {
        "id": "teatable",
        "file": "teatable.glb",
        "name": "津门茶案",
        "subtitle": "束腰三弯腿 · 茶席陈设",
        "category": "硬木家具",
        "era": "清 · 津门茶事",
        "craft": "榫卯木作",
        "material": "深色硬木 / 天然生漆",
        "description": "茶案束腰起线，三弯腿承托，桌面纹理连续，适合作为茶席主案。",
        "tags": ["茶案", "榫卯", "茶席"],
        "palette": ["#44403C", "#A16207", "#D6D3D1"],
        "triangles": 2508,
        "meshes": 1,
        "materials": 1,
        "license": "CC0 1.0",
        "source": "Poly Haven · Chinese Tea Table",
        "source_url": "https://polyhaven.com/a/chinese_tea_table",
    },
    {
        "id": "quanyi",
        "file": "armchair.glb",
        "name": "津作圈椅",
        "subtitle": "天圆地方 · 素面木作",
        "category": "传统家具",
        "era": "明 · 津作工坊",
        "craft": "硬木榫卯",
        "material": "黄花梨色硬木",
        "description": "圈椅靠背一木连作，扶手顺势而下，素面呈现木纹与榫卯结构之美。",
        "tags": ["圈椅", "榫卯", "明式"],
        "palette": ["#3F2A1D", "#92613A", "#E7D3B3"],
        "triangles": 2675,
        "meshes": 1,
        "materials": 1,
        "license": "CC0 1.0",
        "source": "Poly Haven · Chinese Armchair",
        "source_url": "https://polyhaven.com/a/chinese_armchair",
    },
    {
        "id": "woodlantern",
        "file": "lantern.glb",
        "name": "木构灯彩",
        "subtitle": "卯榫骨架 · 暖光夜宴",
        "category": "民俗灯彩",
        "era": "民国 · 津郊庙会",
        "craft": "木作灯彩",
        "material": "老榆木 / 桐油纸",
        "description": "木构灯架以榫卯咬合，灯罩透出暖光，适合庙会与夜游场景复原。",
        "tags": ["灯彩", "榫卯", "庙会"],
        "palette": ["#78350F", "#FBBF24", "#FEF3C7"],
        "triangles": 8321,
        "meshes": 3,
        "materials": 2,
        "license": "CC0 1.0",
        "source": "Poly Haven · Wooden Lantern 01",
        "source_url": "https://polyhaven.com/a/wooden_lantern_01",
    },
]


def _public_entry(entry: dict) -> dict:
    path = MODEL_DIR / entry["file"]
    return {
        **entry,
        "url": f"/static/models/heritage3d/{entry['file']}",
        "size_bytes": path.stat().st_size,
        "size_mb": round(path.stat().st_size / 1048576, 2),
        "available": path.is_file(),
    }


def catalog() -> list[dict]:
    return [_public_entry(entry) for entry in CATALOG if (MODEL_DIR / entry["file"]).is_file()]


KEYWORDS = {
    "panlong": ("龙", "蟠龙", "琉璃", "鎏金"),
    "gongdeng": ("灯", "宫灯", "灯彩", "灯会", "绢"),
    "woodlantern": ("灯", "灯彩", "庙会", "木构"),
    "vase": ("瓷", "瓶", "青花", "梅瓶", "釉"),
    "screen": ("屏", "屏风", "孔雀", "描金", "漆"),
    "teatable": ("茶", "茶案", "茶席", "案"),
    "quanyi": ("椅", "圈椅", "木作", "榫卯"),
}


def pick(exclude_id: str | None = None, prompt: str = "") -> dict | None:
    entries = catalog()
    matched = [entry for entry in entries
               if any(word in prompt for word in KEYWORDS.get(entry["id"], ()))] if prompt else []
    pool = matched or entries
    fresh = [entry for entry in pool if entry["id"] != exclude_id]
    if not fresh:
        fresh = [entry for entry in entries if entry["id"] != exclude_id] or entries
    if not fresh:
        return None
    return random.SystemRandom().choice(fresh)
