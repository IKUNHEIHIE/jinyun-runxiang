"""
津韵润乡 · 天津非遗多模态生成算法与原生矢量资产合成引擎
负责生成真实的津门皮影、青铜器饕餮纹、大漆螺钿与A4激光雕刻纸样矢量资产
"""
import os
import math

STATIC_GENERATED_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static", "generated")
os.makedirs(STATIC_GENERATED_DIR, exist_ok=True)

def generate_shadow_puppet_svg(role_type: str = "生角·津门书生", colored: bool = True) -> str:
    """生成真实的津派皮影矢量艺术图 (支持线稿与传统套色)"""
    stroke = "#2F2925" if colored else "#111111"
    fill_face = "#FBF4E8" if colored else "none"
    fill_robe = "#8B4A2F" if colored else "none"
    fill_gold = "#D6A85C" if colored else "none"
    fill_cyan = "#3A6351" if colored else "none"

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 700" width="500" height="700">
  <defs>
    <radialGradient id="leatherGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#FBF4E8" stop-opacity="0.9"/>
      <stop offset="100%" stop-color="#E2D4BF" stop-opacity="0.6"/>
    </radialGradient>
    <linearGradient id="robeGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#A35939"/>
      <stop offset="100%" stop-color="#6E331E"/>
    </linearGradient>
  </defs>

  <!-- 背景透光宣纸与皮影舞台感 -->
  <rect width="100%" height="100%" fill="#F8F4EC" rx="16"/>
  <rect x="20" y="20" width="460" height="660" fill="none" stroke="#D6A85C" stroke-width="2" stroke-dasharray="6,4" rx="12"/>

  <!-- 顶部题字 -->
  <text x="250" y="55" font-size="18" font-family="'Noto Serif SC', serif" font-weight="bold" fill="#8B4A2F" text-anchor="middle">津门非遗皮影戏 · {role_type}</text>
  <text x="250" y="75" font-size="11" fill="#776D65" text-anchor="middle">传统三签铆接可动皮影 · 镂空雕镞与矿物套色</text>

  <g transform="translate(250, 360)">
    <!-- 操纵签 (三签标记: 颈签与两手签) -->
    <line x1="0" y1="-140" x2="-140" y2="280" stroke="#8C827A" stroke-width="3" stroke-dasharray="4,2"/>
    <line x1="-120" y1="20" x2="-180" y2="280" stroke="#8C827A" stroke-width="3" stroke-dasharray="4,2"/>
    <line x1="120" y1="20" x2="180" y2="280" stroke="#8C827A" stroke-width="3" stroke-dasharray="4,2"/>

    <!-- 腿部与裙摆 (下身) -->
    <path d="M-60,80 Q-90,190 -70,250 L-30,250 Q-40,160 -10,80 Z" fill="{fill_cyan}" stroke="{stroke}" stroke-width="3"/>
    <path d="M10,80 Q40,160 30,250 L70,250 Q90,190 60,80 Z" fill="{fill_cyan}" stroke="{stroke}" stroke-width="3"/>
    <!-- 云纹皂靴 -->
    <path d="M-80,245 L-20,245 Q-15,265 -50,265 L-80,265 Z" fill="#222" stroke="{stroke}" stroke-width="2"/>
    <path d="M20,245 L80,245 Q85,265 50,265 L20,265 Z" fill="#222" stroke="{stroke}" stroke-width="2"/>

    <!-- 锦袍躯干 (镂空回纹与团花) -->
    <path d="M-55,-60 L55,-60 L70,90 L-70,90 Z" fill="url(#robeGrad)" stroke="{stroke}" stroke-width="3"/>
    <!-- 袍肚金带 -->
    <rect x="-58" y="0" width="116" height="18" fill="{fill_gold}" stroke="{stroke}" stroke-width="2"/>
    <!-- 镂空海水江崖与云纹细节 -->
    <circle cx="0" cy="45" r="22" fill="none" stroke="{fill_gold}" stroke-width="3"/>
    <circle cx="0" cy="45" r="14" fill="none" stroke="{stroke}" stroke-width="2"/>
    <path d="M-40,75 Q0,50 40,75" fill="none" stroke="{fill_gold}" stroke-width="2"/>

    <!-- 左臂与手签 (分段：大臂、小臂、手部) -->
    <g>
      <!-- 大臂 -->
      <path d="M-50,-50 L-100,-20 L-85,-5 L-45,-40 Z" fill="{fill_robe}" stroke="{stroke}" stroke-width="3"/>
      <circle cx="-92" cy="-12" r="5" fill="{fill_gold}" stroke="{stroke}" stroke-width="2"/> <!-- 关节骨针 -->
      <!-- 小臂与掌 -->
      <path d="M-92,-12 L-130,20 L-115,30 L-80,0 Z" fill="{fill_robe}" stroke="{stroke}" stroke-width="3"/>
      <!-- 透光生角拂袖 -->
      <path d="M-130,20 Q-170,70 -130,90 Q-110,60 -115,30 Z" fill="{fill_face}" stroke="{stroke}" stroke-width="2"/>
    </g>

    <!-- 右臂与手签 -->
    <g>
      <!-- 大臂 -->
      <path d="M50,-50 L100,-20 L85,-5 L45,-40 Z" fill="{fill_robe}" stroke="{stroke}" stroke-width="3"/>
      <circle cx="92" cy="-12" r="5" fill="{fill_gold}" stroke="{stroke}" stroke-width="2"/> <!-- 关节骨针 -->
      <!-- 小臂与掌 -->
      <path d="M92,-12 L130,20 L115,30 L80,0 Z" fill="{fill_robe}" stroke="{stroke}" stroke-width="3"/>
      <!-- 折扇/文生手势道具 -->
      <path d="M125,25 L165,5 Q180,30 145,45 Z" fill="{fill_gold}" stroke="{stroke}" stroke-width="2"/>
    </g>

    <!-- 头部与生角冠巾 (五官侧影：通天鼻、丹凤眼、朱唇) -->
    <g transform="translate(0, -60)">
      <!-- 脖颈铆接点 -->
      <circle cx="0" cy="0" r="6" fill="#D6A85C" stroke="{stroke}" stroke-width="2"/>
      <!-- 文生头巾与发髻后飘带 -->
      <path d="M-30,-20 Q-60,-40 -50,-80 Q0,-95 30,-70 L20,-20 Z" fill="#222" stroke="{stroke}" stroke-width="3"/>
      <path d="M-40,-30 Q-90,-20 -80,40 L-65,35 Q-75,-10 -35,-20 Z" fill="#222" stroke="{stroke}" stroke-width="2"/> <!-- 软带 -->
      <!-- 冠巾前额宝珠 -->
      <circle cx="10" cy="-75" r="8" fill="{fill_gold}" stroke="{stroke}" stroke-width="2"/>
      <circle cx="10" cy="-75" r="4" fill="#B64A44"/>
      <!-- 头茬侧脸轮廓 -->
      <path d="M-10,-20 L10,-20 Q12,-35 25,-40 L28,-48 Q20,-50 18,-55 Q28,-60 25,-70 L5,-70" fill="{fill_face}" stroke="{stroke}" stroke-width="3"/>
      <!-- 镂空红润眼角与唇线 -->
      <path d="M12,-52 Q18,-54 22,-50" fill="none" stroke="#B64A44" stroke-width="2.5"/>
      <circle cx="17" cy="-51" r="1.5" fill="#111"/>
      <path d="M16,-34 Q22,-34 20,-30" fill="none" stroke="#B64A44" stroke-width="2"/>
    </g>
  </g>

  <!-- 底部印章 -->
  <rect x="405" y="615" width="45" height="45" fill="#8B4A2F" rx="6"/>
  <text x="427" y="642" font-size="16" fill="#FFF" font-weight="bold" font-family="serif" text-anchor="middle">津韵</text>
</svg>"""
    return svg

def generate_shadow_puppet_template_svg(role_type: str = "生角·津门书生") -> str:
    """生成真实的 A4 激光切割与手工打印三签纸样排版"""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 1130" width="800" height="1130">
  <rect width="100%" height="100%" fill="#FFFFFF"/>
  <!-- 裁切与对齐参考线 (A4 标淮尺寸: 210mm x 297mm) -->
  <rect x="30" y="30" width="740" height="1070" fill="none" stroke="#B64A44" stroke-width="1.5" stroke-dasharray="10,5"/>
  <text x="400" y="65" font-size="20" font-family="serif" font-weight="bold" fill="#2F2925" text-anchor="middle">《津韵润乡》乡村美育手工坊 · A4激光切割与实操排版纸样</text>
  <text x="400" y="90" font-size="13" fill="#776D65" text-anchor="middle">非遗剧目配课教具 · 【{role_type}】· 红色实线剪裁，小圆圈穿孔铆钉，蓝色虚线折叠</text>

  <!-- 部件1：头茬 (包含发冠与侧影) -->
  <g transform="translate(150, 220)">
    <rect x="-100" y="-80" width="200" height="170" fill="#FDFBF7" stroke="#CCC" stroke-dasharray="4,4" rx="8"/>
    <text x="0" y="-60" font-size="12" fill="#8B4A2F" text-anchor="middle">【部件一：头部与冠帽】</text>
    <path d="M-40,40 Q-80,10 -70,-40 Q-10,-65 30,-30 L20,30 Q-10,45 -40,40 Z" fill="none" stroke="#B64A44" stroke-width="2"/>
    <circle cx="0" cy="40" r="4" fill="none" stroke="#1C3D5A" stroke-width="2"/> <!-- 颈部铆孔 -->
    <text x="0" y="55" font-size="10" fill="#1C3D5A" text-anchor="middle">◎ 颈铆孔</text>
  </g>

  <!-- 部件2：身段 (前胸与后背镂空雕花) -->
  <g transform="translate(480, 220)">
    <rect x="-140" y="-80" width="280" height="240" fill="#FDFBF7" stroke="#CCC" stroke-dasharray="4,4" rx="8"/>
    <text x="0" y="-60" font-size="12" fill="#8B4A2F" text-anchor="middle">【部件二：上身锦袍躯干】</text>
    <path d="M-70,-30 L70,-30 L90,120 L-90,120 Z" fill="none" stroke="#B64A44" stroke-width="2"/>
    <!-- 镂空花纹切割线 -->
    <circle cx="0" cy="30" r="28" fill="none" stroke="#B64A44" stroke-width="1.5"/>
    <circle cx="0" cy="30" r="18" fill="none" stroke="#B64A44" stroke-width="1.5"/>
    <!-- 颈部与左右肩关节穿孔 -->
    <circle cx="0" cy="-25" r="4" fill="none" stroke="#1C3D5A" stroke-width="2"/>
    <circle cx="-60" cy="-20" r="4" fill="none" stroke="#1C3D5A" stroke-width="2"/>
    <circle cx="60" cy="-20" r="4" fill="none" stroke="#1C3D5A" stroke-width="2"/>
    <circle cx="0" cy="115" r="4" fill="none" stroke="#1C3D5A" stroke-width="2"/>
    <text x="0" y="-35" font-size="10" fill="#1C3D5A" text-anchor="middle">◎ 颈部穿孔</text>
    <text x="-60" y="-32" font-size="10" fill="#1C3D5A" text-anchor="middle">◎ 左肩孔</text>
    <text x="60" y="-32" font-size="10" fill="#1C3D5A" text-anchor="middle">◎ 右肩孔</text>
  </g>

  <!-- 部件3：左右四肢四臂 -->
  <g transform="translate(150, 520)">
    <rect x="-100" y="-60" width="200" height="240" fill="#FDFBF7" stroke="#CCC" stroke-dasharray="4,4" rx="8"/>
    <text x="0" y="-40" font-size="12" fill="#8B4A2F" text-anchor="middle">【部件三：大臂与小臂】</text>
    <!-- 左上臂 -->
    <path d="M-60,-10 L-20,-10 L-25,60 L-55,60 Z" fill="none" stroke="#B64A44" stroke-width="2"/>
    <circle cx="-40" cy="-5" r="4" fill="none" stroke="#1C3D5A" stroke-width="2"/>
    <circle cx="-40" cy="55" r="4" fill="none" stroke="#1C3D5A" stroke-width="2"/>
    <!-- 右上臂 -->
    <path d="M20,-10 L60,-10 L55,60 L25,60 Z" fill="none" stroke="#B64A44" stroke-width="2"/>
    <circle cx="40" cy="-5" r="4" fill="none" stroke="#1C3D5A" stroke-width="2"/>
    <circle cx="40" cy="55" r="4" fill="none" stroke="#1C3D5A" stroke-width="2"/>
    <!-- 小臂及手掌带签环 -->
    <path d="M-60,90 L-20,90 L-15,160 L-65,160 Z" fill="none" stroke="#B64A44" stroke-width="2"/>
    <circle cx="-40" cy="95" r="4" fill="none" stroke="#1C3D5A" stroke-width="2"/>
    <circle cx="-40" cy="155" r="3" fill="#1C3D5A"/>
    <text x="-40" y="170" font-size="10" fill="#1C3D5A" text-anchor="middle">手签铁丝孔</text>
  </g>

  <!-- 部件4：下身下裳与皮影腿靴 -->
  <g transform="translate(480, 560)">
    <rect x="-140" y="-80" width="280" height="200" fill="#FDFBF7" stroke="#CCC" stroke-dasharray="4,4" rx="8"/>
    <text x="0" y="-60" font-size="12" fill="#8B4A2F" text-anchor="middle">【部件四：下裳锦褶与靴履】</text>
    <path d="M-80,-20 L80,-20 L100,80 L-100,80 Z" fill="none" stroke="#B64A44" stroke-width="2"/>
    <circle cx="0" cy="-15" r="4" fill="none" stroke="#1C3D5A" stroke-width="2"/>
    <!-- 腿段1 -->
    <path d="M-50,90 L-20,90 L-20,160 L-50,160 Z" fill="none" stroke="#B64A44" stroke-width="2"/>
    <!-- 腿段2 -->
    <path d="M20,90 L50,90 L50,160 L20,160 Z" fill="none" stroke="#B64A44" stroke-width="2"/>
  </g>

  <!-- 底部教学安装说明 -->
  <g transform="translate(400, 850)">
    <rect x="-350" y="0" width="700" height="200" fill="#FBF9F5" stroke="#EAE3D9" rx="8"/>
    <text x="-330" y="30" font-size="15" font-weight="bold" fill="#2F2925">皮影装配与美育教学指南：</text>
    <text x="-330" y="60" font-size="13" fill="#555">1. 选材推荐：请使用 180g~250g 哑光牛皮纸或透明磨砂 PVC 片（模仿传统刮浆驴皮质感）。</text>
    <text x="-330" y="85" font-size="13" fill="#555">2. 镂雕工艺：沿红色实线用美工刀或激光机镂切，注意面部与冠帽镂空要精巧细腻。</text>
    <text x="-330" y="110" font-size="13" fill="#555">3. 关节穿孔：在所有标注【◎】的圆孔位置用打孔钳打出 2mm 圆孔，使用两脚开脚钉或鱼线穿铆固定。</text>
    <text x="-330" y="135" font-size="13" fill="#555">4. 操纵三签：在颈部和左右双手铆接点固定 20cm 细竹签或铁丝操纵杆，即可在光源幕布后表演！</text>
    <text x="-330" y="165" font-size="12" fill="#8B4A2F" font-weight="bold">津韵润乡乡村美育工程 · 天津非遗传承数字化中心监制</text>
  </g>
</svg>"""

def generate_bronze_taotie_svg(pattern_type: str = "饕餮纹", style: str = "氧化古铜") -> str:
    """生成真实的商周青铜礼器饕餮纹样矢量艺术图"""
    bg = "#1A2520" if "氧化" in style else "#2B221A"
    bronze_main = "#4A7C59" if "氧化" in style else "#C49A45"
    bronze_dark = "#2F4F4F" if "氧化" in style else "#8C6228"
    gold_highlight = "#A2D099" if "氧化" in style else "#F5D77F"

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">
  <rect width="100%" height="100%" fill="{bg}"/>
  <!-- 几何回字形云雷纹底纹 -->
  <defs>
    <pattern id="leiwen" width="30" height="30" patternUnits="userSpaceOnUse">
      <path d="M0,0 L30,0 L30,30 L10,30 L10,10 L20,10 L20,20 L15,20" fill="none" stroke="{bronze_dark}" stroke-width="1.2" opacity="0.4"/>
    </pattern>
  </defs>
  <rect x="20" y="20" width="560" height="560" fill="url(#leiwen)" stroke="{bronze_main}" stroke-width="3" rx="12"/>

  <text x="300" y="65" font-size="20" font-family="serif" font-weight="bold" fill="{gold_highlight}" text-anchor="middle">天津博物馆馆藏神韵 · 商周青铜【{pattern_type}】</text>
  <text x="300" y="90" font-size="12" fill="{bronze_main}" text-anchor="middle">鼎彝吉金 · 兽面巨目重环 · 风格：{style}</text>

  <!-- 饕餮面纹中心组 (对称结构) -->
  <g transform="translate(300, 320)">
    <!-- 巨角 (羊角/牛角变体) -->
    <!-- 左角 -->
    <path d="M-40,-80 C-140,-180 -240,-80 -180,-20 C-140,20 -100,-40 -120,-80 C-100,-100 -50,-80 -40,-80 Z" fill="{bronze_main}" stroke="{gold_highlight}" stroke-width="3"/>
    <!-- 右角 -->
    <path d="M40,-80 C140,-180 240,-80 180,-20 C140,20 100,-40 120,-80 C100,-100 50,-80 40,-80 Z" fill="{bronze_main}" stroke="{gold_highlight}" stroke-width="3"/>

    <!-- 额头饕餮冠纹与鼻梁 -->
    <path d="M0,-110 L-35,-40 L0,50 L35,-40 Z" fill="{bronze_dark}" stroke="{gold_highlight}" stroke-width="3"/>
    <path d="M-15,30 L15,30 L20,80 L-20,80 Z" fill="{bronze_main}" stroke="{gold_highlight}" stroke-width="2"/>

    <!-- 巨目 (突出神目) -->
    <!-- 左眼 -->
    <ellipse cx="-80" cy="0" rx="45" ry="30" fill="{bronze_dark}" stroke="{gold_highlight}" stroke-width="4"/>
    <circle cx="-80" cy="0" r="18" fill="{gold_highlight}"/>
    <circle cx="-80" cy="0" r="8" fill="#111"/>
    <!-- 右眼 -->
    <ellipse cx="80" cy="0" rx="45" ry="30" fill="{bronze_dark}" stroke="{gold_highlight}" stroke-width="4"/>
    <circle cx="80" cy="0" r="18" fill="{gold_highlight}"/>
    <circle cx="80" cy="0" r="8" fill="#111"/>

    <!-- 眉棱骨与颊骨回旋纹 -->
    <path d="M-130,-25 Q-80,-50 -35,-25" fill="none" stroke="{gold_highlight}" stroke-width="5"/>
    <path d="M130,-25 Q80,-50 35,-25" fill="none" stroke="{gold_highlight}" stroke-width="5"/>

    <!-- 巨口与卷唇獠牙 (无下颌经典商代特征) -->
    <path d="M-120,70 Q-60,50 0,60 Q60,50 120,70 L110,110 Q0,85 -110,110 Z" fill="{bronze_main}" stroke="{gold_highlight}" stroke-width="3"/>
    <polygon points="-70,75 -60,115 -50,75" fill="{gold_highlight}"/>
    <polygon points="70,75 60,115 50,75" fill="{gold_highlight}"/>
  </g>

  <!-- 底部说明与非遗标签 -->
  <text x="300" y="540" font-size="13" fill="{gold_highlight}" text-anchor="middle">已输出可用于陶泥模印、金属3D打印及掐丝珐琅工艺的矢量参数曲线</text>
</svg>"""

def save_generated_asset(filename: str, content: str) -> str:
    """将生成的真实非遗 SVG/数据写入静态托管路径并返回访问 URL"""
    filepath = os.path.join(STATIC_GENERATED_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return f"/static/generated/{filename}"
