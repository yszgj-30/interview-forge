from __future__ import annotations

from pathlib import Path

from .storage import Storage


DEMO_PROFILE_NAME = "AI 应用开发实习生（脱敏演示）"


def seed_demo(storage: Storage, examples_dir: str | Path) -> bool:
    """Load an idempotent, fully fictional portfolio demo into local storage."""
    if any(profile["name"] == DEMO_PROFILE_NAME for profile in storage.list_profiles()):
        return False

    root = Path(examples_dir)
    resume = (root / "sample_resume.md").read_text(encoding="utf-8")
    jd = (root / "sample_jd.md").read_text(encoding="utf-8")
    transcript = (root / "sample_transcript.txt").read_text(encoding="utf-8")
    profile_id = storage.save_profile(DEMO_PROFILE_NAME, resume, jd)

    storage.save_question(
        profile_id,
        "模拟面试",
        "请说明你在 RAG 项目中如何降低无依据回答。",
        "我负责检索链路和引用校验，通过相似度阈值、无结果回退与回答引用约束减少无依据输出。",
        82,
        "绿色",
        "结构清楚，仍可补充离线评测集的构建方法。",
        "补充评测集规模、命中率指标和一次失败案例复盘。",
    )
    storage.save_question(
        profile_id,
        "模拟面试",
        "如何验证接口缓存优化确实有效？",
        "使用压测对比优化前后的平均响应时间。",
        68,
        "黄色",
        "说明了对比思路，但缺少压测条件、P95 延迟和缓存一致性处理。",
        "按压测环境、基线指标、优化动作、P95 结果和一致性风险组织回答。",
    )
    summary = (
        "本次演示复盘识别到 2 道问题。项目架构表达清楚；性能验证题需要补充压测条件、"
        "P95 指标和缓存一致性取舍。下一轮优先练习可观测性与故障定位。"
    )
    storage.save_review(profile_id, "脱敏演示 · AI 应用一面", transcript, summary, None)
    storage.save_question(
        profile_id,
        "正式面试",
        "如果检索不到相关文档，你会如何处理？",
        "返回未找到可靠依据，并记录查询用于补充知识库。",
        85,
        "绿色",
        "明确拒绝无依据生成，并形成了数据闭环。",
        "继续补充阈值选择、日志字段和人工复核入口。",
    )
    return True
