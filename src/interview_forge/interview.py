from __future__ import annotations

import re
from dataclasses import dataclass

from .analysis import MatchItem


@dataclass(frozen=True)
class Evaluation:
    score: int
    level: str
    feedback: str
    improved_answer: str


def generate_questions(matrix: list[MatchItem], resume_text: str, limit: int = 8) -> list[str]:
    questions: list[str] = []
    for item in matrix:
        if item.status == "已覆盖":
            questions.append(f"请结合一个真实项目，说明你如何使用 {item.requirement} 解决具体问题。")
        elif item.status == "证据偏弱":
            questions.append(f"你的简历提到了 {item.requirement}，请说明你的实际职责、关键实现和结果。")
        else:
            questions.append(f"这个岗位需要 {item.requirement}。请说明你的理解，以及你会如何快速补齐这一能力。")
        if len(questions) >= limit - 2:
            break

    if re.search(r"项目|project", resume_text, re.I):
        questions.append("请选择简历中最有代表性的项目，介绍业务目标、你的职责、技术方案和最终结果。")
    questions.append("如果项目上线后出现性能下降，你会如何定位问题并验证优化效果？")
    return questions[:limit]


def evaluate_answer(question: str, answer: str) -> Evaluation:
    cleaned = answer.strip()
    if not cleaned:
        return Evaluation(0, "红色", "未作答，需要先形成基础答案。", "先给出结论，再说明做法、个人职责和结果。")

    score = 25
    feedback: list[str] = []
    length = len(cleaned)
    if length >= 80:
        score += 20
    elif length >= 35:
        score += 10
    else:
        feedback.append("回答偏短，缺少必要细节")

    if any(x in cleaned for x in ("首先", "其次", "最后", "背景", "任务", "行动", "结果")):
        score += 15
    else:
        feedback.append("建议使用结论或 STAR 结构组织回答")

    if any(x in cleaned for x in ("我负责", "我实现", "我设计", "我的职责", "我优化")):
        score += 15
    else:
        feedback.append("没有清楚说明个人贡献")

    if re.search(r"\d|提升|降低|结果|效果|上线|验证", cleaned):
        score += 15
    else:
        feedback.append("缺少结果或验证方式")

    key_terms = [
        word.lower() for word in re.findall(r"[A-Za-z][A-Za-z0-9.+#/-]{2,}|[\u4e00-\u9fff]{2,6}", question)
        if word not in {"请说明", "如何", "一个", "以及", "这个", "你的"}
    ]
    if any(term in cleaned.lower() for term in key_terms):
        score += 10
    else:
        feedback.append("与问题核心的关联不够直接")

    score = min(score, 100)
    level = "绿色" if score >= 80 else "黄色" if score >= 60 else "红色"
    message = "；".join(feedback) if feedback else "回答结构完整，继续准备更深入的追问。"
    improved = "建议答案结构：一句话结论 → 项目背景 → 你的具体行动 → 技术取舍 → 可验证结果 → 复盘。"
    return Evaluation(score, level, message, improved)


def extract_interview_questions(transcript: str) -> list[str]:
    questions: list[str] = []
    for raw in transcript.splitlines():
        line = raw.strip()
        if not line:
            continue
        line = re.sub(r"^(面试官| interviewer|q|问)\s*[:：]\s*", "", line, flags=re.I)
        if raw.rstrip().endswith(("?", "？")) or raw.startswith(("面试官", "Q", "问：")):
            if len(line) >= 4 and line not in questions:
                questions.append(line)
    if not questions:
        for sentence in re.findall(r"[^。！？!?\n]{4,}[？?]", transcript):
            question = sentence.strip()
            if question not in questions:
                questions.append(question)
    return questions


def extract_qa_pairs(transcript: str) -> list[tuple[str, str]]:
    """Parse a user-correctable, speaker-labelled transcript into Q/A pairs."""
    pairs: list[tuple[str, str]] = []
    current_question = ""
    answer_lines: list[str] = []
    for raw in transcript.splitlines():
        line = raw.strip()
        if not line:
            continue
        interviewer = re.match(r"^(面试官|interviewer|q|问)\s*[:：]\s*(.+)$", line, flags=re.I)
        candidate = re.match(r"^(候选人|求职者|candidate|a|答)\s*[:：]\s*(.*)$", line, flags=re.I)
        if interviewer:
            if current_question:
                pairs.append((current_question, "\n".join(answer_lines).strip()))
            current_question = interviewer.group(2).strip()
            answer_lines = []
        elif candidate and current_question:
            answer_lines.append(candidate.group(2).strip())
        elif current_question and answer_lines:
            answer_lines.append(line)
    if current_question:
        pairs.append((current_question, "\n".join(answer_lines).strip()))
    return [(q, a) for q, a in pairs if q]


def build_review(transcript: str, questions: list[str]) -> str:
    if not transcript.strip():
        return "缺少面试转写，暂时无法生成复盘。"
    if not questions:
        return "已保存转写，但没有可靠识别到问题。请按“面试官：问题？”格式校对后重新分析。"

    topic_text = "、".join(q[:30] for q in questions[:5])
    return (
        f"本次共识别 {len(questions)} 道面试问题，主要涉及：{topic_text}。\n\n"
        "建议逐题补充结论、个人职责、技术取舍和可验证结果；对无法立即回答的问题标记为红色，"
        "表达基本正确但缺少深度的问题标记为黄色，并安排下一轮强化训练。"
    )
