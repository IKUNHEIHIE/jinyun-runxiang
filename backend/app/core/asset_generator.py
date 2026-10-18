"""
津韵润乡 · 天津非遗多模态生成算法与原生矢量资产合成引擎
负责依据大模型推理与用户提示词语义，动态生成真实的津门皮影、青铜器、大漆螺钿与A4激光雕刻纸样矢量资产
"""
import os
from html import escape
from app.core.files import sanitize_svg
import re

STATIC_GENERATED_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static", "generated")
os.makedirs(STATIC_GENERATED_DIR, exist_ok=True)

def extract_hex_colors(color_palette_list, default_colors=None):
    """从大模型返回的色板描述中精准提取 HEX 颜色代码"""
    found = []
    if color_palette_list and isinstance(color_palette_list, list):
        for item in color_palette_list:
            matches = re.findall(r'#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3}', str(item))
            found.extend(matches)
    if not found:
        return default_colors or ["#B63E2C", "#D6A85C", "#2F4F4F", "#1A1A1A", "#F8F4EC"]
    defaults = ["#B63E2C", "#D6A85C", "#2F4F4F", "#1A1A1A", "#F8F4EC", "#3B82F6"]
    for d in defaults:
        if len(found) < 5 and d not in found:
            found.append(d)
    return found

def detect_puppet_archetype(prompt: str = "", role_type: str = "") -> str:
    """根据提示词与角色定名智能判断皮影艺术原型"""
    if role_type.startswith("净"):
        return "PAINTED_JING"
    if role_type.startswith("丑"):
        return "COMIC_CHOU"
    text = f"{prompt} {role_type}".lower()
    if any(k in text for k in ["大圣", "悟空", "猴王", "美猴王", "金箍棒", "翎毛", "齐天大圣", "大闹天宫"]):
        return "MONKEY_KING"
    elif any(k in text for k in ["福娃", "年画", "锦鲤", "娃娃", "连年有余", "肚兜", "吉庆"]):
        return "FORTUNE_CHILD"
    elif any(k in text for k in ["穆桂英", "武生", "刀马旦", "靠旗", "帅盔", "银枪", "战将", "破阵", "红缨"]):
        return "WARRIOR_HERO"
    elif any(k in text for k in ["花旦", "青衣", "旦角", "仕女", "仙女", "贵妃", "团扇", "水袖", "杜丽娘"]):
        return "BEAUTY_DAN"
    else:
        return "SCHOLAR"

def _generate_shadow_puppet_base_svg(
    role_type: str = "生角·津门书生",
    colored: bool = True,
    prompt: str = "",
    colors: list = None
) -> str:
    """
    生成真实的津派皮影矢量艺术图。
    支持 MONKEY_KING (齐天大圣), FORTUNE_CHILD (杨柳青福娃), WARRIOR_HERO (穆桂英/武生),
    BEAUTY_DAN (津派花旦), SCHOLAR (赶考书生) 五大原型，支持大模型色彩注入与线稿/套色切换。
    """
    role_type = escape(role_type, quote=True)
    prompt = escape(prompt, quote=True)
    archetype = detect_puppet_archetype(prompt, role_type)
    hex_colors = extract_hex_colors(colors)
    
    # 配色配置
    if colored:
        c_stroke = "#2F2925"
        c_p1 = hex_colors[0] if len(hex_colors) > 0 else "#B63E2C"  # 主色
        c_gold = hex_colors[1] if len(hex_colors) > 1 else "#D6A85C" # 泥金
        c_p2 = hex_colors[2] if len(hex_colors) > 2 else "#2F4F4F"  # 副色
        c_dark = hex_colors[3] if len(hex_colors) > 3 else "#1A1A1A"# 深色
        c_skin = "#FBF4E8"  # 驴皮半透光米白
        c_accent = "#FF3333"
    else:
        c_stroke = "#111111"
        c_p1 = "none"
        c_gold = "none"
        c_p2 = "none"
        c_dark = "none"
        c_skin = "none"
        c_accent = "none"

    if archetype in {"PAINTED_JING", "COMIC_CHOU"}:
        return generate_mask_role_puppet(role_type, archetype, colored, hex_colors)
    if archetype == "MONKEY_KING":
        # 齐天大圣·美猴王皮影 (带双根超长活动翎毛、紧箍、凤翅紫金冠、锁子甲、虎皮裙、如意金箍棒)
        c_armor = c_gold if colored else "none"
        c_tiger = "#E67E22" if colored else "none"
        c_mask = "#B63E2C" if colored else "none"
        c_staff = "#C0392B" if colored else "none"
        c_ribbon = c_p1 if colored else "none"

        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 540 760" width="540" height="760">
  <defs>
    <radialGradient id="mkLeatherGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#FBF4E8" stop-opacity="0.95"/>
      <stop offset="100%" stop-color="#E5D6C1" stop-opacity="0.65"/>
    </radialGradient>
    <linearGradient id="featherGradL" x1="0%" y1="100%" x2="0%" y2="0%">
      <stop offset="0%" stop-color="{c_dark}"/>
      <stop offset="35%" stop-color="{c_gold}"/>
      <stop offset="70%" stop-color="{c_p1}"/>
      <stop offset="100%" stop-color="#27AE60"/>
    </linearGradient>
    <linearGradient id="featherGradR" x1="0%" y1="100%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{c_dark}"/>
      <stop offset="30%" stop-color="{c_gold}"/>
      <stop offset="75%" stop-color="{c_p1}"/>
      <stop offset="100%" stop-color="#27AE60"/>
    </linearGradient>
  </defs>

  <!-- 透光宣纸与皮影亮子背景 -->
  <rect width="100%" height="100%" fill="#F8F4EC" rx="16"/>
  <rect x="18" y="18" width="504" height="724" fill="none" stroke="{c_gold}" stroke-width="2" stroke-dasharray="6,4" rx="12"/>

  <!-- 顶部题字与非遗认证 -->
  <text x="270" y="48" font-size="19" font-family="'Noto Serif SC', serif" font-weight="bold" fill="{c_p1 if colored else '#222'}" text-anchor="middle">津门非遗皮影戏 · {role_type}</text>
  <text x="270" y="68" font-size="11" fill="#776D65" text-anchor="middle">齐天大圣三签活动翎毛可动皮影 · 镂空雕镞与矿物套色</text>

  <g transform="translate(270, 390)">
    <!-- 操纵三签与活动轴心标注 (领签、左右两手签) -->
    <line x1="0" y1="-140" x2="-160" y2="330" stroke="#8C827A" stroke-width="3" stroke-dasharray="4,2"/>
    <text x="-165" y="342" font-size="11" fill="#8C827A" font-family="monospace">领签(头枕)</text>
    <line x1="-120" y1="20" x2="-210" y2="330" stroke="#8C827A" stroke-width="3" stroke-dasharray="4,2"/>
    <text x="-215" y="342" font-size="11" fill="#8C827A" font-family="monospace">左手签</text>
    <line x1="120" y1="-30" x2="180" y2="330" stroke="#8C827A" stroke-width="3" stroke-dasharray="4,2"/>
    <text x="175" y="342" font-size="11" fill="#8C827A" font-family="monospace">右手擎棒签</text>

    <!-- 脚底腾云驾雾祥云 -->
    <path d="M-140,285 Q-100,260 -70,285 Q-30,260 0,285 Q40,260 80,285 Q120,260 150,285" fill="none" stroke="{c_gold}" stroke-width="3"/>
    <circle cx="-60" cy="275" r="10" fill="none" stroke="{c_gold}" stroke-width="2"/>
    <circle cx="70" cy="275" r="10" fill="none" stroke="{c_gold}" stroke-width="2"/>

    <!-- 腿部与登云战靴 -->
    <g>
      <!-- 左腿铠甲与战靴 -->
      <path d="M-55,160 Q-80,220 -60,270 L-25,270 Q-35,210 -15,160 Z" fill="{c_armor}" stroke="{c_stroke}" stroke-width="3"/>
      <path d="M-65,265 L-20,265 Q-15,282 -45,282 L-65,282 Z" fill="{c_dark}" stroke="{c_stroke}" stroke-width="2.5"/>
      <path d="M-55,272 L-30,272" stroke="{c_gold}" stroke-width="2"/>
      
      <!-- 右腿铠甲与战靴 (跨步动态) -->
      <path d="M15,160 Q35,210 25,270 L65,270 Q80,220 55,160 Z" fill="{c_armor}" stroke="{c_stroke}" stroke-width="3"/>
      <path d="M20,265 L70,265 Q75,282 45,282 L20,282 Z" fill="{c_dark}" stroke="{c_stroke}" stroke-width="2.5"/>
      <path d="M30,272 L55,272" stroke="{c_gold}" stroke-width="2"/>
    </g>

    <!-- 虎皮战裙 (带斑斓虎纹刻花) -->
    <g>
      <path d="M-65,85 L65,85 L75,165 Q0,185 -75,165 Z" fill="{c_tiger}" stroke="{c_stroke}" stroke-width="3.5"/>
      <!-- 镂空黑色虎皮斑纹 -->
      <polygon points="-55,95 -25,105 -55,115" fill="{c_dark}" stroke="{c_stroke}" stroke-width="1"/>
      <polygon points="55,95 25,105 55,115" fill="{c_dark}" stroke="{c_stroke}" stroke-width="1"/>
      <polygon points="-60,135 -20,145 -55,155" fill="{c_dark}" stroke="{c_stroke}" stroke-width="1"/>
      <polygon points="60,135 20,145 55,155" fill="{c_dark}" stroke="{c_stroke}" stroke-width="1"/>
      <polygon points="-15,115 0,140 15,115" fill="{c_dark}" stroke="{c_stroke}" stroke-width="1"/>
      <!-- 战袍下摆红绸飞扬 -->
      <path d="M-75,120 Q-120,160 -100,195 Q-85,165 -65,150 Z" fill="{c_ribbon}" stroke="{c_stroke}" stroke-width="2.5"/>
      <path d="M75,120 Q120,160 100,195 Q85,165 65,150 Z" fill="{c_ribbon}" stroke="{c_stroke}" stroke-width="2.5"/>
    </g>

    <!-- 躯干：锁子黄金甲与护心镜 -->
    <g>
      <path d="M-55,-60 L55,-60 L68,85 L-68,85 Z" fill="{c_armor}" stroke="{c_stroke}" stroke-width="3.5"/>
      <path d="M-40,-35 Q-20,-20 0,-35 Q20,-20 40,-35" fill="none" stroke="{c_stroke}" stroke-width="2"/>
      <path d="M-45,-10 Q-20,5 0,-10 Q20,5 45,-10" fill="none" stroke="{c_stroke}" stroke-width="2"/>
      <path d="M-40,15 Q-20,30 0,15 Q20,30 40,15" fill="none" stroke="{c_stroke}" stroke-width="2"/>
      <path d="M-45,40 Q-20,55 0,40 Q20,55 45,40" fill="none" stroke="{c_stroke}" stroke-width="2"/>
      <circle cx="0" cy="15" r="22" fill="{c_p1}" stroke="{c_gold}" stroke-width="3"/>
      <circle cx="0" cy="15" r="14" fill="{c_gold}" stroke="{c_stroke}" stroke-width="2"/>
      <circle cx="0" cy="15" r="5" fill="#FFF"/>
      <rect x="-55" y="68" width="110" height="18" fill="{c_gold}" stroke="{c_stroke}" stroke-width="2"/>
      <circle cx="0" cy="77" r="6" fill="{c_p1}" stroke="{c_stroke}" stroke-width="1.5"/>
    </g>

    <!-- 如意金箍棒 (横贯战局，两头金箍，中间朱红) -->
    <g>
      <line x1="-165" y1="130" x2="165" y2="-90" stroke="{c_staff}" stroke-width="10" stroke-linecap="round"/>
      <line x1="-165" y1="130" x2="165" y2="-90" stroke="#FFF" stroke-width="2" stroke-dasharray="8,6" opacity="0.7"/>
      <!-- 金箍端头 1 (右上) -->
      <line x1="125" y1="-63" x2="165" y2="-90" stroke="{c_gold}" stroke-width="12" stroke-linecap="round"/>
      <circle cx="165" cy="-90" r="7" fill="{c_gold}" stroke="{c_stroke}" stroke-width="2"/>
      <text x="110" y="-85" font-size="9" fill="{c_p1}" font-weight="bold" font-family="serif">如意金箍棒</text>
      <!-- 金箍端头 2 (左下) -->
      <line x1="-125" y1="103" x2="-165" y2="130" stroke="{c_gold}" stroke-width="12" stroke-linecap="round"/>
      <circle cx="-165" cy="130" r="7" fill="{c_gold}" stroke="{c_stroke}" stroke-width="2"/>
    </g>

    <!-- 左臂与护肩 -->
    <g>
      <path d="M-55,-60 C-85,-75 -95,-45 -80,-30 Z" fill="{c_p1}" stroke="{c_stroke}" stroke-width="3"/>
      <path d="M-50,-50 L-95,-15 L-80,0 L-45,-35 Z" fill="{c_armor}" stroke="{c_stroke}" stroke-width="3"/>
      <circle cx="-88" cy="-8" r="5" fill="{c_gold}" stroke="{c_stroke}" stroke-width="2"/>
      <path d="M-88,-8 L-125,25 L-110,35 L-78,5 Z" fill="{c_armor}" stroke="{c_stroke}" stroke-width="3"/>
      <circle cx="-120" cy="28" r="8" fill="{c_skin}" stroke="{c_stroke}" stroke-width="2"/>
      <circle cx="-120" cy="28" r="3" fill="{c_gold}"/>
    </g>

    <!-- 右臂举棒与护肩 -->
    <g>
      <path d="M55,-60 C85,-75 95,-45 80,-30 Z" fill="{c_p1}" stroke="{c_stroke}" stroke-width="3"/>
      <path d="M50,-50 L95,-60 L105,-45 L55,-35 Z" fill="{c_armor}" stroke="{c_stroke}" stroke-width="3"/>
      <circle cx="100" cy="-52" r="5" fill="{c_gold}" stroke="{c_stroke}" stroke-width="2"/>
      <path d="M100,-52 L125,-25 L115,-15 L90,-40 Z" fill="{c_armor}" stroke="{c_stroke}" stroke-width="3"/>
      <circle cx="120" cy="-20" r="8" fill="{c_skin}" stroke="{c_stroke}" stroke-width="2"/>
      <circle cx="120" cy="-20" r="3" fill="{c_gold}"/>
    </g>

    <!-- 头部：凤翅紫金冠 + 双根活动翎毛 + 紧箍 + 火眼金睛猴脸 -->
    <g transform="translate(0, -60)">
      <circle cx="0" cy="0" r="6" fill="{c_gold}" stroke="{c_stroke}" stroke-width="2"/>

      <!-- ★★★ 双根超长高耸活动翎毛 (雉尾) ★★★ -->
      <path d="M-8,-55 C-35,-130 -115,-205 -175,-165 C-130,-145 -65,-95 -2,-55 Z" fill="url(#featherGradL)" stroke="{c_stroke}" stroke-width="2.5"/>
      <path d="M-45,-120 L-60,-135 M-78,-145 L-100,-165 M-115,-160 L-138,-182 M-145,-162 L-170,-175" stroke="{c_gold}" stroke-width="2.5"/>
      <circle cx="-175" cy="-165" r="7" fill="{c_p1}" stroke="{c_stroke}" stroke-width="1.5"/>
      <circle cx="-175" cy="-165" r="3" fill="{c_gold}"/>

      <path d="M8,-55 C35,-140 120,-215 185,-175 C140,-155 70,-100 2,-55 Z" fill="url(#featherGradR)" stroke="{c_stroke}" stroke-width="2.5"/>
      <path d="M45,-125 L60,-140 M80,-152 L105,-172 M120,-168 L145,-190 M150,-172 L180,-185" stroke="{c_gold}" stroke-width="2.5"/>
      <circle cx="185" cy="-175" r="7" fill="{c_p1}" stroke="{c_stroke}" stroke-width="1.5"/>
      <circle cx="185" cy="-175" r="3" fill="{c_gold}"/>

      <!-- 凤翅紫金冠冠体 -->
      <path d="M-26,-48 L-35,-85 L-15,-65 L0,-90 L15,-65 L35,-85 L26,-48 Z" fill="{c_gold}" stroke="{c_stroke}" stroke-width="2.5"/>
      <circle cx="0" cy="-70" r="5" fill="{c_p1}" stroke="{c_stroke}" stroke-width="1.5"/>
      <path d="M-30,-60 Q-60,-80 -45,-100 Q-30,-80 -25,-65 Z" fill="{c_p1}" stroke="{c_stroke}" stroke-width="2"/>
      <path d="M30,-60 Q60,-80 45,-100 Q30,-80 25,-65 Z" fill="{c_p1}" stroke="{c_stroke}" stroke-width="2"/>

      <!-- 金箍圈 -->
      <path d="M-22,-44 Q0,-52 22,-44 Q0,-38 -22,-44 Z" fill="{c_gold}" stroke="{c_stroke}" stroke-width="2"/>
      <circle cx="0" cy="-46" r="4.5" fill="{c_gold}" stroke="{c_stroke}" stroke-width="1.5"/>
      <circle cx="0" cy="-46" r="2" fill="{c_p1}"/>

      <!-- 美猴王桃形侧脸脸谱 -->
      <path d="M-15,-40 C-25,-25 -10,-10 5,-15 C18,-18 25,-30 20,-42 Z" fill="{c_mask}" stroke="{c_stroke}" stroke-width="2.5"/>
      <ellipse cx="6" cy="-28" rx="8" ry="6" fill="{c_skin}" stroke="{c_stroke}" stroke-width="1.5"/>
      <!-- 火眼金睛 -->
      <ellipse cx="8" cy="-30" rx="4.5" ry="3" fill="#FFD700" stroke="{c_stroke}" stroke-width="1.5"/>
      <circle cx="9" cy="-30" r="1.8" fill="#000"/>
      <path d="M12,-20 Q22,-20 20,-14 Q12,-12 8,-16" fill="{c_gold}" stroke="{c_stroke}" stroke-width="2"/>
      <circle cx="16" cy="-17" r="1.5" fill="{c_stroke}"/>
      <path d="M-20,-35 Q-35,-20 -28,10 Q-20,-10 -15,-25 Z" fill="{c_gold}" stroke="{c_stroke}" stroke-width="2"/>
    </g>
  </g>

  <!-- 底部红印章 -->
  <rect x="440" y="675" width="48" height="48" fill="{c_p1 if colored else '#888'}" rx="6"/>
  <text x="464" y="698" font-size="14" fill="#FFF" font-weight="bold" font-family="serif" text-anchor="middle">齐天</text>
  <text x="464" y="714" font-size="14" fill="#FFF" font-weight="bold" font-family="serif" text-anchor="middle">大圣</text>
</svg>"""

    elif archetype == "FORTUNE_CHILD":
        # 吉庆福娃·杨柳青大红锦鲤 (双抓髻、红肚兜、长命锁、怀抱杨柳青红锦鲤与荷花荷叶)
        c_carp = c_p1 if colored else "none"
        c_lotus_leaf = "#27AE60" if colored else "none"
        c_lotus_pink = "#FF6B81" if colored else "none"
        c_dudou = c_p1 if colored else "none"

        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 540 760" width="540" height="760">
  <defs>
    <radialGradient id="fcLeatherGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#FDF8F0" stop-opacity="0.95"/>
      <stop offset="100%" stop-color="#EADBCC" stop-opacity="0.65"/>
    </radialGradient>
    <linearGradient id="carpGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FF5722"/>
      <stop offset="50%" stop-color="#E74C3C"/>
      <stop offset="100%" stop-color="#C0392B"/>
    </linearGradient>
  </defs>

  <rect width="100%" height="100%" fill="#F8F4EC" rx="16"/>
  <rect x="18" y="18" width="504" height="724" fill="none" stroke="{c_gold}" stroke-width="2" stroke-dasharray="6,4" rx="12"/>

  <text x="270" y="48" font-size="19" font-family="'Noto Serif SC', serif" font-weight="bold" fill="{c_p1 if colored else '#222'}" text-anchor="middle">津门非遗皮影戏 · {role_type}</text>
  <text x="270" y="68" font-size="11" fill="#776D65" text-anchor="middle">杨柳青吉庆福娃怀抱大红锦鲤 · 连年有余吉庆皮影</text>

  <g transform="translate(270, 390)">
    <line x1="0" y1="-130" x2="-150" y2="330" stroke="#8C827A" stroke-width="3" stroke-dasharray="4,2"/>
    <text x="-155" y="342" font-size="11" fill="#8C827A" font-family="monospace">领签(头枕)</text>
    <line x1="-120" y1="40" x2="-210" y2="330" stroke="#8C827A" stroke-width="3" stroke-dasharray="4,2"/>
    <text x="-215" y="342" font-size="11" fill="#8C827A" font-family="monospace">锦鲤操纵签</text>
    <line x1="110" y1="-30" x2="170" y2="330" stroke="#8C827A" stroke-width="3" stroke-dasharray="4,2"/>
    <text x="165" y="342" font-size="11" fill="#8C827A" font-family="monospace">荷叶莲花签</text>

    <path d="M-150,280 Q-100,240 -50,280 Q0,240 50,280 Q100,240 150,280" fill="none" stroke="#3498DB" stroke-width="2.5"/>
    <path d="M-130,295 Q-80,265 -30,295 Q20,265 70,295 Q120,265 160,295" fill="none" stroke="{c_gold}" stroke-width="2"/>

    <!-- 胖娃娃短腿与红绳金铃铛 -->
    <g>
      <path d="M-45,150 Q-65,220 -40,260 L-10,260 Q-20,200 -5,150 Z" fill="{c_skin}" stroke="{c_stroke}" stroke-width="3"/>
      <circle cx="-25" cy="255" r="6" fill="{c_gold}" stroke="{c_stroke}" stroke-width="1.5"/>
      <path d="M5,150 Q20,200 10,260 L40,260 Q65,220 45,150 Z" fill="{c_skin}" stroke="{c_stroke}" stroke-width="3"/>
      <circle cx="25" cy="255" r="6" fill="{c_gold}" stroke="{c_stroke}" stroke-width="1.5"/>
    </g>

    <!-- 莲花与荷叶配件 -->
    <g transform="translate(90, -40)">
      <circle cx="0" cy="0" r="42" fill="{c_lotus_leaf}" stroke="{c_stroke}" stroke-width="2.5"/>
      <path d="M0,0 L-30,-25 M0,0 L30,-25 M0,0 L-35,15 M0,0 L35,15 M0,0 L0,38" stroke="{c_gold}" stroke-width="1.5"/>
      <path d="M-15,-20 C-30,-60 -5,-75 0,-85 C5,-75 30,-60 15,-20 Z" fill="{c_lotus_pink}" stroke="{c_stroke}" stroke-width="2"/>
      <path d="M-5,-20 C-15,-50 0,-65 0,-70 C0,-65 15,-50 5,-20 Z" fill="#FFF" stroke="{c_stroke}" stroke-width="1.5"/>
      <circle cx="0" cy="-35" r="4" fill="{c_gold}"/>
      <line x1="0" y1="0" x2="30" y2="160" stroke="{c_lotus_leaf}" stroke-width="4"/>
    </g>

    <!-- 躯干：圆润红肚兜与长命百岁金锁 -->
    <g>
      <polygon points="0,-40 45,-15 50,140 -50,140 -45,-15" fill="{c_dudou}" stroke="{c_stroke}" stroke-width="3.5"/>
      <path d="M-25,-55 Q0,-45 25,-55" fill="none" stroke="{c_p1}" stroke-width="3"/>
      <circle cx="0" cy="50" r="28" fill="none" stroke="{c_gold}" stroke-width="3"/>
      <circle cx="0" cy="50" r="18" fill="none" stroke="{c_gold}" stroke-width="1.5" stroke-dasharray="4,2"/>
      <text x="0" y="56" font-size="18" fill="{c_gold}" font-family="serif" font-weight="bold" text-anchor="middle">吉</text>
      <!-- 金锁 -->
      <path d="M-22,-25 Q0,-32 22,-25 Q15,-10 0,-12 Q-15,-10 -22,-25 Z" fill="{c_gold}" stroke="{c_stroke}" stroke-width="2"/>
      <circle cx="-12" cy="-10" r="2.5" fill="{c_gold}"/>
      <circle cx="0" cy="-8" r="2.5" fill="{c_gold}"/>
      <circle cx="12" cy="-10" r="2.5" fill="{c_gold}"/>
    </g>

    <!-- ★★★ 核心资产：天津杨柳青招牌大红锦鲤 ★★★ -->
    <g transform="translate(-15, 45) rotate(-15)">
      <path d="M-105,10 C-80,-40 40,-50 110,0 C125,25 90,65 20,65 C-50,65 -95,45 -105,10 Z" fill="url(#carpGrad)" stroke="{c_stroke}" stroke-width="3.5"/>
      <path d="M105,5 Q155,-25 175,-5 Q145,25 165,55 Q135,35 100,20 Z" fill="{c_carp}" stroke="{c_stroke}" stroke-width="2.5"/>
      <path d="M-30,-35 Q-15,-65 15,-40 Z" fill="{c_gold}" stroke="{c_stroke}" stroke-width="2"/>
      <path d="M-40,45 Q-20,75 10,50 Z" fill="{c_gold}" stroke="{c_stroke}" stroke-width="2"/>
      <path d="M-40,-10 Q-25,5 -10,-10 Q5,5 20,-10 Q35,5 50,-10" fill="none" stroke="{c_gold}" stroke-width="2"/>
      <path d="M-30,15 Q-15,30 0,15 Q15,30 30,15 Q45,30 60,15" fill="none" stroke="{c_gold}" stroke-width="2"/>
      <circle cx="-85" cy="5" r="7" fill="#FFF" stroke="{c_stroke}" stroke-width="2"/>
      <circle cx="-87" cy="5" r="3.5" fill="#000"/>
      <path d="M-98,12 Q-125,20 -115,35" fill="none" stroke="{c_gold}" stroke-width="2.5"/>
    </g>

    <!-- 福娃双臂紧抱大红鲤鱼 -->
    <g>
      <path d="M-40,-30 Q-95,0 -70,55 Q-50,45 -35,0 Z" fill="{c_skin}" stroke="{c_stroke}" stroke-width="3"/>
      <circle cx="-65" cy="55" r="10" fill="{c_skin}" stroke="{c_stroke}" stroke-width="2"/>
      <circle cx="-65" cy="45" r="4" fill="{c_gold}"/>
      <path d="M40,-30 Q85,15 50,65 Q35,50 30,0 Z" fill="{c_skin}" stroke="{c_stroke}" stroke-width="3"/>
      <circle cx="45" cy="65" r="10" fill="{c_skin}" stroke="{c_stroke}" stroke-width="2"/>
      <circle cx="45" cy="55" r="4" fill="{c_gold}"/>
    </g>

    <!-- 福娃头部：双抓髻、红头绳、圆润胖脸 -->
    <g transform="translate(0, -60)">
      <circle cx="0" cy="0" r="6" fill="{c_gold}" stroke="{c_stroke}" stroke-width="2"/>
      <circle cx="-32" cy="-60" r="16" fill="{c_dark}" stroke="{c_stroke}" stroke-width="3"/>
      <path d="M-40,-50 Q-55,-40 -45,-25" fill="none" stroke="{c_p1}" stroke-width="3"/>
      <circle cx="32" cy="-60" r="16" fill="{c_dark}" stroke="{c_stroke}" stroke-width="3"/>
      <path d="M40,-50 Q55,-40 45,-25" fill="none" stroke="{c_p1}" stroke-width="3"/>
      <ellipse cx="0" cy="-35" rx="28" ry="24" fill="{c_skin}" stroke="{c_stroke}" stroke-width="3"/>
      <circle cx="0" cy="-45" r="3.5" fill="{c_accent}"/>
      <path d="M8,-36 Q16,-40 20,-34" fill="none" stroke="{c_stroke}" stroke-width="2.5"/>
      <path d="M12,-24 Q18,-18 20,-24" fill="{c_p1}" stroke="{c_stroke}" stroke-width="1.5"/>
      <ellipse cx="14" cy="-28" rx="6" ry="4" fill="{c_accent}" opacity="0.4"/>
    </g>
  </g>

  <rect x="440" y="675" width="48" height="48" fill="{c_p1 if colored else '#888'}" rx="6"/>
  <text x="464" y="698" font-size="14" fill="#FFF" font-weight="bold" font-family="serif" text-anchor="middle">吉庆</text>
  <text x="464" y="714" font-size="14" fill="#FFF" font-weight="bold" font-family="serif" text-anchor="middle">福娃</text>
</svg>"""

    elif archetype == "WARRIOR_HERO":
        # 穆桂英/武生·四方靠旗大破天门阵
        c_armor = c_gold if colored else "none"
        c_flag = c_p1 if colored else "none"
        c_spear = "#E0E0E0" if colored else "none"

        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 540 760" width="540" height="760">
  <rect width="100%" height="100%" fill="#F8F4EC" rx="16"/>
  <rect x="18" y="18" width="504" height="724" fill="none" stroke="{c_gold}" stroke-width="2" stroke-dasharray="6,4" rx="12"/>

  <text x="270" y="48" font-size="19" font-family="'Noto Serif SC', serif" font-weight="bold" fill="{c_p1 if colored else '#222'}" text-anchor="middle">津门非遗皮影戏 · {role_type}</text>
  <text x="270" y="68" font-size="11" fill="#776D65" text-anchor="middle">帅盔靠旗红缨银枪巾帼武生 · 传统三签联动皮影</text>

  <g transform="translate(270, 390)">
    <line x1="0" y1="-140" x2="-150" y2="330" stroke="#8C827A" stroke-width="3" stroke-dasharray="4,2"/>
    <text x="-155" y="342" font-size="11" fill="#8C827A" font-family="monospace">领签(头枕)</text>
    <line x1="-120" y1="20" x2="-210" y2="330" stroke="#8C827A" stroke-width="3" stroke-dasharray="4,2"/>
    <text x="-215" y="342" font-size="11" fill="#8C827A" font-family="monospace">左手枪身签</text>
    <line x1="120" y1="-20" x2="180" y2="330" stroke="#8C827A" stroke-width="3" stroke-dasharray="4,2"/>
    <text x="175" y="342" font-size="11" fill="#8C827A" font-family="monospace">右手枪尾签</text>

    <!-- 四方靠旗 -->
    <path d="M-20,-40 L-130,-150 L-100,-175 L-10,-60 Z" fill="{c_flag}" stroke="{c_stroke}" stroke-width="2.5"/>
    <line x1="-20" y1="-40" x2="-140" y2="-160" stroke="{c_gold}" stroke-width="3"/>
    <path d="M20,-40 L130,-150 L100,-175 L10,-60 Z" fill="{c_flag}" stroke="{c_stroke}" stroke-width="2.5"/>
    <line x1="20" y1="-40" x2="140" y2="-160" stroke="{c_gold}" stroke-width="3"/>
    <path d="M-25,-10 L-150,-50 L-140,-85 L-15,-25 Z" fill="{c_flag}" stroke="{c_stroke}" stroke-width="2.5"/>
    <path d="M25,-10 L150,-50 L140,-85 L15,-25 Z" fill="{c_flag}" stroke="{c_stroke}" stroke-width="2.5"/>

    <!-- 腿部与战靴 -->
    <path d="M-50,150 Q-70,210 -55,265 L-20,265 Q-30,200 -10,150 Z" fill="{c_armor}" stroke="{c_stroke}" stroke-width="3"/>
    <path d="M-65,260 L-15,260 Q-10,280 -45,280 L-65,280 Z" fill="{c_dark}" stroke="{c_stroke}" stroke-width="2.5"/>
    <path d="M10,150 Q30,200 20,265 L55,265 Q70,210 50,150 Z" fill="{c_armor}" stroke="{c_stroke}" stroke-width="3"/>
    <path d="M15,260 L65,260 Q70,280 35,280 L15,280 Z" fill="{c_dark}" stroke="{c_stroke}" stroke-width="2.5"/>

    <!-- 战裙与连环铠甲 -->
    <path d="M-60,75 L60,75 L70,155 Q0,175 -70,155 Z" fill="{c_flag}" stroke="{c_stroke}" stroke-width="3"/>
    <path d="M-55,-50 L55,-50 L65,75 L-65,75 Z" fill="{c_armor}" stroke="{c_stroke}" stroke-width="3.5"/>
    <circle cx="0" cy="10" r="18" fill="#FFF" stroke="{c_gold}" stroke-width="3"/>

    <!-- 红缨银枪 -->
    <line x1="-160" y1="-80" x2="150" y2="180" stroke="#B0BEC5" stroke-width="7" stroke-linecap="round"/>
    <polygon points="-160,-80 -185,-105 -170,-115 -145,-90" fill="{c_spear}" stroke="{c_stroke}" stroke-width="2"/>
    <path d="M-150,-70 Q-165,-50 -140,-40 Q-130,-55 -140,-75 Z" fill="{c_p1}" stroke="{c_stroke}" stroke-width="2"/>

    <circle cx="-105" cy="-25" r="7" fill="{c_skin}" stroke="{c_stroke}" stroke-width="2"/>
    <circle cx="85" cy="115" r="7" fill="{c_skin}" stroke="{c_stroke}" stroke-width="2"/>

    <!-- 帅盔红缨 -->
    <g transform="translate(0, -50)">
      <circle cx="0" cy="0" r="6" fill="{c_gold}" stroke="{c_stroke}" stroke-width="2"/>
      <path d="M-25,-25 L-20,-70 L0,-85 L20,-70 L25,-25 Z" fill="{c_gold}" stroke="{c_stroke}" stroke-width="2.5"/>
      <path d="M0,-85 Q-20,-125 -40,-135 Q-15,-110 0,-90 Z" fill="{c_p1}" stroke="{c_stroke}" stroke-width="2"/>
      <ellipse cx="6" cy="-40" rx="15" ry="14" fill="{c_skin}" stroke="{c_stroke}" stroke-width="2.5"/>
      <path d="M10,-42 Q18,-45 20,-39" stroke="{c_stroke}" stroke-width="2" fill="none"/>
      <path d="M12,-30 Q18,-30 16,-26" stroke="{c_p1}" stroke-width="2" fill="none"/>
    </g>
  </g>

  <rect x="440" y="675" width="48" height="48" fill="{c_p1 if colored else '#888'}" rx="6"/>
  <text x="464" y="698" font-size="14" fill="#FFF" font-weight="bold" font-family="serif" text-anchor="middle">破阵</text>
  <text x="464" y="714" font-size="14" fill="#FFF" font-weight="bold" font-family="serif" text-anchor="middle">武生</text>
</svg>"""

    elif archetype == "BEAUTY_DAN":
        # 津派花旦/青衣·仕女
        c_dress = c_p1 if colored else "none"
        c_fan = c_gold if colored else "none"
        c_cyan = "#16A085" if colored else "none"

        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 540 760" width="540" height="760">
  <rect width="100%" height="100%" fill="#F8F4EC" rx="16"/>
  <rect x="18" y="18" width="504" height="724" fill="none" stroke="{c_gold}" stroke-width="2" stroke-dasharray="6,4" rx="12"/>

  <text x="270" y="48" font-size="19" font-family="'Noto Serif SC', serif" font-weight="bold" fill="{c_p1 if colored else '#222'}" text-anchor="middle">津门非遗皮影戏 · {role_type}</text>
  <text x="270" y="68" font-size="11" fill="#776D65" text-anchor="middle">点翠头面百褶水袖团扇青衣 · 传统津派旦角皮影</text>

  <g transform="translate(270, 390)">
    <line x1="0" y1="-140" x2="-150" y2="330" stroke="#8C827A" stroke-width="3" stroke-dasharray="4,2"/>
    <line x1="-120" y1="20" x2="-210" y2="330" stroke="#8C827A" stroke-width="3" stroke-dasharray="4,2"/>
    <line x1="120" y1="20" x2="180" y2="330" stroke="#8C827A" stroke-width="3" stroke-dasharray="4,2"/>

    <path d="M-45,60 Q-95,190 -75,265 L75,265 Q95,190 45,60 Z" fill="{c_dress}" stroke="{c_stroke}" stroke-width="3"/>
    <path d="M-40,265 L-40,110 M-15,265 L-15,90 M15,265 L15,90 M40,265 L40,110" stroke="{c_gold}" stroke-width="2" stroke-dasharray="4,3"/>

    <path d="M-45,-45 L45,-45 L50,65 L-50,65 Z" fill="{c_skin}" stroke="{c_stroke}" stroke-width="3"/>
    <path d="M-55,-45 C-30,-20 30,-20 55,-45 C30,10 -30,10 -55,-45 Z" fill="{c_cyan}" stroke="{c_stroke}" stroke-width="2.5"/>

    <g transform="translate(90, 0)">
      <circle cx="20" cy="-20" r="32" fill="{c_skin}" stroke="{c_gold}" stroke-width="2.5"/>
      <line x1="20" y1="12" x2="20" y2="55" stroke="{c_dark}" stroke-width="3"/>
      <circle cx="20" cy="-20" r="10" fill="{c_p1}" stroke="{c_stroke}" stroke-width="1.5"/>
    </g>

    <g transform="translate(0, -50)">
      <circle cx="0" cy="0" r="6" fill="{c_gold}" stroke="{c_stroke}" stroke-width="2"/>
      <path d="M-25,-20 Q-50,-35 -40,-75 Q0,-85 25,-65 L18,-20 Z" fill="{c_cyan}" stroke="{c_stroke}" stroke-width="3"/>
      <line x1="-25" y1="-30" x2="-35" y2="10" stroke="{c_gold}" stroke-width="2" stroke-dasharray="3,3"/>
      <ellipse cx="8" cy="-35" rx="14" ry="16" fill="{c_skin}" stroke="{c_stroke}" stroke-width="2.5"/>
      <path d="M12,-38 Q18,-42 20,-36" stroke="{c_stroke}" stroke-width="2" fill="none"/>
      <path d="M14,-26 Q18,-26 16,-22" stroke="{c_p1}" stroke-width="2" fill="none"/>
    </g>
  </g>

  <rect x="440" y="675" width="48" height="48" fill="{c_p1 if colored else '#888'}" rx="6"/>
  <text x="464" y="698" font-size="14" fill="#FFF" font-weight="bold" font-family="serif" text-anchor="middle">津派</text>
  <text x="464" y="714" font-size="14" fill="#FFF" font-weight="bold" font-family="serif" text-anchor="middle">青衣</text>
</svg>"""

    else:
        # 生角·津门赶考书生
        c_robe = c_p1 if colored else "none"
        c_belt = c_gold if colored else "none"
        c_cyan = c_p2 if colored else "none"

        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 540 760" width="540" height="760">
  <rect width="100%" height="100%" fill="#F8F4EC" rx="16"/>
  <rect x="18" y="18" width="504" height="724" fill="none" stroke="{c_gold}" stroke-width="2" stroke-dasharray="6,4" rx="12"/>

  <text x="270" y="48" font-size="19" font-family="'Noto Serif SC', serif" font-weight="bold" fill="{c_p1 if colored else '#222'}" text-anchor="middle">津门非遗皮影戏 · {role_type}</text>
  <text x="270" y="68" font-size="11" fill="#776D65" text-anchor="middle">身穿绣金文生巾赶考书生 · 传统三签联动皮影</text>

  <g transform="translate(270, 390)">
    <line x1="0" y1="-140" x2="-150" y2="330" stroke="#8C827A" stroke-width="3" stroke-dasharray="4,2"/>
    <line x1="-120" y1="20" x2="-210" y2="330" stroke="#8C827A" stroke-width="3" stroke-dasharray="4,2"/>
    <line x1="120" y1="20" x2="180" y2="330" stroke="#8C827A" stroke-width="3" stroke-dasharray="4,2"/>

    <path d="M-60,80 Q-90,190 -70,250 L-30,250 Q-40,160 -10,80 Z" fill="{c_cyan}" stroke="{c_stroke}" stroke-width="3"/>
    <path d="M10,80 Q40,160 30,250 L70,250 Q90,190 60,80 Z" fill="{c_cyan}" stroke="{c_stroke}" stroke-width="3"/>
    <path d="M-80,245 L-20,245 Q-15,265 -50,265 L-80,265 Z" fill="{c_dark}" stroke="{c_stroke}" stroke-width="2"/>
    <path d="M20,245 L80,245 Q85,265 50,265 L20,265 Z" fill="{c_dark}" stroke="{c_stroke}" stroke-width="2"/>

    <path d="M-55,-60 L55,-60 L70,90 L-70,90 Z" fill="{c_robe}" stroke="{c_stroke}" stroke-width="3"/>
    <rect x="-58" y="0" width="116" height="18" fill="{c_belt}" stroke="{c_stroke}" stroke-width="2"/>
    <circle cx="0" cy="45" r="22" fill="none" stroke="{c_belt}" stroke-width="3"/>

    <g transform="translate(90, 10)">
      <path d="M25,15 L65,-5 Q80,20 45,35 Z" fill="{c_belt}" stroke="{c_stroke}" stroke-width="2"/>
    </g>

    <g transform="translate(0, -60)">
      <circle cx="0" cy="0" r="6" fill="{c_gold}" stroke="{c_stroke}" stroke-width="2"/>
      <path d="M-30,-20 Q-60,-40 -50,-80 Q0,-95 30,-70 L20,-20 Z" fill="{c_dark}" stroke="{c_stroke}" stroke-width="3"/>
      <path d="M-40,-30 Q-90,-20 -80,40 L-65,35 Q-75,-10 -35,-20 Z" fill="{c_dark}" stroke="{c_stroke}" stroke-width="2"/>
      <circle cx="10" cy="-75" r="8" fill="{c_belt}" stroke="{c_stroke}" stroke-width="2"/>
      <path d="M-10,-20 L10,-20 Q12,-35 25,-40 L28,-48 Q20,-50 18,-55 Q28,-60 25,-70 L5,-70" fill="{c_skin}" stroke="{c_stroke}" stroke-width="3"/>
      <path d="M12,-52 Q18,-54 22,-50" fill="none" stroke="{c_p1}" stroke-width="2.5"/>
      <circle cx="17" cy="-51" r="1.5" fill="#111"/>
    </g>
  </g>

  <rect x="440" y="675" width="48" height="48" fill="{c_p1 if colored else '#888'}" rx="6"/>
  <text x="464" y="698" font-size="14" fill="#FFF" font-weight="bold" font-family="serif" text-anchor="middle">津韵</text>
  <text x="464" y="714" font-size="14" fill="#FFF" font-weight="bold" font-family="serif" text-anchor="middle">书生</text>
</svg>"""


FACE_STYLES = {"CLASSIC", "FLORAL", "BOLD"}


def face_pattern_svg(style: str, colored: bool, x: float, y: float, rx: float, ry: float) -> str:
    """Local creative face patterns, separate from the MasterGo interface artwork."""
    if style not in FACE_STYLES:
        raise ValueError("不支持的脸谱样式")
    if style == "CLASSIC":
        return ""
    ink = "#243827" if colored else "#111111"
    if style == "FLORAL":
        paths = ('<path d="M-8,-20 Q0,-34 8,-20 Q0,-26 -8,-20 M-24,-2 Q-7,-18 -3,2 '
                 'M24,-2 Q7,-18 3,2 M-22,13 Q-5,4 -4,25 M22,13 Q5,4 4,25" '
                 f'fill="none" stroke="{ink}" stroke-width="3"/>')
    else:
        paths = (f'<path d="M0,-30 L9,-15 L0,-6 L-9,-15 Z M-26,-4 L-6,-11 L-11,8 L-26,13 Z '
                 f'M26,-4 L6,-11 L11,8 L26,13 Z" fill="{ink if colored else "none"}" '
                 f'stroke="{ink}" stroke-width="2.5"/>')
    return (f'<g id="face-{style}" transform="translate({x} {y}) scale({rx / 30} {ry / 35})">'
            f'{paths}</g>')


def generate_mask_role_puppet(role_type: str, archetype: str, colored: bool, colors: list) -> str:
    """Distinct net and comic-role templates; these are illustrative two-dimensional assets."""
    comic = archetype == "COMIC_CHOU"
    primary, gold, secondary, dark = colors[:4] if colored else ["none"] * 4
    skin, ink = ("#FBF4E8", "#2F2925") if colored else ("none", "#111111")
    face_fill = primary if not comic else skin
    nose_fill = "#FFFFFF" if colored else "none"
    robe = ("M215,310 L325,310 L340,500 L310,545 L230,545 L200,500 Z" if comic else
            "M200,310 L340,310 L355,560 Q270,590 185,560 Z")
    cap = ("M230,185 Q270,145 310,185 L306,202 L234,202 Z" if comic else
           "M224,185 L215,145 L245,165 L270,120 L295,165 L325,145 L316,185 Z")
    beard = ("M249,273 Q270,297 291,273" if comic else
             "M236,265 Q270,290 304,265 L292,330 L270,348 L248,330 Z")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 540 760" width="540" height="760" id="role-{archetype}">
  <rect width="540" height="760" rx="16" fill="#F8F4EC"/>
  <text x="270" y="48" text-anchor="middle" font-family="serif" font-size="19" fill="#2F2925">皮影创作 · {role_type}</text>
  <text x="270" y="70" text-anchor="middle" font-family="serif" font-size="11" fill="#776D65">本地二维模板参考 · 非实体装配成品</text>
  <g stroke="{ink}" stroke-width="3" stroke-linejoin="round">
    <path d="M230,535 L258,535 L250,665 L218,665 Z M282,535 L310,535 L324,665 L290,665 Z" fill="{secondary}"/>
    <path d="M208,660 L250,660 L258,685 L205,685 Z M290,660 L330,660 L345,685 L286,685 Z" fill="{dark}"/>
    <path d="{robe}" fill="{primary}"/>
    <path d="M215,325 L180,370 L145,430 L165,444 L215,400 L240,340 M325,325 L370,370 L395,430 L375,444 L325,400 L300,340" fill="{primary}"/>
    <circle cx="155" cy="437" r="11" fill="{skin}"/><circle cx="385" cy="437" r="11" fill="{skin}"/>
    <path d="M208,350 L332,350 M220,400 Q270,430 320,400 M222,470 Q270,500 318,470" fill="none" stroke="{gold if colored else ink}"/>
    <rect x="250" y="270" width="40" height="45" fill="{skin}"/>
    <ellipse cx="270" cy="232" rx="42" ry="50" fill="{face_fill}"/>
    <path d="{cap}" fill="{dark if comic else gold}"/>
    <path d="M236,216 Q250,207 261,220 M279,220 Q290,207 304,216" fill="none"/>
    <ellipse cx="250" cy="226" rx="7" ry="4" fill="{dark}"/><ellipse cx="290" cy="226" rx="7" ry="4" fill="{dark}"/>
    <path d="M270,229 L261,248 L279,248 M253,260 Q270,270 287,260" fill="none"/>
    <path d="{beard}" fill="{dark if not comic else "none"}"/>
    {f'<path d="M254,234 Q270,223 286,234 L283,251 Q270,257 257,251 Z" fill="{nose_fill}"/>' if comic else f'<path d="M239,202 L251,211 L239,237 M301,202 L289,211 L301,237" fill="none" stroke="{gold if colored else ink}"/>'}
    <circle cx="215" cy="325" r="6" fill="{gold}"/><circle cx="325" cy="325" r="6" fill="{gold}"/>
  </g>
  <g stroke="#8C827A" stroke-width="2" stroke-dasharray="4 3"><path d="M270,290 L120,715 M155,437 L75,715 M385,437 L465,715"/></g>
</svg>"""


def generate_shadow_puppet_svg(role_type="生角·津门书生", colored=True, prompt="", colors=None, face_style="CLASSIC"):
    svg = _generate_shadow_puppet_base_svg(role_type, colored, prompt, colors)
    archetype = detect_puppet_archetype(prompt, role_type)
    anchors = {"MONKEY_KING":(270,305,22,24), "FORTUNE_CHILD":(270,295,26,23),
               "WARRIOR_HERO":(276,300,14,13), "BEAUTY_DAN":(278,305,13,15),
               "SCHOLAR":(285,281,12,17), "PAINTED_JING":(270,232,40,47),
               "COMIC_CHOU":(270,232,40,47)}
    pattern = face_pattern_svg(face_style, colored, *anchors[archetype])
    return svg.replace("</svg>", pattern + "</svg>")


def _generate_shadow_puppet_template_base_svg(role_type: str = "生角·津门书生", prompt: str = "") -> str:
    """生成真实的 A4 激光切割与手工打印三签纸样排版，自适应大圣、福娃、武生等原型部件"""
    role_type = escape(role_type, quote=True)
    prompt = escape(prompt, quote=True)
    archetype = detect_puppet_archetype(prompt, role_type)

    if archetype == "MONKEY_KING":
        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 1130" width="800" height="1130">
  <rect width="100%" height="100%" fill="#FFFFFF"/>
  <rect x="30" y="30" width="740" height="1070" fill="none" stroke="#B64A44" stroke-width="1.5" stroke-dasharray="10,5"/>
  <text x="400" y="65" font-size="20" font-family="serif" font-weight="bold" fill="#2F2925" text-anchor="middle">《津韵润乡》美育手工坊 · A4激光雕刻纸样【齐天大圣·美猴王】</text>
  <text x="400" y="90" font-size="13" fill="#776D65" text-anchor="middle">天津国家级非遗皮影 · 红色实线激光外切，圆圈穿孔铆接，双根活动翎毛独立装配</text>

  <!-- 部件1：美猴王头茬 -->
  <g transform="translate(150, 220)">
    <rect x="-100" y="-80" width="200" height="170" fill="#FDFBF7" stroke="#CCC" stroke-dasharray="4,4" rx="8"/>
    <text x="0" y="-60" font-size="12" fill="#B63E2C" text-anchor="middle">【部件一：美猴王头茬与紧箍】</text>
    <path d="M-20,-10 L-25,-45 L-10,-30 L0,-50 L10,-30 L25,-45 L20,-10 Z" fill="none" stroke="#B64A44" stroke-width="2"/>
    <path d="M-15,-10 Q0,-18 15,-10 Q0,-5 -15,-10 Z" fill="none" stroke="#B64A44" stroke-width="2"/>
    <path d="M-10,-5 C-20,10 -5,25 10,20 C22,18 28,5 20,-5 Z" fill="none" stroke="#B64A44" stroke-width="2"/>
    <circle cx="0" cy="45" r="5" fill="none" stroke="#333" stroke-width="2"/>
    <text x="0" y="65" font-size="10" fill="#666" text-anchor="middle">○ 领签铆钉轴孔</text>
  </g>

  <!-- 部件2：左右双长翎毛 -->
  <g transform="translate(480, 220)">
    <rect x="-160" y="-80" width="320" height="170" fill="#FDFBF7" stroke="#CCC" stroke-dasharray="4,4" rx="8"/>
    <text x="0" y="-60" font-size="12" fill="#B63E2C" text-anchor="middle">【部件二：左右双根超长活动翎毛】</text>
    <path d="M-130,40 C-90,-20 -40,-60 10,-30 C-20,-20 -70,20 -110,40 Z" fill="none" stroke="#B64A44" stroke-width="2"/>
    <circle cx="-120" cy="38" r="4" fill="none" stroke="#333" stroke-width="2"/>
    <path d="M-130,70 C-70,10 0,-10 120,-30 C60,-10 -20,30 -110,75 Z" fill="none" stroke="#B64A44" stroke-width="2"/>
    <circle cx="-120" cy="73" r="4" fill="none" stroke="#333" stroke-width="2"/>
    <text x="0" y="70" font-size="10" fill="#666" text-anchor="middle">根部○孔用铜铆钉固定于冠顶</text>
  </g>

  <!-- 部件3：锁子甲躯干与虎皮战裙 -->
  <g transform="translate(200, 480)">
    <rect x="-140" y="-80" width="280" height="230" fill="#FDFBF7" stroke="#CCC" stroke-dasharray="4,4" rx="8"/>
    <text x="0" y="-60" font-size="12" fill="#B63E2C" text-anchor="middle">【部件三：铠甲躯干与虎皮裙】</text>
    <path d="M-45,-40 L45,-40 L55,40 L-55,40 Z" fill="none" stroke="#B64A44" stroke-width="2"/>
    <path d="M-55,40 L55,40 L65,110 Q0,125 -65,110 Z" fill="none" stroke="#B64A44" stroke-width="2"/>
    <circle cx="0" cy="-35" r="4" fill="none" stroke="#333" stroke-width="2"/>
    <circle cx="-42" cy="-32" r="4" fill="none" stroke="#333" stroke-width="2"/>
    <circle cx="42" cy="-32" r="4" fill="none" stroke="#333" stroke-width="2"/>
    <circle cx="-35" cy="105" r="4" fill="none" stroke="#333" stroke-width="2"/>
    <circle cx="35" cy="105" r="4" fill="none" stroke="#333" stroke-width="2"/>
  </g>

  <!-- 部件4：如意金箍棒与四肢 -->
  <g transform="translate(560, 480)">
    <rect x="-150" y="-80" width="300" height="230" fill="#FDFBF7" stroke="#CCC" stroke-dasharray="4,4" rx="8"/>
    <text x="0" y="-60" font-size="12" fill="#B63E2C" text-anchor="middle">【部件四：如意金箍棒与擎棒手】</text>
    <rect x="-130" y="-30" width="260" height="12" rx="4" fill="none" stroke="#B64A44" stroke-width="2"/>
    <circle cx="-130" cy="-24" r="9" fill="none" stroke="#B64A44" stroke-width="2"/>
    <circle cx="130" cy="-24" r="9" fill="none" stroke="#B64A44" stroke-width="2"/>
    <path d="M-100,20 L-40,40 L-30,55 L-85,45 Z" fill="none" stroke="#B64A44" stroke-width="2"/>
    <circle cx="-95" cy="22" r="4" fill="none" stroke="#333" stroke-width="2"/>
    <circle cx="-35" cy="48" r="4" fill="none" stroke="#333" stroke-width="2"/>
    <path d="M10,20 L70,40 L80,55 L25,45 Z" fill="none" stroke="#B64A44" stroke-width="2"/>
    <circle cx="15" cy="22" r="4" fill="none" stroke="#333" stroke-width="2"/>
    <circle cx="75" cy="48" r="4" fill="none" stroke="#333" stroke-width="2"/>
  </g>

  <!-- 底部装配指南 -->
  <g transform="translate(400, 840)">
    <rect x="-350" y="-50" width="700" height="180" fill="#F7FAFC" stroke="#E2E8F0" rx="10"/>
    <text x="-320" y="-20" font-size="14" font-weight="bold" fill="#2D3748">【齐天大圣皮影装配说明书】</text>
    <text x="-320" y="10" font-size="12" fill="#4A5568">1. 材料推荐：250g牛皮纸或透明PVC片激光雕刻裁切，按镂空线透空雕凿。</text>
    <text x="-320" y="35" font-size="12" fill="#4A5568">2. 翎毛装配：用子母铜铆钉将双根独立翎毛贯穿于美猴王冠帽顶端，保证活动翎毛可360°旋转翻飞。</text>
    <text x="-320" y="60" font-size="12" fill="#4A5568">3. 三签连接：以细铁丝将领签连接于脖颈轴孔，两手签分别固定于左腕与金箍棒棒身，实现翻云覆雨动态打斗。</text>
    <text x="-320" y="85" font-size="12" fill="#4A5568">4. 上色指导：矿物朱砂红涂抹脸谱面颊，泥金色套印锁子甲与金箍棒两端，虎皮战裙套染秋香黄并勾黑斑纹。</text>
  </g>
</svg>"""

    elif archetype == "FORTUNE_CHILD":
        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 1130" width="800" height="1130">
  <rect width="100%" height="100%" fill="#FFFFFF"/>
  <rect x="30" y="30" width="740" height="1070" fill="none" stroke="#B64A44" stroke-width="1.5" stroke-dasharray="10,5"/>
  <text x="400" y="65" font-size="20" font-family="serif" font-weight="bold" fill="#2F2925" text-anchor="middle">《津韵润乡》美育手工坊 · A4激光雕刻纸样【吉庆福娃·连年有余】</text>
  <text x="400" y="90" font-size="13" fill="#776D65" text-anchor="middle">天津杨柳青非遗版画年画娃娃 · 红色实线激光外切，圆圈穿孔铆接，大红锦鲤独立雕琢</text>

  <g transform="translate(180, 220)">
    <rect x="-120" y="-80" width="240" height="180" fill="#FDFBF7" stroke="#CCC" stroke-dasharray="4,4" rx="8"/>
    <text x="0" y="-60" font-size="12" fill="#B63E2C" text-anchor="middle">【部件一：福娃双抓髻头茬】</text>
    <circle cx="-30" cy="-20" r="18" fill="none" stroke="#B64A44" stroke-width="2"/>
    <circle cx="30" cy="-20" r="18" fill="none" stroke="#B64A44" stroke-width="2"/>
    <ellipse cx="0" cy="15" rx="30" ry="25" fill="none" stroke="#B64A44" stroke-width="2"/>
    <circle cx="0" cy="55" r="5" fill="none" stroke="#333" stroke-width="2"/>
    <text x="0" y="75" font-size="10" fill="#666" text-anchor="middle">○ 领签穿孔</text>
  </g>

  <g transform="translate(520, 220)">
    <rect x="-180" y="-80" width="360" height="180" fill="#FDFBF7" stroke="#CCC" stroke-dasharray="4,4" rx="8"/>
    <text x="0" y="-60" font-size="12" fill="#B63E2C" text-anchor="middle">【部件二：杨柳青招牌大红锦鲤】</text>
    <path d="M-130,20 C-90,-30 40,-40 120,10 C140,40 90,80 20,80 C-50,80 -110,60 -130,20 Z" fill="none" stroke="#B64A44" stroke-width="2.5"/>
    <circle cx="-30" cy="20" r="5" fill="none" stroke="#333" stroke-width="2"/>
    <circle cx="40" cy="20" r="5" fill="none" stroke="#333" stroke-width="2"/>
    <text x="0" y="70" font-size="10" fill="#666" text-anchor="middle">双手抓持位铆钉孔</text>
  </g>

  <g transform="translate(200, 480)">
    <rect x="-140" y="-80" width="280" height="230" fill="#FDFBF7" stroke="#CCC" stroke-dasharray="4,4" rx="8"/>
    <text x="0" y="-60" font-size="12" fill="#B63E2C" text-anchor="middle">【部件三：红肚兜与躯干】</text>
    <polygon points="0,-40 50,-15 55,120 -55,120 -50,-15" fill="none" stroke="#B64A44" stroke-width="2"/>
    <circle cx="0" cy="-35" r="4" fill="none" stroke="#333" stroke-width="2"/>
    <circle cx="-45" cy="110" r="4" fill="none" stroke="#333" stroke-width="2"/>
    <circle cx="45" cy="110" r="4" fill="none" stroke="#333" stroke-width="2"/>
  </g>

  <g transform="translate(560, 480)">
    <rect x="-150" y="-80" width="300" height="230" fill="#FDFBF7" stroke="#CCC" stroke-dasharray="4,4" rx="8"/>
    <text x="0" y="-60" font-size="12" fill="#B63E2C" text-anchor="middle">【部件四：莲花荷叶与胖手足】</text>
    <circle cx="-60" cy="20" r="35" fill="none" stroke="#B64A44" stroke-width="2"/>
    <path d="M40,-20 C20,-60 50,-70 55,-75 C60,-70 90,-60 70,-20 Z" fill="none" stroke="#B64A44" stroke-width="2"/>
    <circle cx="-60" cy="80" r="4" fill="none" stroke="#333" stroke-width="2"/>
    <circle cx="60" cy="80" r="4" fill="none" stroke="#333" stroke-width="2"/>
  </g>

  <g transform="translate(400, 840)">
    <rect x="-350" y="-50" width="700" height="180" fill="#F7FAFC" stroke="#E2E8F0" rx="10"/>
    <text x="-320" y="-20" font-size="14" font-weight="bold" fill="#2D3748">【吉庆福娃皮影装配说明书】</text>
    <text x="-320" y="10" font-size="12" fill="#4A5568">1. 年画意蕴：源自杨柳青经典《连年有余》，福娃怀抱活鲤，象征年年丰登。</text>
    <text x="-320" y="35" font-size="12" fill="#4A5568">2. 锦鲤可动：锦鲤单独剪裁后，以子母铜扣与福娃左右手连接，既可抱于胸前，亦可摆动出跃水之态。</text>
    <text x="-320" y="60" font-size="12" fill="#4A5568">3. 色彩套印：大红涂染肚兜与鲤鱼身躯，藤黄套印鱼鳞与长命锁，翡翠绿点缀并蒂莲叶。</text>
  </g>
</svg>"""

    else:
        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 1130" width="800" height="1130">
  <rect width="100%" height="100%" fill="#FFFFFF"/>
  <rect x="30" y="30" width="740" height="1070" fill="none" stroke="#B64A44" stroke-width="1.5" stroke-dasharray="10,5"/>
  <text x="400" y="65" font-size="20" font-family="serif" font-weight="bold" fill="#2F2925" text-anchor="middle">《津韵润乡》美育手工坊 · A4激光雕刻纸样【{role_type}】</text>
  <text x="400" y="90" font-size="13" fill="#776D65" text-anchor="middle">非遗皮影戏教具 · 红色实线剪裁，小圆圈穿孔铆接，蓝色虚线折叠</text>

  <g transform="translate(150, 220)">
    <rect x="-100" y="-80" width="200" height="170" fill="#FDFBF7" stroke="#CCC" stroke-dasharray="4,4" rx="8"/>
    <text x="0" y="-60" font-size="12" fill="#8B4A2F" text-anchor="middle">【部件一：头部与冠帽】</text>
    <path d="M-20,-30 Q-40,-50 -30,-70 Q0,-80 20,-60 L15,-20 Z" fill="none" stroke="#B64A44" stroke-width="2"/>
    <path d="M-10,-20 L10,-20 Q12,-35 25,-40 L28,-48 Q20,-50 18,-55 Q28,-60 25,-70 L5,-70" fill="none" stroke="#B64A44" stroke-width="2"/>
    <circle cx="0" cy="10" r="4" fill="none" stroke="#333" stroke-width="2"/>
    <text x="0" y="35" font-size="10" fill="#666" text-anchor="middle">○ 颈部领签穿孔</text>
  </g>

  <g transform="translate(480, 220)">
    <rect x="-160" y="-80" width="320" height="170" fill="#FDFBF7" stroke="#CCC" stroke-dasharray="4,4" rx="8"/>
    <text x="0" y="-60" font-size="12" fill="#8B4A2F" text-anchor="middle">【部件二：宽袍锦缎躯干】</text>
    <path d="M-45,-40 L45,-40 L55,40 L-55,40 Z" fill="none" stroke="#B64A44" stroke-width="2"/>
    <circle cx="0" cy="-35" r="4" fill="none" stroke="#333" stroke-width="2"/>
    <circle cx="-45" cy="-35" r="4" fill="none" stroke="#333" stroke-width="2"/>
    <circle cx="45" cy="-35" r="4" fill="none" stroke="#333" stroke-width="2"/>
    <circle cx="-35" cy="35" r="4" fill="none" stroke="#333" stroke-width="2"/>
    <circle cx="35" cy="35" r="4" fill="none" stroke="#333" stroke-width="2"/>
  </g>

  <g transform="translate(200, 480)">
    <rect x="-140" y="-80" width="280" height="230" fill="#FDFBF7" stroke="#CCC" stroke-dasharray="4,4" rx="8"/>
    <text x="0" y="-60" font-size="12" fill="#8B4A2F" text-anchor="middle">【部件三：分段双臂与道具手】</text>
    <path d="M-60,-20 L-20,-10 L-10,0 L-50,0 Z" fill="none" stroke="#B64A44" stroke-width="2"/>
    <circle cx="-55" cy="-15" r="4" fill="none" stroke="#333" stroke-width="2"/>
    <circle cx="-15" cy="-5" r="4" fill="none" stroke="#333" stroke-width="2"/>
    <path d="M20,-20 L60,-10 L50,0 L10,0 Z" fill="none" stroke="#B64A44" stroke-width="2"/>
    <circle cx="15" cy="-15" r="4" fill="none" stroke="#333" stroke-width="2"/>
    <circle cx="55" cy="-5" r="4" fill="none" stroke="#333" stroke-width="2"/>
  </g>

  <g transform="translate(560, 480)">
    <rect x="-150" y="-80" width="300" height="230" fill="#FDFBF7" stroke="#CCC" stroke-dasharray="4,4" rx="8"/>
    <text x="0" y="-60" font-size="12" fill="#8B4A2F" text-anchor="middle">【部件四：下袍双腿与云纹皂靴】</text>
    <path d="M-50,-20 L-20,-20 L-30,50 L-60,50 Z" fill="none" stroke="#B64A44" stroke-width="2"/>
    <path d="M20,-20 L50,-20 L60,50 L30,50 Z" fill="none" stroke="#B64A44" stroke-width="2"/>
    <circle cx="-35" cy="-15" r="4" fill="none" stroke="#333" stroke-width="2"/>
    <circle cx="35" cy="-15" r="4" fill="none" stroke="#333" stroke-width="2"/>
  </g>

  <g transform="translate(400, 840)">
    <rect x="-350" y="-50" width="700" height="180" fill="#F7FAFC" stroke="#E2E8F0" rx="10"/>
    <text x="-320" y="-20" font-size="14" font-weight="bold" fill="#2D3748">【乡村美育·津派皮影制作指南】</text>
    <text x="-320" y="10" font-size="12" fill="#4A5568">1. 打印或激光雕刻：直接将本文件发送至激光切割机，采用红色实线作为裁切层。</text>
    <text x="-320" y="35" font-size="12" fill="#4A5568">2. 关节连接：每个标注○的圆孔请用 2mm 活页铆钉或细铁丝穿孔弯折铆接。</text>
    <text x="-320" y="60" font-size="12" fill="#4A5568">3. 三签组装：颈部连接主杆领签，左右手端连接操纵签，即可在皮影幕布后表演生动剧目。</text>
  </g>
</svg>"""


def generate_shadow_puppet_template_svg(role_type="生角·津门书生", prompt="", face_style="CLASSIC"):
    svg = _generate_shadow_puppet_template_base_svg(role_type, prompt)
    svg = svg.replace("A4激光雕刻纸样", "A4比例纸样参考")
    svg = svg.replace("直接将本文件发送至激光切割机，采用红色实线作为裁切层。",
                      "纸样仅供学习参考；请先核对打印比例，设备切割需专业人员另行检查。")
    archetype = detect_puppet_archetype(prompt, role_type)
    if archetype in {"PAINTED_JING", "COMIC_CHOU"}:
        comic = archetype == "COMIC_CHOU"
        head = ('<g id="paper-' + archetype + '"><rect x="110" y="175" width="80" height="100" fill="#FDFBF7"/>'
                '<ellipse cx="150" cy="215" rx="26" ry="30" fill="none" stroke="#B64A44" stroke-width="2"/>'
                '<path d="M128,198 Q150,179 172,198 M134,210 L143,207 M157,207 L166,210 M142,230 Q150,236 158,230" fill="none" stroke="#B64A44" stroke-width="2"/>'
                + ('<path d="M140,212 Q150,207 160,212 L158,223 Q150,228 142,223 Z" fill="none" stroke="#B64A44" stroke-width="1.5"/>' if comic else
                   '<path d="M130,230 L140,252 L150,262 L160,252 L170,230 M129,194 L125,180 L140,188 L150,175 L160,188 L175,180 L171,194" fill="none" stroke="#B64A44" stroke-width="2"/>') +
                '<circle cx="150" cy="270" r="4" fill="none" stroke="#333" stroke-width="2"/></g>')
        pattern = head + face_pattern_svg(face_style, False, 150, 215, 24, 28)
    else:
        pattern = face_pattern_svg(face_style, False, 150, 170, 12, 17)
    warning = ('<text x="400" y="1080" text-anchor="middle" font-size="12" fill="#776D65">'
               '纸样参考：未验证实体装配与设备切割，请勿直接作为机器加工文件。</text>')
    return svg.replace("</svg>", pattern + warning + "</svg>")


def generate_bronze_taotie_svg(
    pattern_type: str = "饕餮纹",
    style: str = "氧化古铜",
    prompt: str = "",
    colors: list = None
) -> str:
    """生成真实的蓟州青铜器矢量纹饰 (支持编钟、双夔龙、饕餮兽面多原型及大模型铜绿色板注入)"""
    pattern_type = escape(pattern_type, quote=True)
    style = escape(style, quote=True)
    prompt = escape(prompt, quote=True)
    hex_colors = extract_hex_colors(colors, default_colors=["#4D5D53", "#C59B27", "#2B2625", "#1B3B34", "#E5DCC5"])
    c_patina = hex_colors[0]
    c_gold = hex_colors[1]
    c_dark = hex_colors[2]
    text = f"{prompt} {pattern_type}".lower()

    if any(k in text for k in ["编钟", "钟", "乐钟", "奏乐"]):
        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">
  <defs>
    <radialGradient id="bellBronze" cx="50%" cy="40%" r="60%">
      <stop offset="0%" stop-color="{c_patina}"/>
      <stop offset="60%" stop-color="{c_dark}"/>
      <stop offset="100%" stop-color="#141110"/>
    </radialGradient>
  </defs>
  <rect width="100%" height="100%" fill="#1A1817"/>
  <rect x="20" y="20" width="560" height="560" fill="none" stroke="{c_gold}" stroke-width="2" stroke-dasharray="6,4" rx="8"/>

  <text x="300" y="55" font-size="18" font-family="'Noto Serif SC', serif" font-weight="bold" fill="#E5DCC5" text-anchor="middle">蓟州青铜器 · 战国宴乐编钟矢量图谱</text>
  <text x="300" y="78" font-size="11" fill="{c_gold}" text-anchor="middle">双音编钟 · 三十六枚钟乳螺旋浮雕 · 错金云雷篆带</text>

  <g transform="translate(300, 310)">
    <path d="M-35,-190 Q0,-235 35,-190 L20,-160 L-20,-160 Z" fill="{c_gold}" stroke="#000" stroke-width="2"/>
    <circle cx="0" cy="-195" r="10" fill="{c_dark}" stroke="{c_gold}" stroke-width="2"/>

    <path d="M-110,-160 L110,-160 L145,120 Q0,80 -145,120 Z" fill="url(#bellBronze)" stroke="{c_gold}" stroke-width="3"/>
    <path d="M-145,120 Q0,75 145,120 Q0,95 -145,120 Z" fill="{c_gold}" opacity="0.6"/>

    <g transform="translate(-75, -80)">
      <circle cx="-25" cy="-30" r="7" fill="{c_gold}" stroke="{c_dark}" stroke-width="2"/>
      <circle cx="0" cy="-30" r="7" fill="{c_gold}" stroke="{c_dark}" stroke-width="2"/>
      <circle cx="25" cy="-30" r="7" fill="{c_gold}" stroke="{c_dark}" stroke-width="2"/>
      <circle cx="-25" cy="10" r="7" fill="{c_gold}" stroke="{c_dark}" stroke-width="2"/>
      <circle cx="0" cy="10" r="7" fill="{c_gold}" stroke="{c_dark}" stroke-width="2"/>
      <circle cx="25" cy="10" r="7" fill="{c_gold}" stroke="{c_dark}" stroke-width="2"/>
      <circle cx="-25" cy="50" r="7" fill="{c_gold}" stroke="{c_dark}" stroke-width="2"/>
      <circle cx="0" cy="50" r="7" fill="{c_gold}" stroke="{c_dark}" stroke-width="2"/>
      <circle cx="25" cy="50" r="7" fill="{c_gold}" stroke="{c_dark}" stroke-width="2"/>
    </g>
    <g transform="translate(75, -80)">
      <circle cx="-25" cy="-30" r="7" fill="{c_gold}" stroke="{c_dark}" stroke-width="2"/>
      <circle cx="0" cy="-30" r="7" fill="{c_gold}" stroke="{c_dark}" stroke-width="2"/>
      <circle cx="25" cy="-30" r="7" fill="{c_gold}" stroke="{c_dark}" stroke-width="2"/>
      <circle cx="-25" cy="10" r="7" fill="{c_gold}" stroke="{c_dark}" stroke-width="2"/>
      <circle cx="0" cy="10" r="7" fill="{c_gold}" stroke="{c_dark}" stroke-width="2"/>
      <circle cx="25" cy="10" r="7" fill="{c_gold}" stroke="{c_dark}" stroke-width="2"/>
      <circle cx="-25" cy="50" r="7" fill="{c_gold}" stroke="{c_dark}" stroke-width="2"/>
      <circle cx="0" cy="50" r="7" fill="{c_gold}" stroke="{c_dark}" stroke-width="2"/>
      <circle cx="25" cy="50" r="7" fill="{c_gold}" stroke="{c_dark}" stroke-width="2"/>
    </g>

    <path d="M-40,40 Q0,20 40,40 Q30,80 0,75 Q-30,80 -40,40 Z" fill="none" stroke="{c_gold}" stroke-width="2"/>
    <circle cx="0" cy="55" r="8" fill="{c_gold}"/>
    <text x="0" y="58" font-size="8" fill="#111" text-anchor="middle" font-weight="bold">音</text>
  </g>

  <rect x="255" y="535" width="90" height="28" fill="{c_dark}" stroke="{c_gold}" stroke-width="1.5" rx="4"/>
  <text x="300" y="554" font-size="13" fill="{c_gold}" font-family="serif" text-anchor="middle">蓟门金石</text>
</svg>"""

    elif any(k in text for k in ["夔龙", "双龙", "蟠螭", "龙纹"]):
        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">
  <defs>
    <radialGradient id="dragonBronze" cx="50%" cy="50%" r="60%">
      <stop offset="0%" stop-color="{c_patina}"/>
      <stop offset="70%" stop-color="{c_dark}"/>
      <stop offset="100%" stop-color="#141110"/>
    </radialGradient>
  </defs>
  <rect width="100%" height="100%" fill="#1A1817"/>
  <circle cx="300" cy="300" r="260" fill="url(#dragonBronze)" stroke="{c_gold}" stroke-width="3"/>
  <circle cx="300" cy="300" r="248" fill="none" stroke="{c_patina}" stroke-width="2" stroke-dasharray="6,4"/>

  <text x="300" y="65" font-size="18" font-family="'Noto Serif SC', serif" font-weight="bold" fill="#E5DCC5" text-anchor="middle">蓟州青铜器 · 双夔龙拱璧纹饰图谱</text>
  <text x="300" y="88" font-size="11" fill="{c_gold}" text-anchor="middle">对称双夔龙蟠曲 · 云雷地纹衬底 · 错金青铜重器</text>

  <g transform="translate(300, 300)">
    <circle cx="0" cy="0" r="50" fill="{c_dark}" stroke="{c_gold}" stroke-width="4"/>
    <circle cx="0" cy="0" r="25" fill="#1A1817" stroke="{c_gold}" stroke-width="2"/>

    <path d="M-45,-20 C-90,-120 -180,-80 -180,20 C-180,100 -120,160 -45,35" fill="none" stroke="{c_gold}" stroke-width="8"/>
    <path d="M-180,20 Q-210,0 -195,-35" fill="none" stroke="{c_gold}" stroke-width="5"/>
    <circle cx="-165" cy="-70" r="9" fill="{c_gold}" stroke="{c_dark}" stroke-width="2"/>

    <path d="M45,-20 C90,-120 180,-80 180,20 C180,100 120,160 45,35" fill="none" stroke="{c_gold}" stroke-width="8"/>
    <path d="M180,20 Q210,0 195,-35" fill="none" stroke="{c_gold}" stroke-width="5"/>
    <circle cx="165" cy="-70" r="9" fill="{c_gold}" stroke="{c_dark}" stroke-width="2"/>
  </g>

  <rect x="255" y="535" width="90" height="28" fill="{c_dark}" stroke="{c_gold}" stroke-width="1.5" rx="4"/>
  <text x="300" y="554" font-size="13" fill="{c_gold}" font-family="serif" text-anchor="middle">夔龙青铜</text>
</svg>"""

    else:
        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">
  <defs>
    <radialGradient id="taotieBg" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="{c_patina}"/>
      <stop offset="80%" stop-color="{c_dark}"/>
      <stop offset="100%" stop-color="#151211"/>
    </radialGradient>
  </defs>

  <rect width="100%" height="100%" fill="#1A1817"/>
  <rect x="20" y="20" width="560" height="560" fill="none" stroke="{c_gold}" stroke-width="2" stroke-dasharray="6,4" rx="8"/>

  <text x="300" y="60" font-size="18" font-family="'Noto Serif SC', serif" font-weight="bold" fill="#E5DCC5" text-anchor="middle">蓟州青铜器 · 馆藏商周【{pattern_type}】矢量图谱</text>
  <text x="300" y="82" font-size="11" fill="{c_gold}" text-anchor="middle">巨角圆睛 · 云雷衬底 · 范铸重器 · 质感：{style}</text>

  <g transform="translate(300, 310)">
    <path d="M-30,-70 C-90,-160 -190,-150 -180,-60 C-170,10 -110,-30 -80,-40" fill="none" stroke="{c_gold}" stroke-width="9" stroke-linecap="round"/>
    <path d="M30,-70 C90,-160 190,-150 180,-60 C170,10 110,-30 80,-40" fill="none" stroke="{c_gold}" stroke-width="9" stroke-linecap="round"/>

    <g transform="translate(-75, 10)">
      <rect x="-35" y="-20" width="70" height="40" rx="14" fill="{c_dark}" stroke="{c_gold}" stroke-width="4"/>
      <circle cx="0" cy="0" r="12" fill="{c_gold}"/>
      <circle cx="0" cy="0" r="5" fill="#111"/>
    </g>
    <g transform="translate(75, 10)">
      <rect x="-35" y="-20" width="70" height="40" rx="14" fill="{c_dark}" stroke="{c_gold}" stroke-width="4"/>
      <circle cx="0" cy="0" r="12" fill="{c_gold}"/>
      <circle cx="0" cy="0" r="5" fill="#111"/>
    </g>

    <path d="M-15,-60 L15,-60 L20,70 L-20,70 Z" fill="{c_dark}" stroke="{c_gold}" stroke-width="4"/>
    <path d="M-120,90 Q0,50 120,90 Q80,140 0,130 Q-80,140 -120,90 Z" fill="none" stroke="{c_gold}" stroke-width="6"/>
    <polygon points="-70,95 -60,120 -50,95" fill="{c_gold}"/>
    <polygon points="50,95 60,120 70,95" fill="{c_gold}"/>
  </g>

  <rect x="255" y="535" width="90" height="28" fill="{c_dark}" stroke="{c_gold}" stroke-width="1.5" rx="4"/>
  <text x="300" y="554" font-size="13" fill="{c_gold}" font-family="serif" text-anchor="middle">蓟门金石</text>
</svg>"""


def generate_ballad_sheet_svg(
    tune_name: str = "津韵新声·时调大鼓",
    rhythm_style: str = "骆派京韵大鼓快板",
    sheet_music_text: str = "1 1 5 5 | 6 6 5 - | 4 4 3 3 | 2 2 1 -",
    ballad_lyrics: str = "运河水阔映津门，曲艺声声唱古今。",
    prompt: str = "",
    colors: list = None
) -> str:
    """生成真实的津门曲艺时调简谱工尺谱与茶馆鼓板矢量艺术图谱"""
    tune_name = escape(tune_name, quote=True)
    rhythm_style = escape(rhythm_style, quote=True)
    sheet_music_text = escape(sheet_music_text, quote=True)
    ballad_lyrics = escape(ballad_lyrics, quote=True)
    prompt = escape(prompt, quote=True)
    hex_colors = extract_hex_colors(colors, default_colors=["#B63E2C", "#D6A85C", "#5C3317", "#1A1A1A", "#FAF5EB"])
    c_red = hex_colors[0]
    c_gold = hex_colors[1]
    c_wood = hex_colors[2]
    c_bg = hex_colors[4] if len(hex_colors) > 4 else "#FAF5EB"

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 460" width="700" height="460">
  <rect width="100%" height="100%" fill="{c_bg}" rx="12"/>
  <rect x="15" y="15" width="670" height="430" fill="none" stroke="{c_gold}" stroke-width="2" stroke-dasharray="6,3" rx="8"/>

  <text x="350" y="50" font-size="20" font-family="'Noto Serif SC', serif" font-weight="bold" fill="{c_red}" text-anchor="middle">津门曲艺非遗档案 · 【{tune_name}】</text>
  <text x="350" y="74" font-size="12" fill="#6B5B52" text-anchor="middle">传统五声音阶简谱对照 · 板眼：{rhythm_style} · 鼓板结合伴奏谱</text>

  <g transform="translate(50, 100)">
    <rect x="0" y="0" width="600" height="230" fill="#FFFDF9" stroke="#E2D7C8" rx="8"/>
    
    <g transform="translate(40, 45)">
      <circle cx="25" cy="25" r="22" fill="{c_red}" stroke="{c_gold}" stroke-width="2"/>
      <circle cx="25" cy="25" r="16" fill="#FFF" stroke="{c_gold}" stroke-width="1.5" stroke-dasharray="3,2"/>
      <rect x="60" y="8" width="12" height="36" rx="3" fill="{c_wood}" stroke="#333" stroke-width="1"/>
      <rect x="76" y="8" width="12" height="36" rx="3" fill="{c_wood}" stroke="#333" stroke-width="1"/>
    </g>
    <text x="145" y="48" font-size="14" font-weight="bold" fill="{c_red}">天津茶馆大鼓双楗与紫檀鸳鸯板伴奏板式</text>
    <text x="145" y="68" font-size="11" fill="#8C796C">调式：正宫调 1=G (宫 商 角 徵 羽 五声音阶) · 速度：中板转快板流水</text>

    <line x1="30" y1="95" x2="570" y2="95" stroke="#D1C4B2" stroke-width="1.5"/>
    <text x="40" y="135" font-size="18" font-family="monospace" font-weight="bold" fill="#2F2925" letter-spacing="4">{sheet_music_text}</text>
    
    <line x1="30" y1="160" x2="570" y2="160" stroke="#D1C4B2" stroke-width="1.5"/>
    <text x="40" y="195" font-size="15" font-family="'Noto Serif SC', serif" fill="{c_red}" font-weight="bold">【唱词】{ballad_lyrics}</text>
  </g>

  <g transform="translate(50, 350)">
    <text x="0" y="32" font-size="12" fill="#8C796C">天津市非物质文化遗产数字赋能乡村美育工程 · 智能曲艺创客音律档案</text>
    <rect x="530" y="5" width="48" height="48" fill="{c_red}" rx="4"/>
    <text x="554" y="26" font-size="13" fill="#FFF" font-family="'Noto Serif SC', serif" font-weight="bold" text-anchor="middle">津派</text>
    <text x="554" y="44" font-size="13" fill="#FFF" font-family="'Noto Serif SC', serif" font-weight="bold" text-anchor="middle">曲艺</text>
  </g>
</svg>"""


def generate_lacquer_raden_svg(
    title: str = "古法大漆螺钿月季圆盘",
    style: str = "天然矿物大漆",
    prompt: str = "",
    colors: list = None
) -> str:
    """生成真实的津派大漆螺钿髹饰矢量艺术图 (支持喜上眉梢/锦鲤戏莲/月季花鸟多题材及大模型色板注入)"""
    title = escape(title, quote=True)
    style = escape(style, quote=True)
    prompt = escape(prompt, quote=True)
    clean_title = title.strip("《》").strip()
    hex_colors = extract_hex_colors(colors, default_colors=["#B63E2C", "#D6A85C", "#7CE8E2", "#1A1817", "#FAF089"])
    c_gold = hex_colors[1]
    c_raden = hex_colors[2]
    text = f"{prompt} {title}".lower()

    if any(k in text for k in ["喜上眉梢", "喜鹊", "梅花"]):
        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">
  <defs>
    <radialGradient id="lqBg" cx="45%" cy="40%" r="60%">
      <stop offset="0%" stop-color="#262322"/>
      <stop offset="80%" stop-color="#110F0E"/>
      <stop offset="100%" stop-color="#050505"/>
    </radialGradient>
    <linearGradient id="lqRaden" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#7CE8E2"/>
      <stop offset="40%" stop-color="#B794F4"/>
      <stop offset="70%" stop-color="#FAF089"/>
      <stop offset="100%" stop-color="#68D391"/>
    </linearGradient>
  </defs>
  <rect width="100%" height="100%" fill="#141211"/>
  <circle cx="300" cy="300" r="260" fill="url(#lqBg)" stroke="#4A3B32" stroke-width="4"/>
  <circle cx="300" cy="300" r="252" fill="none" stroke="{c_gold}" stroke-width="2.5"/>

  <text x="300" y="65" font-size="18" font-family="'Noto Serif SC', serif" font-weight="bold" fill="#EAD6B8" text-anchor="middle">津派传统大漆螺钿 · 【{clean_title}】</text>
  <text x="300" y="88" font-size="11" fill="#A89485" text-anchor="middle">点螺细嵌 · 喜鹊双飞登梅 · 风格：{style}</text>

  <g transform="translate(300, 300)">
    <path d="M-190,160 Q-80,60 0,80 Q80,100 180,-40" fill="none" stroke="{c_gold}" stroke-width="7" stroke-linecap="round"/>
    <path d="M0,80 Q-30,-20 -60,-80" fill="none" stroke="{c_gold}" stroke-width="4"/>
    
    <circle cx="-60" cy="-80" r="14" fill="url(#lqRaden)" stroke="{c_gold}" stroke-width="1.5"/>
    <circle cx="-30" cy="-40" r="10" fill="url(#lqRaden)" stroke="{c_gold}" stroke-width="1.5"/>
    <circle cx="80" cy="20" r="12" fill="url(#lqRaden)" stroke="{c_gold}" stroke-width="1.5"/>
    <circle cx="140" cy="-20" r="11" fill="url(#lqRaden)" stroke="{c_gold}" stroke-width="1.5"/>

    <g transform="translate(-40, 30) rotate(-20)">
      <path d="M-40,0 Q0,-20 40,-10 Q30,15 -10,15 Z" fill="url(#lqRaden)" stroke="{c_gold}" stroke-width="1.5"/>
      <path d="M40,-10 L80,-25 L65,-5 Z" fill="url(#lqRaden)"/>
      <circle cx="-35" cy="-5" r="3" fill="#FFF"/>
    </g>
  </g>

  <rect x="270" y="525" width="60" height="28" fill="#8B4A2F" rx="4"/>
  <text x="300" y="544" font-size="13" fill="#FFF" font-family="serif" font-weight="bold" text-anchor="middle">津门大漆</text>
</svg>"""

    elif any(k in text for k in ["锦鲤", "鱼", "莲", "荷"]):
        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">
  <defs>
    <radialGradient id="lqFishBg" cx="45%" cy="40%" r="60%">
      <stop offset="0%" stop-color="#262322"/>
      <stop offset="80%" stop-color="#110F0E"/>
      <stop offset="100%" stop-color="#050505"/>
    </radialGradient>
    <linearGradient id="lqFishRaden" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FF7675"/>
      <stop offset="50%" stop-color="#FAF089"/>
      <stop offset="100%" stop-color="#7CE8E2"/>
    </linearGradient>
  </defs>
  <rect width="100%" height="100%" fill="#141211"/>
  <circle cx="300" cy="300" r="260" fill="url(#lqFishBg)" stroke="#4A3B32" stroke-width="4"/>
  <circle cx="300" cy="300" r="252" fill="none" stroke="{c_gold}" stroke-width="2.5"/>

  <text x="300" y="65" font-size="18" font-family="'Noto Serif SC', serif" font-weight="bold" fill="#EAD6B8" text-anchor="middle">津派传统大漆螺钿 · 【{clean_title}】</text>
  <text x="300" y="88" font-size="11" fill="#A89485" text-anchor="middle">点螺锦鲤戏莲 · 风格：{style}</text>

  <g transform="translate(300, 300)">
    <path d="M-140,120 Q-70,90 0,120 T140,120" fill="none" stroke="{c_raden}" stroke-width="2" opacity="0.6"/>
    <g transform="translate(-50, -40) rotate(45)">
      <path d="M-60,0 C-30,-25 30,-25 60,0 C40,20 -40,20 -60,0 Z" fill="url(#lqFishRaden)" stroke="{c_gold}" stroke-width="1.8"/>
      <path d="M60,0 Q90,-20 100,5 Q80,20 60,0 Z" fill="url(#lqFishRaden)"/>
    </g>
    <g transform="translate(50, 40) rotate(-135)">
      <path d="M-60,0 C-30,-25 30,-25 60,0 C40,20 -40,20 -60,0 Z" fill="url(#lqFishRaden)" stroke="{c_gold}" stroke-width="1.8"/>
      <path d="M60,0 Q90,-20 100,5 Q80,20 60,0 Z" fill="url(#lqFishRaden)"/>
    </g>
  </g>

  <rect x="270" y="525" width="60" height="28" fill="#8B4A2F" rx="4"/>
  <text x="300" y="544" font-size="13" fill="#FFF" font-family="serif" font-weight="bold" text-anchor="middle">津门大漆</text>
</svg>"""

    else:
        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">
  <defs>
    <radialGradient id="lacquerBlack" cx="45%" cy="40%" r="60%">
      <stop offset="0%" stop-color="#262322"/>
      <stop offset="70%" stop-color="#141211"/>
      <stop offset="100%" stop-color="#080706"/>
    </radialGradient>
    <linearGradient id="radenCyan" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#7CE8E2"/>
      <stop offset="35%" stop-color="#B794F4"/>
      <stop offset="70%" stop-color="#F6E05E"/>
      <stop offset="100%" stop-color="#68D391"/>
    </linearGradient>
    <linearGradient id="radenPink" x1="100%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#FEB2B2"/>
      <stop offset="50%" stop-color="#FAF089"/>
      <stop offset="100%" stop-color="#9AE6B4"/>
    </linearGradient>
  </defs>

  <rect width="100%" height="100%" fill="#1A1817"/>
  <circle cx="300" cy="300" r="260" fill="url(#lacquerBlack)" stroke="#4A3B32" stroke-width="4"/>
  <circle cx="300" cy="300" r="252" fill="none" stroke="{c_gold}" stroke-width="2.5"/>

  <text x="300" y="65" font-size="18" font-family="'Noto Serif SC', serif" font-weight="bold" fill="#EAD6B8" text-anchor="middle">津派传统大漆髹饰 · 【{clean_title}】</text>
  <text x="300" y="88" font-size="11" fill="#A89485" text-anchor="middle">髹漆刮灰 · 点螺细嵌 · 推光出彩 · 风格：{style}</text>

  <g transform="translate(300, 305)">
    <path d="M-140,140 Q-70,110 0,140 T140,140" fill="none" stroke="url(#radenCyan)" stroke-width="2" opacity="0.6"/>
    <path d="M0,-30 C-45,-90 -10,-150 0,-150 C10,-150 45,-90 0,-30 Z" fill="url(#radenCyan)" stroke="{c_gold}" stroke-width="1.8"/>
    <path d="M-25,-20 C-95,-45 -140,-15 -135,-3 C-130,10 -75,2 -25,-20 Z" fill="url(#radenPink)" stroke="{c_gold}" stroke-width="1.8"/>
    <path d="M25,-20 C95,-45 140,-15 135,-3 C130,10 75,2 25,-20 Z" fill="url(#radenPink)" stroke="{c_gold}" stroke-width="1.8"/>
    <circle cx="0" cy="-5" r="24" fill="#0E0D0D" stroke="{c_gold}" stroke-width="2"/>
    <circle cx="0" cy="-5" r="14" fill="url(#radenCyan)"/>
  </g>

  <rect x="270" y="525" width="60" height="28" fill="#8B4A2F" rx="4"/>
  <text x="300" y="544" font-size="13" fill="#FFF" font-family="serif" font-weight="bold" text-anchor="middle">津门大漆</text>
</svg>"""


def generate_lacquer_design_svg(title: str, pattern: str = "FLORAL", prompt: str = "", colors: list = None) -> str:
    """Create a local 2D motif reference; no image inference or material simulation."""
    palette = extract_hex_colors(colors, ["#C4A35A", "#D4AF37", "#2D5A4A", "#1A1817", "#F7F4ED"])
    primary, gold, green, ink, paper = palette[:5]
    note = "本地二维纹样参考；未分析草图、应用LoRA或验证实体制作。"
    if pattern == "FLORAL":
        svg = generate_lacquer_raden_svg(title, "本地花鸟模板", prompt=prompt, colors=palette)
        for old in ["#7CE8E2", "#B794F4", "#FF7675", "#FEB2B2", "#9AE6B4"]:
            svg = svg.replace(old, primary)
        return svg.rsplit('</svg>', 1)[0] + f'<text x="300" y="585" font-size="10" fill="#EAD6B8" text-anchor="middle">{note}</text></svg>'
    label = "几何纹样" if pattern == "GEOMETRIC" else "吉祥文字"
    if pattern == "GEOMETRIC":
        motifs = []
        for row in range(3):
            for col in range(3):
                x, y = 170 + col * 130, 175 + row * 130
                motifs.append(f'<g transform="translate({x},{y})"><path d="M0,-48 L48,0 L0,48 L-48,0 Z" fill="{primary}" stroke="{gold}" stroke-width="3"></path><path d="M0,-29 L29,0 L0,29 L-29,0 Z" fill="{ink}" stroke="{green}" stroke-width="3"></path><circle r="10" fill="{gold}"></circle></g>')
        art = ''.join(motifs)
    else:
        character = next((char for char in prompt if char in "福寿喜和"), "福")
        art = (f'<circle cx="300" cy="300" r="178" fill="{primary}" stroke="{gold}" stroke-width="5"></circle>'
               f'<path d="M300,95 L505,300 L300,505 L95,300 Z" fill="none" stroke="{green}" stroke-width="8"></path>'
               f'<text x="300" y="358" font-family="serif" font-size="174" fill="{paper}" text-anchor="middle">{character}</text>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">'
            f'<rect width="600" height="600" fill="{ink}"></rect>'
            f'<rect x="32" y="32" width="536" height="536" rx="24" fill="none" stroke="{gold}" stroke-width="2"></rect>'
            f'<text x="300" y="65" font-size="18" font-family="serif" fill="{paper}" text-anchor="middle">{escape(title[:60], quote=True)}</text>'
            f'<text x="300" y="88" font-size="11" fill="{gold}" text-anchor="middle">{label} · 本地模板</text>'
            f'{art}<text x="300" y="585" font-size="10" fill="{paper}" text-anchor="middle">{note}</text></svg>')


def generate_mesh_preview_svg(title: str = "津门皮影三维骨骼") -> str:
    """生成三维骨骼与网格模型的等轴测预览矢量图"""
    title = escape(title, quote=True)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 450" width="600" height="450">
  <rect width="100%" height="100%" fill="#111827" rx="12"/>
  <defs>
    <pattern id="grid3d" width="30" height="30" patternUnits="userSpaceOnUse">
      <path d="M 30 0 L 0 0 0 30" fill="none" stroke="#1F2937" stroke-width="1"/>
    </pattern>
  </defs>
  <rect width="100%" height="100%" fill="url(#grid3d)"/>
  
  <text x="300" y="45" font-size="18" fill="#60A5FA" font-family="monospace" font-weight="bold" text-anchor="middle">GLTF 3D MESH TOPOLOGY · {title}</text>
  <text x="300" y="70" font-size="12" fill="#9CA3AF" text-anchor="middle">三签活动骨骼拓扑 · 实时四元数驱动节点</text>

  <g transform="translate(300, 240)">
    <polygon points="0,-120 70,-40 50,80 -50,80 -70,-40" fill="rgba(59, 130, 246, 0.15)" stroke="#3B82F6" stroke-width="2"/>
    <line x1="0" y1="-120" x2="0" y2="80" stroke="#60A5FA" stroke-width="2" stroke-dasharray="4,2"/>
    <line x1="-70" y1="-40" x2="70" y2="-40" stroke="#60A5FA" stroke-width="1.5"/>

    <circle cx="0" cy="-120" r="7" fill="#F59E0B" stroke="#FFF" stroke-width="2"/>
    <circle cx="-70" cy="-40" r="6" fill="#10B981" stroke="#FFF" stroke-width="2"/>
    <circle cx="70" cy="-40" r="6" fill="#10B981" stroke="#FFF" stroke-width="2"/>
    <circle cx="-50" cy="80" r="6" fill="#10B981" stroke="#FFF" stroke-width="2"/>
    <circle cx="50" cy="80" r="6" fill="#10B981" stroke="#FFF" stroke-width="2"/>
    
    <line x1="0" y1="-120" x2="-120" y2="120" stroke="#EC4899" stroke-width="2"/>
    <circle cx="-120" cy="120" r="5" fill="#EC4899"/>
    <line x1="-70" y1="-40" x2="-160" y2="120" stroke="#EC4899" stroke-width="2"/>
    <circle cx="-160" cy="120" r="5" fill="#EC4899"/>
    <line x1="70" y1="-40" x2="160" y2="120" stroke="#EC4899" stroke-width="2"/>
    <circle cx="160" cy="120" r="5" fill="#EC4899"/>
  </g>

  <text x="300" y="415" font-size="12" fill="#6B7280" font-family="monospace" text-anchor="middle">Vertices: 1,482 | Joints: 16 | Rig: Standard Three-Rod Puppetry</text>
</svg>"""


def save_generated_asset(filename: str, content: str) -> str:
    """将生成的真实非遗 SVG/数据写入静态托管路径并返回访问 URL"""
    content = sanitize_svg(content)
    filepath = os.path.join(STATIC_GENERATED_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return f"/static/generated/{filename}"
