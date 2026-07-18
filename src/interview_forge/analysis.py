from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass


SKILLS = (
    "Python", "Java", "Go", "JavaScript", "TypeScript", "React", "Vue", "Next.js",
    "FastAPI", "Django", "Flask", "Spring", "MySQL", "PostgreSQL", "MongoDB",
    "Redis", "Docker", "Kubernetes", "Linux", "Git", "RESTful API", "微服务",
    "机器学习", "深度学习", "NLP", "LLM", "大模型", "RAG", "Agent", "LangChain",
    "LangGraph", "向量数据库", "Chroma", "Qdrant", "Milvus", "提示词", "微调",
    "数据分析", "系统设计", "高并发", "消息队列", "单元测试", "CI/CD",
)

STOPWORDS = {
    "and", "the", "with", "for", "from", "that", "this", "are", "you", "your",
    "工作", "岗位", "负责", "相关", "具备", "熟悉", "掌握", "优先", "能够", "要求",
    "经验", "能力", "进行", "以及", "我们", "以上", "良好", "使用", "开发",
}


@dataclass(frozen=True)
class MatchItem:
    requirement: str
    status: str
    evidence: str
    suggestion: str


def extract_requirements(jd_text: str, limit: int = 18) -> list[str]:
    found: list[str] = []
    lower = jd_text.lower()
    for skill in SKILLS:
        if skill.lower() in lower and skill not in found:
            found.append(skill)

    words = re.findall(r"[A-Za-z][A-Za-z0-9.+#/-]{2,}", jd_text)
    counts = Counter(w for w in words if w.lower() not in STOPWORDS)
    for word, _ in counts.most_common(limit):
        if not any(word.lower() == item.lower() for item in found):
            found.append(word)
        if len(found) >= limit:
            break
    return found[:limit]


def build_match_matrix(resume_text: str, jd_text: str) -> list[MatchItem]:
    requirements = extract_requirements(jd_text)
    resume_lower = resume_text.lower()
    items: list[MatchItem] = []
    for requirement in requirements:
        pattern = re.escape(requirement.lower())
        match = re.search(pattern, resume_lower)
        if match:
            evidence = _evidence_line(resume_text, requirement)
            detailed = len(evidence) >= 24 and any(
                marker in evidence.lower()
                for marker in ("实现", "负责", "优化", "提升", "构建", "设计", "%", "项目")
            )
            status = "已覆盖" if detailed else "证据偏弱"
            suggestion = (
                "保留，并补充职责、实现方式和可验证结果。"
                if detailed
                else "不要只罗列关键词，补充在哪个项目中如何使用。"
            )
        else:
            evidence = "—"
            status = "缺失"
            suggestion = "如有真实经历请补充；没有证据时不要写入简历。"
        items.append(MatchItem(requirement, status, evidence, suggestion))
    return items


def match_summary(matrix: list[MatchItem]) -> dict[str, int]:
    total = len(matrix)
    covered = sum(item.status == "已覆盖" for item in matrix)
    weak = sum(item.status == "证据偏弱" for item in matrix)
    missing = sum(item.status == "缺失" for item in matrix)
    score = round((covered + weak * 0.5) / total * 100) if total else 0
    return {"score": score, "covered": covered, "weak": weak, "missing": missing}


def _evidence_line(text: str, term: str) -> str:
    lines = [line.strip(" -•\t") for line in text.splitlines() if line.strip()]
    for line in lines:
        if term.lower() in line.lower():
            return line[:220]
    return term
