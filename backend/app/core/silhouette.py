"""Procedural paper-cut silhouette portraits for the shadow-puppet workshop.

The output is a deterministic SVG composed from a profile bust, headwear and
hand props. Keywords in the user's brief pick the closest archetype; explicit
choices from the client take precedence.
"""
from html import escape

ROLE_LABELS = {"生": "生角书生", "旦": "旦角佳人", "净": "净角武将", "丑": "丑角笑生"}
HEAD_LABELS = {"crown": "凤冠", "bun": "云髻", "floral": "花冠", "feather": "翎羽", "scarf": "方巾"}
PROP_LABELS = {"fan": "团扇", "folding_fan": "折扇", "sword": "长剑", "umbrella": "油纸伞", "branch": "花枝"}
POEMS = {
    "生": "青衫侧影 · 一卷书香",
    "旦": "云鬓花颜 · 半掩春风",
    "净": "铁面丹心 · 气贯长虹",
    "丑": "眉间一点 · 笑看人间",
}


def infer(prompt: str, role=None, headwear=None, prop=None):
    text = prompt or ""
    if not role:
        if any(word in text for word in ("女", "旦", "妃", "娘", "仕女", "佳人")):
            role = "旦"
        elif any(word in text for word in ("武将", "将军", "净", "花脸", "英雄", "侠")):
            role = "净"
        elif any(word in text for word in ("丑", "喜剧", "笑")):
            role = "丑"
        else:
            role = "生"
    if not headwear:
        if any(word in text for word in ("凤冠", "冠", "后", "贵妃")):
            headwear = "crown"
        elif any(word in text for word in ("花", "簪", "海棠", "梅")):
            headwear = "floral"
        elif any(word in text for word in ("翎", "羽", "将")):
            headwear = "feather"
        elif any(word in text for word in ("巾", "书生", "儒")):
            headwear = "scarf"
        else:
            headwear = "bun" if role == "旦" else "scarf" if role == "生" else "feather"
    if not prop:
        if any(word in text for word in ("剑", "刀", "侠", "武")):
            prop = "sword"
        elif any(word in text for word in ("伞", "雨")):
            prop = "umbrella"
        elif any(word in text for word in ("折扇", "扇骨")):
            prop = "folding_fan"
        elif any(word in text for word in ("花", "枝", "梅", "海棠")):
            prop = "branch"
        else:
            prop = "fan"
    return role, headwear, prop


def _head():
    """Delicate right-facing profile, drawn inside a 600x800 canvas."""
    return """
    <path d="M272,400 C266,378 262,348 266,314 C270,276 288,246 318,236
             C346,227 370,244 378,270 C382,284 380,296 378,306
             C376,314 373,321 369,326 C375,332 382,338 380,344
             C378,349 370,349 366,351 C370,356 370,361 364,363
             C367,368 365,373 358,374 C360,382 354,390 346,392
             C336,400 324,402 316,400 L314,430 L270,430
             C268,418 271,409 272,400 Z" />
    <path d="M330,304 C336,300 344,300 350,305 C344,309 336,309 330,304 Z" fill="black" />
    <path d="M331,288 C338,284 347,284 353,288" fill="none" stroke="black" stroke-width="3" />
    <path d="M330,246 C314,252 300,266 296,286 C310,274 326,266 344,262 Z" fill="black" />
    <path d="M348,342 C352,340 356,341 356,344" fill="none" stroke="black" stroke-width="2.4" />
    """


def _hair_bun():
    return """
    <ellipse cx="268" cy="272" rx="25" ry="22" />
    <ellipse cx="286" cy="244" rx="21" ry="15" transform="rotate(-22 286 244)" />
    <path d="M284,252 C274,262 269,276 271,292" fill="none" stroke="black" stroke-width="3" />
    <path d="M250,254 C232,238 214,230 198,232" fill="none" stroke="white" stroke-width="4" />
    """


def _headwear(kind):
    if kind == "crown":
        return """
        <path d="M292,242 C300,222 314,210 332,208 C350,206 364,216 370,232
                 L362,242 C352,230 338,224 324,226 C312,228 302,234 296,244 Z" />
        <path d="M304,220 C290,200 274,190 256,190 C272,202 280,216 284,232 Z" />
        <circle cx="316" cy="216" r="5" /><circle cx="334" cy="208" r="5" />
        <circle cx="352" cy="216" r="4.5" /><circle cx="343" cy="226" r="3.4" />
        <path d="M310,238 C298,226 282,220 266,222" fill="none" stroke="black" stroke-width="3" />
        """
    if kind == "floral":
        clusters = []
        for cx, cy, r in ((306, 232, 8), (326, 222, 9), (346, 226, 8), (360, 238, 6.5)):
            for angle in range(0, 360, 72):
                clusters.append(
                    f'<ellipse cx="{cx}" cy="{cy}" rx="{r}" ry="{r * 0.5}" '
                    f'transform="rotate({angle} {cx} {cy})" />'
                )
            clusters.append(f'<circle cx="{cx}" cy="{cy}" r="2.2" fill="black" />')
        clusters.append('<path d="M302,244 C314,238 330,236 344,240" fill="none" stroke="black" stroke-width="2.6" />')
        return "".join(clusters)
    if kind == "feather":
        return """
        <path d="M324,228 C298,184 262,142 214,112" fill="none" stroke="white" stroke-width="7" />
        <path d="M334,224 C310,178 282,136 244,102" fill="none" stroke="white" stroke-width="6" />
        <path d="M350,228 C350,192 362,158 384,132" fill="none" stroke="white" stroke-width="5" />
        <path d="M300,234 C292,224 280,218 266,218" fill="none" stroke="black" stroke-width="3" />
        """
    if kind == "scarf":
        return """
        <path d="M286,238 C286,214 300,198 320,194 C342,190 360,204 366,224
                 L358,244 C350,228 336,220 320,222 C306,224 294,230 288,244 Z" />
        <path d="M300,200 C316,192 336,194 350,204" fill="none" stroke="black" stroke-width="2.6" />
        <path d="M292,236 C278,248 270,266 268,286" fill="none" stroke="black" stroke-width="3" />
        """
    return _hair_bun()


def _prop(kind):
    # Props are painted after the paper-cut mask: ink shapes with a paper-coloured
    # outline so they separate cleanly from the robe wherever they overlap.
    INK = "#17120d"
    PAPER = "#f7efe0"
    if kind == "fan":
        return f"""
        <g>
          <circle cx="448" cy="520" r="44" fill="{INK}" stroke="{PAPER}" stroke-width="8" />
          <path d="M444,564 L426,636" fill="none" stroke="{PAPER}" stroke-width="16" stroke-linecap="round" />
          <path d="M444,564 L426,636" fill="none" stroke="{INK}" stroke-width="8" stroke-linecap="round" />
          <g stroke="{PAPER}" stroke-width="3.4" fill="none">
            <circle cx="448" cy="520" r="31" />
            <path d="M448,489 L448,551 M417,520 L479,520 M426,498 L470,542 M470,498 L426,542" />
          </g>
        </g>
        """
    if kind == "folding_fan":
        return f"""
        <g>
          <path d="M420,610 L458,486 A124,124 0 0 1 512,522 Z" fill="{INK}" stroke="{PAPER}" stroke-width="8" stroke-linejoin="round" />
          <g stroke="{PAPER}" stroke-width="3.2" fill="none">
            <path d="M428,592 L470,500 M440,600 L486,512 M452,606 L500,522" />
          </g>
        </g>
        """
    if kind == "sword":
        return f"""
        <g>
          <path d="M434,614 L496,428 L508,434 L466,620 Z" fill="{INK}" stroke="{PAPER}" stroke-width="7" stroke-linejoin="round" />
          <path d="M412,592 L470,606 L467,618 L409,604 Z" fill="{INK}" stroke="{PAPER}" stroke-width="7" stroke-linejoin="round" />
          <path d="M424,620 L440,606" fill="none" stroke="{PAPER}" stroke-width="17" stroke-linecap="round" />
          <path d="M424,620 L440,606" fill="none" stroke="{INK}" stroke-width="9" stroke-linecap="round" />
          <path d="M442,606 L498,440" stroke="{PAPER}" stroke-width="2.4" />
        </g>
        """
    if kind == "umbrella":
        return f"""
        <g>
          <path d="M374,492 C394,424 494,424 518,492 C492,480 466,476 446,484
                   C426,492 398,498 374,492 Z" fill="{INK}" stroke="{PAPER}" stroke-width="8" stroke-linejoin="round" />
          <path d="M446,492 L446,654" fill="none" stroke="{PAPER}" stroke-width="17" stroke-linecap="round" />
          <path d="M446,492 L446,654" fill="none" stroke="{INK}" stroke-width="9" stroke-linecap="round" />
          <g stroke="{PAPER}" stroke-width="3" fill="none">
            <path d="M446,452 L446,490 M410,466 L424,490 M482,466 L468,490" />
          </g>
        </g>
        """
    return f"""
    <g>
      <path d="M432,648 C450,582 474,512 510,446" fill="none" stroke="{PAPER}" stroke-width="18" stroke-linecap="round" />
      <path d="M432,648 C450,582 474,512 510,446" fill="none" stroke="{INK}" stroke-width="9" stroke-linecap="round" />
      <g fill="{INK}" stroke="{PAPER}" stroke-width="5">
        <circle cx="488" cy="490" r="11" /><circle cx="508" cy="458" r="9" />
        <circle cx="466" cy="532" r="9" /><circle cx="506" cy="530" r="8" />
        <circle cx="478" cy="566" r="7" />
      </g>
      <g fill="{PAPER}">
        <circle cx="488" cy="490" r="3" /><circle cx="508" cy="458" r="2.6" />
        <circle cx="466" cy="532" r="2.6" /><circle cx="506" cy="530" r="2.4" />
      </g>
    </g>
    """


def _body():
    return """
    <path d="M276,418 C254,430 228,442 210,464 C190,488 182,520 180,556
             L174,692 C246,706 372,706 444,692 L438,556 C436,520 428,488 408,464
             C390,442 360,430 338,418 C332,438 322,448 306,448 C292,448 280,438 276,418 Z" />
    <path d="M398,478 C426,486 446,508 452,536 L444,578 C426,554 410,524 400,500 Z" />
    <path d="M286,424 C300,440 314,446 326,446 C336,446 348,440 356,428"
          fill="none" stroke="black" stroke-width="6" />
    <path d="M398,482 C420,496 434,518 440,544" fill="none" stroke="black" stroke-width="3.4" />
    <path d="M232,520 C252,540 272,552 292,556" fill="none" stroke="black" stroke-width="3" />
    <path d="M356,520 C376,540 394,552 412,558" fill="none" stroke="black" stroke-width="3" />
    """


CUTOUTS = """
<g fill="black">
  <circle cx="238" cy="566" r="8" /><circle cx="286" cy="612" r="7" />
  <circle cx="334" cy="574" r="8.5" /><circle cx="388" cy="618" r="6" />
  <path d="M262,650 C270,640 284,640 292,650 C284,660 270,660 262,650 Z" />
  <path d="M340,648 C348,638 362,638 370,648 C362,658 348,658 340,648 Z" />
  <path d="M206,622 L218,610 L230,622 L218,634 Z" />
  <path d="M300,522 C306,514 318,514 324,522 C318,530 306,530 300,522 Z" />
  <path d="M218,600 C230,584 250,584 262,596" fill="none" stroke="black" stroke-width="3" />
  <path d="M360,596 C372,584 390,586 400,600" fill="none" stroke="black" stroke-width="3" />
</g>
"""


def _accessory(kind):
    if kind == "crown":
        return ('<path d="M298,238 C308,216 326,204 346,208 C356,210 364,218 368,228" />'
                '<circle cx="316" cy="214" r="2.6" fill="#c9a84c" stroke="none" />'
                '<circle cx="334" cy="206" r="2.8" fill="#c9a84c" stroke="none" />'
                '<circle cx="353" cy="214" r="2.4" fill="#c9a84c" stroke="none" />')
    if kind == "floral":
        return ('<circle cx="306" cy="232" r="2.2" fill="#c9a84c" stroke="none" />'
                '<circle cx="326" cy="222" r="2.4" fill="#c9a84c" stroke="none" />'
                '<circle cx="346" cy="226" r="2.2" fill="#c9a84c" stroke="none" />'
                '<circle cx="360" cy="238" r="2" fill="#c9a84c" stroke="none" />')
    if kind == "feather":
        return ('<path d="M324,228 C298,184 262,142 214,112" />'
                '<path d="M334,224 C310,178 282,136 244,102" />'
                '<path d="M350,228 C350,192 362,158 384,132" />')
    if kind == "scarf":
        return '<path d="M290,236 C300,212 318,202 338,204 C352,206 362,216 366,228" />'
    return ('<path d="M252,252 C232,236 212,228 196,230" />'
            '<circle cx="196" cy="230" r="2.6" fill="#c9a84c" stroke="none" />')


def generate_silhouette_svg(prompt: str, role=None, headwear=None, prop=None) -> dict:
    role, headwear, prop = infer(prompt or "", role, headwear, prop)
    title = f"{HEAD_LABELS[headwear]}{PROP_LABELS[prop]} · {role}角剪影"
    poem = POEMS.get(role, POEMS["生"])

    mask_parts = _body() + _head() + _headwear(headwear)
    accessory = _accessory(headwear)
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 800" width="600" height="800">
  <defs>
    <pattern id="grain" width="22" height="22" patternUnits="userSpaceOnUse">
      <circle cx="3" cy="4" r="0.7" fill="#7a5c2c" opacity="0.10"/>
      <circle cx="15" cy="16" r="0.5" fill="#7a5c2c" opacity="0.07"/>
    </pattern>
    <mask id="paperCut">
      <rect width="600" height="800" fill="black"/>
      <g fill="white">{mask_parts}</g>
      {CUTOUTS}
    </mask>
  </defs>
  <rect width="600" height="800" fill="#f7efe0"/>
  <rect width="600" height="800" fill="url(#grain)"/>
  <circle cx="306" cy="430" r="212" fill="#f1e5cf" opacity="0.72"/>
  <circle cx="306" cy="430" r="212" fill="none" stroke="#c9a84c" stroke-width="1.2" opacity="0.38"/>
  <rect x="24" y="24" width="552" height="752" fill="none" stroke="#c9a84c" stroke-width="1.4"/>
  <rect x="32" y="32" width="536" height="736" fill="none" stroke="#c9a84c" stroke-width="0.6" opacity="0.7"/>

  <text x="52" y="74" font-size="11" letter-spacing="4.2" fill="#8a6a37">津门剪影 · PAPER SILHOUETTE</text>
  <text x="52" y="120" font-size="31" font-family="serif" font-weight="700" letter-spacing="3" fill="#1a365d">{escape(title)}</text>
  <line x1="52" y1="141" x2="548" y2="141" stroke="#c9a84c" stroke-width="0.8" opacity="0.6"/>

  <rect x="112" y="180" width="428" height="528" fill="#17120d" mask="url(#paperCut)"/>
  {_prop(prop)}

  <g fill="none" stroke="#c9a84c" stroke-width="1.8">
    {accessory}
  </g>
  <circle cx="318" cy="342" r="2.4" fill="#c9a84c"/>

  <g fill="#8b1a1a">
    <rect x="486" y="646" width="46" height="58" rx="3"/>
    <text x="509" y="669" font-size="15" fill="#f7efe0" font-family="serif" text-anchor="middle">剪</text>
    <text x="509" y="690" font-size="15" fill="#f7efe0" font-family="serif" text-anchor="middle">影</text>
  </g>
  <text x="52" y="712" font-size="12" letter-spacing="2.4" fill="#6b5634">{escape(poem)}</text>
  <text x="52" y="742" font-size="9" letter-spacing="1.6" fill="#9a8a70">PAPER CUT · 津韵润乡 · {escape(ROLE_LABELS[role])} / {escape(HEAD_LABELS[headwear])} / {escape(PROP_LABELS[prop])}</text>
</svg>"""
    return {
        "svg": svg,
        "title": title,
        "poem": poem,
        "params": {"role": role, "headwear": headwear, "prop": prop},
    }
