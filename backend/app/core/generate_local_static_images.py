import os

OUTPUT_DIR = "/www/opencode-workspace/shumei/backend/static/images"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def create_svg(filename, bg_gradient, main_color, accent_color, tag, title, subtitle, icon_svg):
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 400" width="100%" height="100%">
  <defs>
    <linearGradient id="grad_{filename}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{bg_gradient[0]}"/>
      <stop offset="100%" stop-color="{bg_gradient[1]}"/>
    </linearGradient>
    <filter id="shadow_{filename}" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="4" stdDeviation="8" flood-opacity="0.25"/>
    </filter>
  </defs>

  <!-- 背景底色与宣纸纹理 -->
  <rect width="600" height="400" fill="url(#grad_{filename})"/>
  <rect x="15" y="15" width="570" height="370" fill="none" stroke="{accent_color}" stroke-width="1.5" stroke-dasharray="8 4" opacity="0.6"/>
  <rect x="22" y="22" width="556" height="356" fill="none" stroke="{accent_color}" stroke-width="0.75" opacity="0.4"/>

  <!-- 四角传统纹样回纹装饰 -->
  <g stroke="{accent_color}" stroke-width="2" fill="none" opacity="0.7">
    <path d="M 28 45 L 28 28 L 45 28 M 34 40 L 34 34 L 40 34"/>
    <path d="M 572 45 L 572 28 L 555 28 M 566 40 L 566 34 L 560 34"/>
    <path d="M 28 355 L 28 372 L 45 372 M 34 360 L 34 366 L 40 366"/>
    <path d="M 572 355 L 572 372 L 555 372 M 566 360 L 566 366 L 560 366"/>
  </g>

  <!-- 艺术图形主体 -->
  <g transform="translate(300, 160)" filter="url(#shadow_{filename})">
    {icon_svg}
  </g>

  <!-- 顶部标签徽章 -->
  <g transform="translate(300, 55)">
    <rect x="-80" y="-14" width="160" height="28" rx="14" fill="{accent_color}" opacity="0.15"/>
    <rect x="-78" y="-12" width="156" height="24" rx="12" fill="none" stroke="{accent_color}" stroke-width="1" opacity="0.6"/>
    <text text-anchor="middle" y="5" fill="{accent_color}" font-size="12" font-family="'Noto Serif SC', 'PingFang SC', serif" font-weight="600" letter-spacing="2">❖ {tag} ❖</text>
  </g>

  <!-- 底部标题与说明 -->
  <text x="300" y="315" text-anchor="middle" fill="#2C241E" font-size="22" font-weight="bold" font-family="'Noto Serif SC', 'SimSun', serif" letter-spacing="1">{title}</text>
  <text x="300" y="345" text-anchor="middle" fill="#786B61" font-size="13" font-family="'Noto Sans SC', sans-serif" letter-spacing="0.5">{subtitle}</text>

  <!-- 右下角朱砂印章 -->
  <g transform="translate(520, 320)">
    <rect x="0" y="0" width="34" height="34" rx="4" fill="#A8382B" opacity="0.9"/>
    <rect x="2" y="2" width="30" height="30" rx="3" fill="none" stroke="#FDE2DE" stroke-width="0.8"/>
    <text x="17" y="15" text-anchor="middle" fill="#FFF" font-size="9" font-family="serif" font-weight="bold">津韵</text>
    <text x="17" y="27" text-anchor="middle" fill="#FFF" font-size="9" font-family="serif" font-weight="bold">润乡</text>
  </g>
</svg>"""
    filepath = os.path.join(OUTPUT_DIR, f"{filename}.svg")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(svg)
    return filepath

# 1. 皮影图形 (生旦净丑人物剪影与挑杆)
shadow_icon = """
<circle cx="0" cy="0" r="70" fill="#8B4A2F" opacity="0.08"/>
<circle cx="0" cy="0" r="55" fill="#8B4A2F" opacity="0.12"/>
<!-- 头冠 -->
<path d="M -15 -45 Q 0 -65 15 -45 Q 25 -30 20 -15 Q 0 -25 -15 -15 Z" fill="#8B4A2F"/>
<!-- 脸谱头翎 -->
<path d="M 0 -60 Q 25 -95 55 -80 Q 30 -65 5 -55 Z" fill="#D6A85C"/>
<!-- 身段与长袍 -->
<path d="M -22 -10 L 22 -10 L 35 45 L -35 45 Z" fill="#A8382B" stroke="#D6A85C" stroke-width="1.5"/>
<!-- 操纵操杆 -->
<line x1="-35" y1="20" x2="-75" y2="70" stroke="#5D4037" stroke-width="2.5" stroke-linecap="round"/>
<line x1="30" y1="25" x2="65" y2="75" stroke="#5D4037" stroke-width="2.5" stroke-linecap="round"/>
<line x1="0" y1="40" x2="0" y2="85" stroke="#5D4037" stroke-width="3" stroke-linecap="round"/>
<!-- 关节铆钉点 -->
<circle cx="-20" cy="-5" r="3" fill="#D6A85C" stroke="#FFF" stroke-width="1"/>
<circle cx="20" cy="-5" r="3" fill="#D6A85C" stroke="#FFF" stroke-width="1"/>
"""

# 2. 年画图形 (娃娃抱鲤鱼与荷花)
painting_icon = """
<circle cx="0" cy="0" r="70" fill="#E65100" opacity="0.08"/>
<!-- 吉祥大鲤鱼 -->
<path d="M -50 15 C -30 -35 30 -35 50 15 C 30 45 -30 45 -50 15 Z" fill="#E65100"/>
<path d="M 50 15 C 65 0 75 -20 85 -5 C 75 15 80 35 60 25 Z" fill="#EF6C00"/>
<circle cx="-35" cy="5" r="5" fill="#FFF"/>
<circle cx="-35" cy="5" r="2.5" fill="#212121"/>
<!-- 鱼鳞套印纹理 -->
<path d="M -20 10 Q -10 5 0 10 Q 10 5 20 10" stroke="#FFD54F" stroke-width="2" fill="none"/>
<path d="M -10 22 Q 0 17 10 22 Q 20 17 30 22" stroke="#FFD54F" stroke-width="2" fill="none"/>
<!-- 莲花荷叶背景 -->
<path d="M -25 -40 Q 0 -60 25 -40 Q 0 -25 -25 -40 Z" fill="#43A047"/>
"""

# 3. 泥人张彩塑 (民俗泥塑兔儿爷)
clay_icon = """
<circle cx="0" cy="0" r="70" fill="#3949AB" opacity="0.08"/>
<!-- 兔子长耳朵 -->
<path d="M -16 -65 C -25 -95 -5 -95 -8 -45 Z" fill="#FFF" stroke="#E53935" stroke-width="2"/>
<path d="M 16 -65 C 25 -95 5 -95 8 -45 Z" fill="#FFF" stroke="#E53935" stroke-width="2"/>
<!-- 泥塑头部与金盔 -->
<circle cx="0" cy="-35" r="24" fill="#FFF" stroke="#D6A85C" stroke-width="2"/>
<path d="M -20 -45 Q 0 -60 20 -45 Z" fill="#D6A85C"/>
<!-- 身披戏服大袍 -->
<path d="M -30 -12 L 30 -12 L 38 48 L -38 48 Z" fill="#C62828"/>
<rect x="-12" y="5" width="24" height="24" fill="#FDD835" rx="2"/>
<text x="0" y="22" text-anchor="middle" font-size="14" fill="#B71C1C" font-weight="bold">吉</text>
"""

# 4. 青铜饕餮纹
bronze_icon = """
<circle cx="0" cy="0" r="70" fill="#00695C" opacity="0.08"/>
<!-- 饕餮巨角 -->
<path d="M -45 -40 C -60 -75 -15 -65 -15 -35" fill="none" stroke="#26A69A" stroke-width="6" stroke-linecap="round"/>
<path d="M 45 -40 C 60 -75 15 -65 15 -35" fill="none" stroke="#26A69A" stroke-width="6" stroke-linecap="round"/>
<!-- 饕餮神目 -->
<ellipse cx="-22" cy="-10" rx="14" ry="10" fill="#004D40" stroke="#80CBC4" stroke-width="3"/>
<circle cx="-22" cy="-10" r="5" fill="#E0F2F1"/>
<ellipse cx="22" cy="-10" rx="14" ry="10" fill="#004D40" stroke="#80CBC4" stroke-width="3"/>
<circle cx="22" cy="-10" r="5" fill="#E0F2F1"/>
<!-- 鼻梁与獠牙 -->
<path d="M 0 -20 L 0 15 M -12 15 L 12 15" stroke="#26A69A" stroke-width="4"/>
<path d="M -18 15 L -25 35 L -10 20 L 0 35 L 10 20 L 25 35 L 18 15" fill="#004D40" stroke="#80CBC4" stroke-width="2"/>
"""

# 5. 风筝魏 (彩绘沙燕风筝)
kite_icon = """
<circle cx="0" cy="0" r="70" fill="#1565C0" opacity="0.08"/>
<!-- 沙燕风筝头部 -->
<circle cx="0" cy="-45" r="15" fill="#212121"/>
<circle cx="-6" cy="-47" r="3" fill="#FFEB3B"/>
<circle cx="6" cy="-47" r="3" fill="#FFEB3B"/>
<!-- 两侧展翅主翼 -->
<path d="M 0 -35 C -45 -55 -85 -25 -80 5 C -50 -5 -15 -10 0 -15 Z" fill="#D32F2F" stroke="#FFC107" stroke-width="1.5"/>
<path d="M 0 -35 C 45 -55 85 -25 80 5 C 50 -5 15 -10 0 -15 Z" fill="#D32F2F" stroke="#FFC107" stroke-width="1.5"/>
<!-- 剪刀燕尾 -->
<path d="M -12 0 L -45 55 L -20 45 L 0 15 L 20 45 L 45 55 L 12 0 Z" fill="#1976D2" stroke="#FFC107" stroke-width="1.5"/>
"""

# 6. 大漆与螺钿
lacquer_icon = """
<circle cx="0" cy="0" r="70" fill="#212121" opacity="0.08"/>
<!-- 漆器底盘 -->
<circle cx="0" cy="0" r="52" fill="#1A1A1A" stroke="#B71C1C" stroke-width="3"/>
<circle cx="0" cy="0" r="44" fill="none" stroke="#D6A85C" stroke-width="1" stroke-dasharray="4 2"/>
<!-- 螺钿折光花鸟 -->
<path d="M -20 10 C -15 -25 15 -25 20 10 C 5 20 -5 20 -20 10 Z" fill="#80DEEA" opacity="0.85"/>
<circle cx="0" cy="-10" r="6" fill="#FFF59D"/>
<path d="M -25 -5 Q 0 -35 25 -5" stroke="#E1BEE7" stroke-width="2" fill="none"/>
"""

# 7. 汉沽版画
woodcut_icon = """
<circle cx="0" cy="0" r="70" fill="#2E7D32" opacity="0.08"/>
<!-- 木版刻痕与海浪盐田 -->
<rect x="-45" y="-45" width="90" height="90" rx="6" fill="#263238" stroke="#ECEFF1" stroke-width="2"/>
<path d="M -45 10 Q -20 -15 0 10 Q 20 35 45 10" stroke="#FFF" stroke-width="3" fill="none"/>
<path d="M -45 25 Q -20 0 0 25 Q 20 50 45 25" stroke="#FFF" stroke-width="2" fill="none"/>
<!-- 渔船与红日 -->
<circle cx="-18" cy="-20" r="10" fill="#E53935"/>
<path d="M 5 -15 L 30 -15 L 20 0 L -5 0 Z" fill="#FFF"/>
<line x1="12" y1="-30" x2="12" y2="-15" stroke="#FFF" stroke-width="2"/>
"""

# 8. 研学地标 (古建飞檐殿堂)
landmark_icon = """
<circle cx="0" cy="0" r="70" fill="#8B4A2F" opacity="0.08"/>
<!-- 殿顶飞檐斗栱 -->
<path d="M -60 -15 Q -40 -40 0 -45 Q 40 -40 60 -15 Q 40 -22 0 -22 Q -40 -22 -60 -15 Z" fill="#B71C1C"/>
<rect x="-42" y="-14" width="84" height="8" fill="#D6A85C"/>
<!-- 立柱与匾额 -->
<rect x="-35" y="-6" width="70" height="48" fill="#FBF7EE" stroke="#8B4A2F" stroke-width="2"/>
<rect x="-16" y="-2" width="32" height="14" fill="#B71C1C" rx="2"/>
<text x="0" y="9" text-anchor="middle" font-size="8" fill="#FFD54F" font-weight="bold">独乐古刹</text>
<!-- 廊柱 -->
<rect x="-30" y="8" width="6" height="34" fill="#8B4A2F"/>
<rect x="24" y="8" width="6" height="34" fill="#8B4A2F"/>
<rect x="-10" y="14" width="20" height="28" fill="#5D4037"/>
"""

# 9. 助农文创产品
product_icon = """
<circle cx="0" cy="0" r="70" fill="#F57F17" opacity="0.08"/>
<!-- 礼盒托盘 -->
<rect x="-45" y="-20" width="90" height="65" rx="6" fill="#FFF8E1" stroke="#D6A85C" stroke-width="2"/>
<!-- 盒盖与丝带结 -->
<rect x="-50" y="-35" width="100" height="18" rx="4" fill="#8B4A2F"/>
<path d="M 0 -45 Q -15 -60 -5 -40 Q 0 -35 0 -35 Q 0 -35 5 -40 Q 15 -60 0 -45" fill="#D6A85C"/>
<line x1="0" y1="-35" x2="0" y2="45" stroke="#D6A85C" stroke-width="3"/>
<!-- 非遗铭牌 -->
<rect x="-24" y="2" width="48" height="22" rx="3" fill="#A8382B"/>
<text x="0" y="17" text-anchor="middle" font-size="10" fill="#FFF" font-weight="bold">非遗文创</text>
"""

# 10. 用户头像
avatar_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100%" height="100%">
  <circle cx="50" cy="50" r="48" fill="#FBF7EE" stroke="#8B4A2F" stroke-width="2"/>
  <circle cx="50" cy="40" r="18" fill="#8B4A2F" opacity="0.85"/>
  <path d="M 22 80 C 22 62 34 58 50 58 C 66 58 78 62 78 80 Z" fill="#8B4A2F" opacity="0.85"/>
  <circle cx="50" cy="40" r="15" fill="#F5EBE1"/>
  <!-- 头顶祥云发簪 -->
  <path d="M 45 22 Q 50 16 55 22" stroke="#D6A85C" stroke-width="2" fill="none"/>
</svg>"""

images_data = [
    # 皮影系列
    ("shadow_puppet_1", ("#FCF8F2", "#F5EFEB"), "#8B4A2F", "#8B4A2F", "国家级非遗 · 津派皮影", "穆桂英智破天门阵 · 皮影女将", "蓟州区下营镇中心小学 · 乡村美育手工坊", shadow_icon),
    ("shadow_puppet_2", ("#FBF5F0", "#F0E7DD"), "#8B4A2F", "#D6A85C", "津门皮影操杆", "白布映光芒 · 孙悟空大闹天宫", "光影艺术语言与多关节联动设计", shadow_icon),
    ("shadow_puppet_3", ("#FDF9F5", "#F7ECE1"), "#A8382B", "#8B4A2F", "非遗皮影道具", "皮影神兽与坐骑 · 工艺拓印", "传统牛皮精雕与矿物颜料着色", shadow_icon),

    # 杨柳青年画系列
    ("yangliuqing_1", ("#FFF8F0", "#FDEBD0"), "#D35400", "#E67E22", "国家级非遗 · 木版年画", "杨柳青抱鱼娃娃 · 年年有余", "明清传统木版套印与手工彩绘点染", painting_icon),
    ("yangliuqing_2", ("#FDF6EE", "#F9E7D2"), "#E65100", "#D6A85C", "岁时吉祥版画", "莲花童子 · 吉庆有余年画挂轴", "乡村学校文创工坊优秀学生作品", painting_icon),
    ("yangliuqing_3", ("#FCF4E8", "#F7E2CA"), "#C0392B", "#E67E22", "传统木版套色", "门神秦琼尉迟恭 · 威震津门", "五套色木版套印技艺解析", painting_icon),

    # 泥人张彩塑系列
    ("clay_figurine_1", ("#F3F5F9", "#E8EDF5"), "#2C3E50", "#34495E", "国家级非遗 · 泥人张", "民俗彩塑 · 指尖上的百态神韵", "纯天然矿物泥塑与津派写实传神造像", clay_icon),
    ("clay_figurine_2", ("#F0F4F8", "#E2EAF2"), "#1A5276", "#2980B9", "津派泥彩塑", "兔子王彩塑 · 中秋拜月中堂", "泥人张世家技法指导研学作品", clay_icon),

    # 青铜饕餮系列
    ("bronze_taotie_1", ("#F0F7F4", "#E1EFEA"), "#117A65", "#16A085", "商周汉代青铜礼乐", "青铜神兽饕餮纹 · 守护图腾", "天津博物馆藏商周青铜器纹样提取", bronze_icon),
    ("bronze_taotie_2", ("#EDF6F2", "#DCECE5"), "#0E6251", "#48C9B0", "古代青铜纹样", "回纹与夔龙纹 · 礼器铸造之美", "乡村美育AI纹样衍生重构", bronze_icon),

    # 风筝魏系列
    ("weiji_kite_1", ("#F4F8FB", "#E5EEF5"), "#2471A3", "#5499C7", "国家级非遗 · 风筝魏", "沙燕金鹰 · 榫卯折叠彩绘风筝", "非遗大师折叠骨架秘籍与凌空翱翔", kite_icon),

    # 古法大漆
    ("lacquer_craft_1", ("#FAF5F5", "#F2E4E4"), "#78281F", "#922B21", "津沽传统髹饰", "古法大漆与螺钿 · 天然器物光华", "益德成古法髹饰与天然大漆工序", lacquer_icon),

    # 汉沽版画
    ("hangu_woodcut_1", ("#F5F7F6", "#E3EAE6"), "#1E8449", "#27AE60", "滨海民间艺术", "汉沽版画 · 泥土与黑白的滨海叙事", "盐滩渔歌与乡村质朴生活刻痕", woodcut_icon),

    # 研学地标系列
    ("landmark_duleyi", ("#FAF7F2", "#F0E8DC"), "#8B4A2F", "#D6A85C", "蓟州古建名胜", "独乐寺 · 辽代木构榫卯奇观", "千年古刹观音阁 · 研学第一营地", landmark_icon),
    ("landmark_tianjin_museum", ("#F2F6F8", "#E2ECF0"), "#2E4053", "#5D6D7E", "国家一级博物馆", "天津博物馆 · 文华津沽华章", "探寻青铜饕餮与津门近现代文明", landmark_icon),
    ("landmark_yangliuqing", ("#FFF8F0", "#FDECD2"), "#D35400", "#F39C12", "运河文化名镇", "杨柳青古镇 · 年画世家传习所", "大运河畔的水乡年画研学营地", landmark_icon),
    ("landmark_guangdong_guild", ("#FBF5F2", "#F4E5DC"), "#A93226", "#CB4335", "历史风貌建筑", "广东会馆戏楼 · 津门皮影剧场", "全木质古典戏楼与非遗展演现场", landmark_icon),

    # 助农产品
    ("product_diy_kit", ("#FFFDF5", "#FCF3CF"), "#B7950B", "#D4AC0D", "助农文创公益套装", "杨柳青木版年画 DIY 亲子拓印套装", "内含传统雕版/特制宣纸/矿物墨汁", product_icon),
    ("product_clay_rabbit", ("#FDF6F0", "#FADBD8"), "#C0392B", "#E74C3C", "非遗工坊纯手作", "泥人张彩塑 · 吉祥兔儿爷非遗摆件", "老艺人手工彩绘制作 · 收益定向捐助", product_icon)
]

for item in images_data:
    fn, bg, mc, ac, tag, title, sub, icon = item
    create_svg(fn, bg, mc, ac, tag, title, sub, icon)

with open(os.path.join(OUTPUT_DIR, "default_avatar.svg"), "w", encoding="utf-8") as f:
    f.write(avatar_svg)

print(f"Successfully generated {len(images_data) + 1} authentic Tianjin non-heritage local SVGs in {OUTPUT_DIR}")
