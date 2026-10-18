"""Validated lesson content shared by the mobile and teacher workspaces."""
import json
import unicodedata
from typing import Annotated

import httpx
from pydantic import BaseModel, Field, field_validator
from app.models.entities import SysConfig


class CleanModel(BaseModel):
    @field_validator("*", mode="before")
    @classmethod
    def strip_text(cls, value):
        return value.strip() if isinstance(value, str) else value


Text = Annotated[str, Field(min_length=1, max_length=2000)]


class Targets(CleanModel):
    aesthetic: Text
    skill: Text
    emotion: Text


class DifficultPoints(CleanModel):
    key: Text
    difficult: Text


class TeachingStep(CleanModel):
    step: Annotated[str, Field(min_length=1, max_length=160)]
    content: Annotated[str, Field(min_length=1, max_length=4000)]


class LessonContent(CleanModel):
    targets: Targets
    key_difficult_points: DifficultPoints
    teaching_process: list[TeachingStep] = Field(min_length=1, max_length=12)
    teacher_script: Annotated[str, Field(min_length=1, max_length=16000)]
    interactive_questions: list[Text] = Field(min_length=1, max_length=12)
    homework_proposal: Text


def model_configuration(db):
    record = db.query(SysConfig).filter_by(config_key="llm_settings").first()
    try:
        cfg = json.loads(record.config_value) if record and record.config_value else {}
        key = str(cfg.get("api_key", "")).strip()
        if len(key) <= 10 or "*" in key:
            return None
        return {"key": key, "base": str(cfg.get("api_base") or "https://api.deepseek.com/v1").strip().rstrip("/"),
                "model": str(cfg.get("model_name") or "deepseek-chat")[:128],
                "temperature": float(cfg.get("temperature", .7))}
    except (TypeError, ValueError, AttributeError):
        return None


def grade_guidance(grade):
    """Concrete expression and evidence expectations for each supported band."""
    if "小学" in grade or "低段" in grade:
        return {
            "expression": "用两三句话说明自己最喜欢的细节和原因",
            "question": "今天的材料中，你最喜欢哪一个细节？为什么？",
            "homework": "请老师或家长帮助补充一条可查证的资料，并用一句话说说它改变了你哪个想法。",
        }
    if "初中" in grade:
        return {
            "expression": "用一段文字说明自己的设计或聆听依据",
            "question": "比较两份材料，它们在造型、色彩、声音或节奏上的相同和不同是什么？",
            "homework": "补充一条可查证的资料，说明它如何影响你的理解或修改。",
        }
    if "高中" in grade:
        return {
            "expression": "标注所依据的课堂资料，并说明仍待查证的问题",
            "question": "这些形式选择可能与材料、用途或观念有什么关系？哪些说法需要进一步查证？",
            "homework": "补充两条可查证的资料，比较它们的说法，并说明证据如何支持你的判断。",
        }
    if "大学" in grade:
        return {
            "expression": "形成一页观察、分析或设计提案，区分事实、推断与个人判断",
            "question": "从材料、工艺与社会使用的角度，如何解释这种形式选择？现有资料的证据边界在哪里？",
            "homework": "补充两条以上可查证资料，区分事实、推断与价值判断，并提出一个仍待研究的问题。",
        }
    return None


def local_lesson(req):
    topic, grade = req.topic, req.grade
    guidance = grade_guidance(grade)
    focus = "线条、色彩、造型与纹样"
    practice = "完成一张观察记录和一幅手绘设计草图"
    materials = "教师准备的实物、图片或已发布课程资料，以及纸笔"
    if "古琴" in topic or "音乐" in topic:
        focus = "音色、节奏、乐句与聆听感受"
        practice = "完成一张聆听记录，用文字或图形表达一段节奏"
        materials = "教师确认可播放的音频、相关图文资料和聆听记录表；无音频时采用图文鉴赏"
    elif "陶瓷" in topic or "瓷" in topic:
        focus = "器形、装饰位置、纹样与色彩"
        practice = "手绘一种器形，并说明纹样安排和色彩选择"
    elif "脸谱" in topic or "皮影" in topic:
        focus = "人物轮廓、面部特征、色彩与角色表达"
        practice = "绘制角色草图，并说明造型如何表达人物特点"
    elif "绣" in topic:
        focus = "针迹方向、疏密、纹样与色彩"
        practice = "用纸笔设计纹样，并以线条标注拟采用的针迹方向"
    elif "景泰蓝" in topic:
        focus = "掐丝线条、填色分区、色彩与纹样"
        practice = "在纸上设计分区纹样，并说明线条与色彩的关系"
    expression = guidance["expression"] if guidance else "用两三句话解释你的选择"
    questions = [f"在{topic}的课堂材料中，你最关注哪个细节？依据是什么？",
                 "如果改变其中一种线条、色彩、形态或节奏，表达效果会怎样变化？"]
    if guidance:
        questions.append(guidance["question"])
    homework = (f"整理本课关于{topic}的观察记录或草图，" + guidance["homework"]) if guidance else \
        f"整理本课关于{topic}的观察记录或草图，补充一条可查证的资料，并说明它如何影响你的理解或修改。"
    minutes = [max(1, round(req.duration_minutes * ratio)) for ratio in (8/45, 15/45, 12/45)]
    minutes.append(req.duration_minutes-sum(minutes))
    stages = [
        ("观察与提问", f"展示{materials}。围绕{topic}提出一个观察问题，学生先记录自己的发现。"),
        ("比较与理解", f"从{focus}比较两份材料。教师结合已核实的资料补充背景，不把示意图片或模板内容当作实物证据。"),
        ("设计与实践", f"学生{practice}。先说明构思，再独立或合作完成；课堂不安排未准备材料和工具的工艺操作。"),
        ("交流与反思", "展示观察记录或草图，从表达是否清楚、选择是否有依据、修改是否有效三个方面交流，记录一个仍待查证的问题。"),
    ]
    return {
        "targets": {"aesthetic": f"观察{topic}的{focus}，用具体例子表达自己的感受。",
                    "skill": practice + f"，{expression}。",
                    "emotion": req.objectives or "认识传统技艺与生活的联系，形成尊重文化多样性和继续了解相关技艺的意愿。"},
        "key_difficult_points": {"key": f"以{focus}为线索，建立观察、比较和表达的方法。",
                                 "difficult": "区分自己的感受与可查证的知识，把观察所得转化为有依据的设计说明。"},
        "teaching_process": [{"step": f"{i+1}. {title}（{minutes[i]}分钟）", "content": body}
                             for i, (title, body) in enumerate(stages)],
        "teacher_script": (
            f"【导入】\n同学们，今天我们一起了解{topic}。请先观察或聆听老师准备的材料，写下你最先注意到的一个细节。\n\n"
            f"【比较与讨论】\n我们从{focus}进行比较。你发现了哪些相同或不同之处？请指出材料中的具体位置，说明自己的判断依据。"
            "涉及历史、地域和工艺知识时，我们共同查阅课堂资料，暂时不能确认的内容先记录为问题。\n\n"
            f"【实践】\n接下来，请{practice}。先想清楚要表达什么，再选择适合的形式。完成后{expression}。\n\n"
            "【交流与总结】\n请同伴说出作品中表达清楚的一点，再提出一个具体问题。根据反馈修改，并记录今天的新发现和下一次想了解的内容。"
        ),
        "interactive_questions": questions,
        "homework_proposal": homework,
    }


def generate_lesson(req, db, mode="AUTO"):
    cfg = model_configuration(db) if mode != "LOCAL" else None
    attempted = cfg is not None
    content = None
    if cfg:
        prompt = (f"为学段【{req.grade}】、主题【{req.topic}】、时长【{req.duration_minutes}分钟】编写课堂教案。"
                  f"补充目标：{req.objectives or '按学段安排观察、理解和实践活动'}。"
                  "只返回JSON：targets含aesthetic/skill/emotion，key_difficult_points含key/difficult，"
                  "teaching_process为step/content对象数组，teacher_script为完整讲稿字符串，"
                  "interactive_questions为问题字符串数组，homework_proposal为字符串。"
                  "不要编造视频、资源链接、文物藏品或未经核实的史实，不安排未提供材料的危险工艺操作。")
        try:
            with httpx.Client(timeout=15, follow_redirects=False) as client:
                response = client.post(cfg["base"]+"/chat/completions", headers={"Authorization":"Bearer "+cfg["key"]},
                    json={"model":cfg["model"],"temperature":cfg["temperature"],
                          "messages":[{"role":"system","content":"You write complete, age-appropriate lesson plans as JSON."},
                                      {"role":"user","content":prompt}],"response_format":{"type":"json_object"}})
                response.raise_for_status()
                content = LessonContent.model_validate_json(response.json()["choices"][0]["message"]["content"]).model_dump()
        except (httpx.HTTPError, httpx.InvalidURL, ValueError, TypeError, KeyError, IndexError):
            content = None
    source = "已配置模型辅助" if content else ("本地课程模板（模型服务未完成）" if attempted else "本地课程模板")
    content = content or LessonContent.model_validate(local_lesson(req)).model_dump()
    return {"title": req.topic+" · 课堂教案", "grade":req.grade, "topic":req.topic,
            "duration":str(req.duration_minutes)+" 分钟", **content,
            "activity_design":[s["step"] for s in content["teaching_process"]], "generated_by":source,
            "generation_method":"configured_model" if source=="已配置模型辅助" else "local_template",
            "model_fallback":attempted and source!="已配置模型辅助"}


def text_parts(value):
    """Keep readable historical content without assuming a model's old shape."""
    if isinstance(value, dict):
        return [str(v) for v in value.values() if v is not None]
    if isinstance(value, list):
        return [str(v) for v in value if v is not None]
    return [str(value)] if value is not None else []


def text_pages(text, width=72, lines=12):
    """Conservative CJK-aware wrapping for editable slide text, preserving content."""
    wrapped, current, used = [], "", 0
    for char in str(text):
        if char == "\r":
            continue
        if char == "\n":
            wrapped.append(current); current=""; used=0
            continue
        amount=2 if unicodedata.east_asian_width(char) in "WF" else 1
        closing = char in "，。！？；：、）》】」』”’％,.;:!?%)]}"
        # Keep closing punctuation with the preceding CJK line. The renderer
        # reserves more horizontal space than this small hanging allowance.
        if current and used+amount>width and not (closing and used < width+8):
            wrapped.append(current); current=""; used=0
        current+=char; used+=amount
    if current or not wrapped:
        wrapped.append(current)
    return ["\n".join(wrapped[i:i+lines]) for i in range(0,len(wrapped),lines)]
