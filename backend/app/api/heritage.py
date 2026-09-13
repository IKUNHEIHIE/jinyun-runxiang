import os
import uuid
import re
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user_optional, get_current_user
from app.schemas.common import success_response, error_response
from app.models.entities import Badge, UserBadge, SysConfig

router = APIRouter(prefix="/heritage", tags=["津门非遗环境音与金石印章多宝阁"])

STATIC_GENERATED_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static", "generated"
)
os.makedirs(STATIC_GENERATED_DIR, exist_ok=True)

class StampSealRequest(BaseModel):
    seal_code: str
    svg_url: Optional[str] = None
    svg_raw: Optional[str] = None

@router.get("/soundscapes")
def get_soundscapes(db: Session = Depends(get_db)):
    tracks = [
        {
            "id": "haihe_water",
            "title": "海河帆影·运河水韵",
            "category": "自然地脉",
            "description": "三岔河口大运河波光水流、微风拂柳与木舟摇橹清韵",
            "icon": "🌊",
            "ambient_freq": 174,
            "wave_type": "sine",
            "noise_type": "pink",
            "default_volume": 0.45,
            "culture_note": "天津因水而兴，九河下梢汇海河，运河漕运催生杨柳青与津门百艺。"
        },
        {
            "id": "dagu_drum",
            "title": "骆派京韵·檀板鼓韵",
            "category": "津派曲艺",
            "description": "国家级非遗骆玉笙先生京韵大鼓檀板开打、鼓套轻重缓急之律动",
            "icon": "🥁",
            "ambient_freq": 260,
            "wave_type": "triangle",
            "noise_type": "drum_beat",
            "default_volume": 0.5,
            "culture_note": "天津被誉为曲艺摇篮，京韵大鼓一板一眼尽显津门豪迈儒雅气质。"
        },
        {
            "id": "nianhua_carving",
            "title": "杨柳木版·刀刻沙竹",
            "category": "手工技艺",
            "description": "杜梨木版雕刻刀锋刮竹沙沙声、滚刷拓墨与生宣擦纸声",
            "icon": "🪵",
            "ambient_freq": 432,
            "wave_type": "sawtooth",
            "noise_type": "brown",
            "default_volume": 0.4,
            "culture_note": "杨柳青木版年画半印半画，每道刻线皆沉淀着数百道手工印记。"
        },
        {
            "id": "bell_morning",
            "title": "古刹晨钟·独乐梵音",
            "category": "金石建筑",
            "description": "蓟州独乐寺千年辽代斗拱檐下微风与古刹青铜晨钟回荡",
            "icon": "🔔",
            "ambient_freq": 528,
            "wave_type": "sine",
            "noise_type": "chime",
            "default_volume": 0.35,
            "culture_note": "独乐寺观音阁为全国现存最早木结构阁楼之一，金石与古建同辉。"
        }
    ]
    return success_response(tracks)

@router.get("/seals")
def get_heritage_seals(
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    user_id = current_user.get("user_id") if current_user else None
    unlocked_badge_ids = set()
    if user_id:
        unlocked = db.query(UserBadge).filter(UserBadge.user_id == user_id).all()
        unlocked_badge_ids = {u.badge_id for u in unlocked}

    seals = db.query(Badge).filter(Badge.code.like("SEAL_%")).all()
    res = []
    for s in seals:
        cond = s.condition_json if isinstance(s.condition_json, dict) else {}
        short_text = cond.get("short_text", s.name[:2])
        color = cond.get("color", "#C1272D")
        is_unlocked = (s.id in unlocked_badge_ids) or (user_id is None)

        res.append({
            "id": s.id,
            "code": s.code,
            "name": s.name,
            "description": s.description,
            "short_text": short_text,
            "color": color,
            "is_unlocked": is_unlocked,
            "seal_svg": f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="80" height="80">
  <rect x="5" y="5" width="90" height="90" rx="10" fill="{color}" stroke="#7A0010" stroke-width="4"/>
  <rect x="12" y="12" width="76" height="76" rx="6" fill="none" stroke="#FFE4D6" stroke-width="2" stroke-dasharray="6,2" opacity="0.85"/>
  <text x="50" y="58" fill="#FFF" font-size="30" font-weight="900" font-family="'STKaiti','KaiTi','SimSun',serif" text-anchor="middle" letter-spacing="2">{short_text}</text>
</svg>"""
        })

    return success_response(res)

@router.post("/seals/stamp")
def stamp_seal_on_svg(
    req: StampSealRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    seal = db.query(Badge).filter(Badge.code == req.seal_code).first()
    if not seal:
        return error_response(code=4041, message="未找到对应的非遗金石印章")

    cond = seal.condition_json if isinstance(seal.condition_json, dict) else {}
    short_text = cond.get("short_text", seal.name[:2])
    color = cond.get("color", "#C1272D")

    raw_svg = req.svg_raw
    if not raw_svg and req.svg_url:
        rel_path = req.svg_url.replace("/static/", "")
        static_base = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static")
        local_path = os.path.join(static_base, rel_path)
        if os.path.exists(local_path):
            with open(local_path, "r", encoding="utf-8", errors="ignore") as f:
                raw_svg = f.read()

    if not raw_svg:
        return error_response(code=4006, message="未提供有效的 SVG 内容或文件路径")

    seal_g = f"""
  <!-- 金石篆刻落款印章：{seal.name} -->
  <g id="heritage_seal_stamp" transform="translate(670, 860)">
    <filter id="seal_glow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="2" dy="3" stdDeviation="2" flood-color="#550000" flood-opacity="0.3"/>
    </filter>
    <rect x="0" y="0" width="105" height="105" rx="12" fill="{color}" stroke="#6F0F16" stroke-width="4" filter="url(#seal_glow)"/>
    <rect x="7" y="7" width="91" height="91" rx="8" fill="none" stroke="#FFDFD4" stroke-width="2.5" stroke-dasharray="8,3" opacity="0.9"/>
    <text x="52" y="62" fill="#FFFFFF" font-size="34" font-weight="900" font-family="'STKaiti','KaiTi','SimSun',serif" text-anchor="middle" letter-spacing="3">{short_text}</text>
    <text x="52" y="85" fill="#FFEFEA" font-size="11" font-family="sans-serif" text-anchor="middle" opacity="0.85">津韵润乡·藏</text>
  </g>
</svg>"""

    clean_svg = re.sub(r'<g id="heritage_seal_stamp".*?</g>', '', raw_svg, flags=re.DOTALL)
    if "</svg>" in clean_svg:
        stamped_svg = clean_svg.replace("</svg>", seal_g)
    else:
        stamped_svg = clean_svg + seal_g

    stamped_id = f"stamped_{uuid.uuid4().hex[:10]}.svg"
    dest_path = os.path.join(STATIC_GENERATED_DIR, stamped_id)
    with open(dest_path, "w", encoding="utf-8") as f:
        f.write(stamped_svg)

    stamped_url = f"/static/generated/{stamped_id}"

    return success_response({
        "seal_name": seal.name,
        "seal_code": seal.code,
        "short_text": short_text,
        "stamped_url": stamped_url
    }, message=f"已成功加盖【{seal.name}】朱砂金石印章")
