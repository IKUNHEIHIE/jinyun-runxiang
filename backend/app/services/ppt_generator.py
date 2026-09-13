import io
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# 经典津派非遗色系定义
COLOR_PRIMARY = RGBColor(139, 74, 47)    # 津门古铜红 / 熟褐
COLOR_GOLD = RGBColor(196, 134, 58)      # 典雅矿物金
COLOR_TEXT_MAIN = RGBColor(47, 41, 37)   # 深灰墨黑
COLOR_TEXT_MUTED = RGBColor(119, 109, 101) # 典雅中灰
COLOR_BG_CARD = RGBColor(246, 242, 236)  # 宣纸米白色
COLOR_WHITE = RGBColor(255, 255, 255)
COLOR_BORDER = RGBColor(220, 210, 200)

def set_slide_background(slide, prs, color=COLOR_WHITE):
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = color

def add_header(slide, title_text, category_tag="天津非遗乡土美育微课"):
    # 顶部装饰顶栏
    top_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.12))
    top_bar.fill.solid()
    top_bar.fill.fore_color.rgb = COLOR_PRIMARY
    top_bar.line.color.rgb = COLOR_PRIMARY

    # 顶部标签
    tag_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.4))
    tf = tag_box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = f"❖ {category_tag.upper()} · 备课微课配套演示课件"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_GOLD

    # 幻灯片主标题
    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.7), Inches(11.7), Inches(0.7))
    tf_t = title_box.text_frame
    tf_t.word_wrap = True
    p_t = tf_t.paragraphs[0]
    p_t.text = title_text
    p_t.font.size = Pt(24)
    p_t.font.bold = True
    p_t.font.color.rgb = COLOR_PRIMARY

    # 底部分割细线
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.45), Inches(11.733), Inches(0.02))
    line.fill.solid()
    line.fill.fore_color.rgb = COLOR_BORDER
    line.line.color.rgb = COLOR_BORDER

def add_footer(slide):
    footer_box = slide.shapes.add_textbox(Inches(0.8), Inches(7.0), Inches(11.7), Inches(0.35))
    tf = footer_box.text_frame
    p = tf.paragraphs[0]
    p.text = "津脉智韵 · 天津市乡村美育浸润行动协同备课中台 | 天津市教育科学研究院非遗美育专家组联合监制"
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_TEXT_MUTED

def generate_lesson_pptx(
    topic: str,
    grade: str = "小学四年级",
    duration_minutes: int = 45,
    targets: dict = None,
    key_difficult: dict = None,
    teaching_process: list = None,
    teacher_script: str = "",
    interactive_questions: list = None,
    homework_proposal: str = ""
) -> io.BytesIO:
    prs = Presentation()
    # 采用标准 16:9 宽屏分辨率
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_slide_layout = prs.slide_layouts[6]

    # ----------------------------------------------------
    # Slide 1: 课件封面
    # ----------------------------------------------------
    s1 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(s1, prs, COLOR_BG_CARD)

    # 封面边框装饰框
    border_rect = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6), Inches(0.6), Inches(12.133), Inches(6.3))
    border_rect.fill.solid()
    border_rect.fill.fore_color.rgb = COLOR_WHITE
    border_rect.line.color.rgb = COLOR_GOLD
    border_rect.line.width = Pt(2)

    # 顶部徽章
    top_badge = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2), Inches(1.2), Inches(3.8), Inches(0.45))
    top_badge.fill.solid()
    top_badge.fill.fore_color.rgb = COLOR_PRIMARY
    top_badge.line.color.rgb = COLOR_PRIMARY
    p_badge = top_badge.text_frame.paragraphs[0]
    p_badge.text = "❖ 天津市乡村美育浸润行动计划 ❖"
    p_badge.font.size = Pt(11)
    p_badge.font.bold = True
    p_badge.font.color.rgb = COLOR_WHITE
    p_badge.alignment = PP_ALIGN.CENTER

    # 课题主标题
    title_box = s1.shapes.add_textbox(Inches(1.2), Inches(1.9), Inches(10.8), Inches(1.4))
    tf1 = title_box.text_frame
    tf1.word_wrap = True
    p1 = tf1.paragraphs[0]
    p1.text = f"《津门非遗美育：{topic}》"
    p1.font.size = Pt(36)
    p1.font.bold = True
    p1.font.color.rgb = COLOR_PRIMARY

    # 副标题
    p_sub = tf1.add_paragraph()
    p_sub.text = "非物质文化遗产活态传承与具身数字工坊协同育人课件"
    p_sub.font.size = Pt(18)
    p_sub.font.color.rgb = COLOR_GOLD
    p_sub.space_before = Pt(8)

    # 课程元信息卡片
    meta_card = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2), Inches(4.2), Inches(10.8), Inches(1.2))
    meta_card.fill.solid()
    meta_card.fill.fore_color.rgb = COLOR_BG_CARD
    meta_card.line.color.rgb = COLOR_BORDER
    tf_m = meta_card.text_frame
    tf_m.word_wrap = True
    p_m1 = tf_m.paragraphs[0]
    p_m1.text = f"适用学段：{grade}    |    建议课时：{duration_minutes} 分钟    |    课程类型：国家级非遗数字化美育微课"
    p_m1.font.size = Pt(14)
    p_m1.font.bold = True
    p_m1.font.color.rgb = COLOR_TEXT_MAIN
    
    p_m2 = tf_m.add_paragraph()
    p_m2.text = "指导单位：天津市非物质文化遗产保护中心 · 天津美院乡村美育工作站"
    p_m2.font.size = Pt(12)
    p_m2.font.color.rgb = COLOR_TEXT_MUTED
    p_m2.space_before = Pt(6)

    add_footer(s1)

    # ----------------------------------------------------
    # Slide 2: 教学目标 (三维素养育人)
    # ----------------------------------------------------
    s2 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(s2, prs, COLOR_WHITE)
    add_header(s2, "01 / 课程教学目标 (三维素养体系)", topic)

    target_aesthetic = (targets or {}).get("aesthetic", f"感知{topic}的传统造型构图、矿物色彩配比与非遗手工肌理之美。")
    target_skill = (targets or {}).get("skill", f"掌握{topic}的经典制作工序与刀笔表现，结合数字工坊尝试构思创编。")
    target_emotion = (targets or {}).get("emotion", "体悟津沽乡土工匠一丝不苟的精神，厚植知家乡、爱津沽的文化自信。")

    cols_data = [
        ("🎨 审美感知素养", target_aesthetic, COLOR_PRIMARY),
        ("✍️ 艺术表现技艺", target_skill, COLOR_GOLD),
        ("🏮 文化理解与情怀", target_emotion, RGBColor(77, 139, 99))
    ]

    card_width = Inches(3.64)
    card_gap = Inches(0.4)
    start_x = Inches(0.8)

    for i, (col_title, col_content, col_color) in enumerate(cols_data):
        curr_x = start_x + i * (card_width + card_gap)
        c_rect = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, curr_x, Inches(1.8), card_width, Inches(4.8))
        c_rect.fill.solid()
        c_rect.fill.fore_color.rgb = COLOR_BG_CARD
        c_rect.line.color.rgb = col_color
        c_rect.line.width = Pt(1.5)

        # 头部标题块
        h_rect = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, curr_x + Inches(0.2), Inches(2.0), card_width - Inches(0.4), Inches(0.6))
        h_rect.fill.solid()
        h_rect.fill.fore_color.rgb = col_color
        h_rect.line.fill.background()
        p_h = h_rect.text_frame.paragraphs[0]
        p_h.text = col_title
        p_h.font.size = Pt(14)
        p_h.font.bold = True
        p_h.font.color.rgb = COLOR_WHITE
        p_h.alignment = PP_ALIGN.CENTER

        # 内容文本
        t_box = s2.shapes.add_textbox(curr_x + Inches(0.3), Inches(2.8), card_width - Inches(0.6), Inches(3.5))
        tf_c = t_box.text_frame
        tf_c.word_wrap = True
        p_c = tf_c.paragraphs[0]
        p_c.text = col_content
        p_c.font.size = Pt(13)
        p_c.font.color.rgb = COLOR_TEXT_MAIN
        p_c.line_spacing = 1.4

    add_footer(s2)

    # ----------------------------------------------------
    # Slide 3: 教学重难点与学情导向
    # ----------------------------------------------------
    s3 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(s3, prs, COLOR_WHITE)
    add_header(s3, "02 / 教学重难点解析与学情突破", topic)

    kp = (key_difficult or {}).get("key", f"理解{topic}的历史渊源与核心造型特质，熟稔色彩分布规范。")
    dp = (key_difficult or {}).get("difficult", f"在手工实践中拿捏线条的柔韧性与转折力度，生动表达人物神韵。")

    # 教学重点卡片
    kp_box = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(11.733), Inches(2.2))
    kp_box.fill.solid()
    kp_box.fill.fore_color.rgb = COLOR_BG_CARD
    kp_box.line.color.rgb = COLOR_PRIMARY
    kp_box.line.width = Pt(1.5)
    tf_kp = kp_box.text_frame
    tf_kp.word_wrap = True
    p_kph = tf_kp.paragraphs[0]
    p_kph.text = "★ 教学重点 (Key Objectives)"
    p_kph.font.size = Pt(16)
    p_kph.font.bold = True
    p_kph.font.color.rgb = COLOR_PRIMARY
    p_kpc = tf_kp.add_paragraph()
    p_kpc.text = kp
    p_kpc.font.size = Pt(14)
    p_kpc.font.color.rgb = COLOR_TEXT_MAIN
    p_kpc.space_before = Pt(8)
    p_kpc.line_spacing = 1.3

    # 教学难点卡片
    dp_box = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(4.3), Inches(11.733), Inches(2.2))
    dp_box.fill.solid()
    dp_box.fill.fore_color.rgb = COLOR_BG_CARD
    dp_box.line.color.rgb = COLOR_GOLD
    dp_box.line.width = Pt(1.5)
    tf_dp = dp_box.text_frame
    tf_dp.word_wrap = True
    p_dph = tf_dp.paragraphs[0]
    p_dph.text = "▲ 教学难点与化解策略 (Challenges & Pedagogical Solutions)"
    p_dph.font.size = Pt(16)
    p_dph.font.bold = True
    p_dph.font.color.rgb = COLOR_GOLD
    p_dpc = tf_dp.add_paragraph()
    p_dpc.text = dp
    p_dpc.font.size = Pt(14)
    p_dpc.font.color.rgb = COLOR_TEXT_MAIN
    p_dpc.space_before = Pt(8)
    p_dpc.line_spacing = 1.3

    add_footer(s3)

    # ----------------------------------------------------
    # Slide 4: 教学实施过程 (环节设计)
    # ----------------------------------------------------
    s4 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(s4, prs, COLOR_WHITE)
    add_header(s4, "03 / 课堂教学流程与环节推进", topic)

    steps = [
        ("第一环节", "情境导入 · 探寻非遗源流", "以津沽地域风情视频或民谣童谣开篇，唤醒乡村孩子们对本土非遗技艺的生活记忆与好奇心。"),
        ("第二环节", "大师传习 · 核心工艺拆解", "细致讲授选材、构线、着色、雕琢等传统工序，分析经典代表作的构图技巧与意蕴。"),
        ("第三环节", "智能工坊 · 动脑动手实践", "利用数字化工具或非遗材料包亲手操作，尝试创新配色与造型，鼓励个性化美育表达。"),
        ("第四环节", "成果展评 · 互评总结升华", "搭建“小小津门非遗工坊”展评台，学生自评与互评，教师从构图、色彩、情感三维进行评价。")
    ]

    for idx, (step_no, step_title, step_desc) in enumerate(steps):
        s_y = Inches(1.8) + idx * Inches(1.22)
        step_card = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), s_y, Inches(11.733), Inches(1.05))
        step_card.fill.solid()
        step_card.fill.fore_color.rgb = COLOR_BG_CARD
        step_card.line.color.rgb = COLOR_BORDER
        
        # 步骤数字小标
        s_badge = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), s_y + Inches(0.18), Inches(1.2), Inches(0.68))
        s_badge.fill.solid()
        s_badge.fill.fore_color.rgb = COLOR_PRIMARY if idx % 2 == 0 else COLOR_GOLD
        s_badge.line.fill.background()
        p_sb = s_badge.text_frame.paragraphs[0]
        p_sb.text = step_no
        p_sb.font.size = Pt(11)
        p_sb.font.bold = True
        p_sb.font.color.rgb = COLOR_WHITE
        p_sb.alignment = PP_ALIGN.CENTER

        # 步骤文本
        s_text = s4.shapes.add_textbox(Inches(2.4), s_y + Inches(0.1), Inches(9.8), Inches(0.85))
        tf_s = s_text.text_frame
        tf_s.word_wrap = True
        p_st = tf_s.paragraphs[0]
        p_st.text = step_title
        p_st.font.size = Pt(14)
        p_st.font.bold = True
        p_st.font.color.rgb = COLOR_TEXT_MAIN
        p_sd = tf_s.add_paragraph()
        p_sd.text = step_desc
        p_sd.font.size = Pt(11)
        p_sd.font.color.rgb = COLOR_TEXT_MUTED
        p_sd.space_before = Pt(3)

    add_footer(s4)

    # ----------------------------------------------------
    # Slide 5: 课中师生互动提问与研学测验
    # ----------------------------------------------------
    s5 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(s5, prs, COLOR_WHITE)
    add_header(s5, "04 / 课堂师生探究互动与思考题", topic)

    q_list = interactive_questions or [
        f"在欣赏《{topic}》时，你觉得它最吸引你的地方是色彩、造型还是背后的民间故事？",
        f"传统非遗与我们现代乡村生活有哪些融合的可能？你能为家乡设计一件伴手礼吗？"
    ]

    for q_idx, q_item in enumerate(q_list[:2]):
        qy = Inches(1.8) + q_idx * Inches(2.4)
        q_card = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), qy, Inches(11.733), Inches(2.1))
        q_card.fill.solid()
        q_card.fill.fore_color.rgb = COLOR_BG_CARD
        q_card.line.color.rgb = COLOR_PRIMARY if q_idx == 0 else COLOR_GOLD
        q_card.line.width = Pt(1.5)

        tf_q = q_card.text_frame
        tf_q.word_wrap = True
        p_qh = tf_q.paragraphs[0]
        p_qh.text = f"探究问题 {q_idx + 1}："
        p_qh.font.size = Pt(16)
        p_qh.font.bold = True
        p_qh.font.color.rgb = COLOR_PRIMARY if q_idx == 0 else COLOR_GOLD

        p_qc = tf_q.add_paragraph()
        p_qc.text = q_item
        p_qc.font.size = Pt(14)
        p_qc.font.color.rgb = COLOR_TEXT_MAIN
        p_qc.space_before = Pt(8)
        p_qc.line_spacing = 1.3

        p_qt = tf_q.add_paragraph()
        p_qt.text = "【教师引导提示】鼓励学生结合身边生活环境发散思维，注重情感共鸣与动手热情。"
        p_qt.font.size = Pt(11)
        p_qt.font.color.rgb = COLOR_TEXT_MUTED
        p_qt.space_before = Pt(6)

    add_footer(s5)

    # ----------------------------------------------------
    # Slide 6: 课后实践作业与结语
    # ----------------------------------------------------
    s6 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(s6, prs, COLOR_WHITE)
    add_header(s6, "05 / 课后实践任务与乡村美育展望", topic)

    hw = homework_proposal or f"请发挥创意，结合本节课所学技巧，设计制作一幅具有津派特色的【{topic}】手工作品，拍照上传至乡村美育数字广场。"

    hw_card = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(11.733), Inches(2.4))
    hw_card.fill.solid()
    hw_card.fill.fore_color.rgb = COLOR_BG_CARD
    hw_card.line.color.rgb = COLOR_PRIMARY
    hw_card.line.width = Pt(1.5)
    tf_hw = hw_card.text_frame
    tf_hw.word_wrap = True
    p_hh = tf_hw.paragraphs[0]
    p_hh.text = "📝 课后实践与工坊延伸任务 (Creative Practice)"
    p_hh.font.size = Pt(16)
    p_hh.font.bold = True
    p_hh.font.color.rgb = COLOR_PRIMARY
    p_hc = tf_hw.add_paragraph()
    p_hc.text = hw
    p_hc.font.size = Pt(14)
    p_hc.font.color.rgb = COLOR_TEXT_MAIN
    p_hc.space_before = Pt(8)
    p_hc.line_spacing = 1.3

    # 结课致谢标语卡片
    thanks_box = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(4.5), Inches(11.733), Inches(2.0))
    thanks_box.fill.solid()
    thanks_box.fill.fore_color.rgb = COLOR_PRIMARY
    thanks_box.line.fill.background()
    tf_th = thanks_box.text_frame
    tf_th.word_wrap = True
    p_th1 = tf_th.paragraphs[0]
    p_th1.text = "传承津沽文脉 · 赋能乡村美育"
    p_th1.font.size = Pt(22)
    p_th1.font.bold = True
    p_th1.font.color.rgb = COLOR_WHITE
    p_th1.alignment = PP_ALIGN.CENTER
    p_th2 = tf_th.add_paragraph()
    p_th2.text = "感谢天津市各试点小学美育教师的悉心付出，期待乡村孩子绽放更绚烂的乡土艺术梦想！"
    p_th2.font.size = Pt(13)
    p_th2.font.color.rgb = COLOR_GOLD
    p_th2.alignment = PP_ALIGN.CENTER
    p_th2.space_before = Pt(8)

    add_footer(s6)

    # 导出字节流
    output = io.BytesIO()
    prs.save(output)
    output.seek(0)
    return output
