from pathlib import Path
from types import SimpleNamespace

from interview_forge.analysis import build_match_matrix, match_summary
from interview_forge.agent import InterviewAgent
from interview_forge.documents import _ocr_text_lines
from interview_forge.interview import evaluate_answer, extract_interview_questions, extract_qa_pairs
from interview_forge.storage import Storage


def test_match_matrix_marks_real_evidence():
    resume = "项目经历\n我负责使用 FastAPI 构建接口，并通过缓存优化响应时间。"
    jd = "要求熟悉 Python、FastAPI、Docker。"
    matrix = build_match_matrix(resume, jd)
    statuses = {item.requirement: item.status for item in matrix}
    assert statuses["FastAPI"] == "已覆盖"
    assert statuses["Docker"] == "缺失"
    assert match_summary(matrix)["score"] < 100


def test_answer_evaluation_and_question_extraction():
    result = evaluate_answer(
        "请介绍项目",
        "首先介绍背景。我负责设计接口，其次完成缓存优化，最后验证响应时间降低了 30%。",
    )
    assert result.score >= 80
    assert result.level == "绿色"
    transcript = "面试官：请介绍你的项目？\n候选人：这是一个 RAG 项目。\nQ: 如何处理召回失败?"
    assert len(extract_interview_questions(transcript)) == 2
    assert extract_interview_questions("你好，请介绍你最有挑战的项目？我主要负责接口开发。") == ["你好，请介绍你最有挑战的项目？"]
    pairs = extract_qa_pairs(transcript)
    assert pairs[0] == ("请介绍你的项目？", "这是一个 RAG 项目。")


def test_local_agent_builds_formal_review():
    transcript = "面试官：你如何优化接口？\n候选人：我负责加入缓存，最后验证耗时降低了 30%。"
    review = InterviewAgent().review_formal(transcript)
    assert len(review.evaluations) == 1
    assert "逐题平均分" in review.summary


def test_storage_roundtrip(tmp_path: Path):
    storage = Storage(tmp_path / "test.db")
    profile_id = storage.save_profile("Python 后端", "resume", "jd")
    storage.save_question(profile_id, "模拟面试", "问题", "回答", 50, "红色", "不足", "建议")
    assert storage.count("profiles") == 1
    assert storage.list_questions("红色")[0]["question"] == "问题"
    assert storage.list_weak_questions(profile_id) == ["问题"]


def test_ocr_output_normalization():
    assert _ocr_text_lines(SimpleNamespace(txts=(" 简历 ", "Python / FastAPI", ""))) == [
        "简历",
        "Python / FastAPI",
    ]
    legacy = ([([0, 0], "岗位要求", 0.99), ([1, 1], "Docker", 0.95)], {})
    assert _ocr_text_lines(legacy) == ["岗位要求", "Docker"]
