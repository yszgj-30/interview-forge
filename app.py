from __future__ import annotations

import base64
import hashlib
import os
import sys
from io import BytesIO
from pathlib import Path

import streamlit as st
import requests
from streamlit_paste_button import paste_image_button

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))

from interview_forge.agent import InterviewAgent
from interview_forge.analysis import build_match_matrix, match_summary
from interview_forge.documents import extract_image_text, extract_text
from interview_forge.demo import seed_demo
from interview_forge.interview import (
    extract_interview_questions,
)
from interview_forge.llm import LLMConfig
from interview_forge.speech import transcribe
from interview_forge.storage import Storage
from interview_forge.ui import (
    apply_theme,
    callout,
    hero,
    metric_card,
    model_status,
    page_header,
    question_card,
    sidebar_brand,
    workflow,
)


st.set_page_config(page_title="Interview Forge", layout="wide", initial_sidebar_state="auto")
apply_theme()

storage = Storage(os.getenv("INTERVIEW_FORGE_DB", str(ROOT / "data" / "interview_forge.db")))
if os.getenv("INTERVIEW_FORGE_AUTO_DEMO") == "1":
    seed_demo(storage, ROOT / "examples")


@st.cache_data(ttl=15, show_spinner=False)
def local_ollama_models() -> list[str]:
    if os.getenv("INTERVIEW_FORGE_DISABLE_OLLAMA") == "1":
        return []
    try:
        response = requests.get("http://127.0.0.1:11434/api/tags", timeout=2)
        response.raise_for_status()
        return [item["name"] for item in response.json().get("models", []) if item.get("name")]
    except (requests.RequestException, KeyError, TypeError, ValueError):
        return []


def speak_button(text: str) -> None:
    payload = base64.b64encode(text.encode("utf-8")).decode("ascii")
    st.iframe(
        f"""
        <button onclick='speak()' style='height:42px;border:1px solid #d7d0e3;border-radius:8px;padding:0 16px;background:white;color:#4c1d95;font:600 14px Inter,Microsoft YaHei,sans-serif;cursor:pointer;transition:all 180ms ease'>
        播放面试官语音</button>
        <script>
        function speak() {{
          speechSynthesis.cancel();
          const bytes = Uint8Array.from(atob("{payload}"), c => c.charCodeAt(0));
          const u = new SpeechSynthesisUtterance(new TextDecoder().decode(bytes));
          u.lang = 'zh-CN'; u.rate = 0.95; speechSynthesis.speak(u);
        }}
        </script>
        """,
        height=48,
        width="content",
        tab_index=0,
    )


def profiles() -> list[dict]:
    return storage.list_profiles()


def selected_profile() -> dict | None:
    items = profiles()
    if not items:
        return None
    labels = {f"{item['name']} · {item['created_at'][:10]}": item for item in items}
    label = st.sidebar.selectbox("当前岗位档案", list(labels))
    return labels[label]


def screenshot_text_input(
    *,
    paste_label: str,
    text_label: str,
    text_key: str,
    paste_key: str,
    placeholder: str,
) -> str:
    st.caption("已复制截图时，点击下方按钮即可粘贴并在本机识别文字；支持连续粘贴多张。")
    pasted = paste_image_button(
        label=paste_label,
        text_color="#FFFFFF",
        background_color="#6D28D9",
        hover_background_color="#5B21B6",
        key=paste_key,
        errors="raise",
    )
    if pasted.image_data is not None:
        image_buffer = BytesIO()
        pasted.image_data.convert("RGB").save(image_buffer, format="PNG")
        image_bytes = image_buffer.getvalue()
        digest = hashlib.sha256(image_bytes).hexdigest()
        history_key = f"{paste_key}_history"
        processed = st.session_state.setdefault(history_key, [])
        if digest not in processed:
            try:
                with st.spinner("正在本机识别截图文字……"):
                    recognized = extract_image_text(image_bytes)
                current = st.session_state.get(text_key, "").strip()
                st.session_state[text_key] = "\n".join(part for part in (current, recognized) if part)
                processed.append(digest)
                st.session_state[f"{paste_key}_preview"] = image_bytes
                st.success(f"截图识别完成，已追加 {len(recognized)} 个字符，请在下方校对。")
            except (ValueError, RuntimeError) as exc:
                st.error(str(exc))

    preview = st.session_state.get(f"{paste_key}_preview")
    if preview:
        st.image(preview, caption="最近粘贴的截图", width=200)
    return st.text_area(text_label, key=text_key, height=220, placeholder=placeholder)


sidebar_brand()
with st.sidebar.expander("大模型设置（可选）"):
    st.caption("兼容 OpenAI API、Ollama 等 /v1/chat/completions 服务；密钥仅保存在当前会话。")
    llm_base_url = st.text_input("Base URL", value="http://localhost:11434/v1")
    detected_models = local_ollama_models()
    if detected_models:
        custom_model_option = "手动输入其他模型…"
        selected_model = st.selectbox("模型名称", [*detected_models, custom_model_option])
        llm_model = (
            st.text_input("自定义模型名称", placeholder="例如 deepseek-r1:7b")
            if selected_model == custom_model_option
            else selected_model
        )
        st.caption(f"已发现本机 Ollama，共 {len(detected_models)} 个模型。")
    else:
        llm_model = st.text_input("模型名称", placeholder="例如 qwen3:4b 或 deepseek-r1:7b")
    st.caption("可填写未自动列出的本地或远端模型名称；请先确保对应推理服务可访问该模型。")
    llm_api_key = st.text_input("API Key", type="password")
agent = InterviewAgent(LLMConfig(llm_base_url, llm_model, llm_api_key))
model_status(
    f"模型模式：{llm_model}" if agent.llm_enabled else "模型模式：本地规则引擎",
    model_enabled=agent.llm_enabled,
)
if st.sidebar.button("载入脱敏演示数据", use_container_width=True):
    created = seed_demo(storage, ROOT / "examples")
    st.session_state["demo_seed_message"] = "演示数据已载入。" if created else "演示数据已存在。"
    st.rerun()
if demo_message := st.session_state.pop("demo_seed_message", None):
    st.sidebar.success(demo_message)
st.sidebar.caption("一键 Demo 无需 Ollama，不会读取你的个人文件。")
page = st.sidebar.radio(
    "工作区导航",
    ["工作台", "简历与 JD", "语音模拟面试", "正式面试复盘", "面试知识库"],
)
profile = selected_profile()
st.sidebar.divider()
st.sidebar.caption("正式面试录音前，请获得参与者同意并遵守公司规定。")


if page == "工作台":
    hero(
        "INTERVIEW READINESS WORKSPACE",
        "让每一次训练，都转化为下一次面试的确定性",
        "基于真实简历和岗位要求，完成证据分析、语音模拟、薄弱题强化与正式面试复盘。",
    )
    profile_count = storage.count("profiles")
    question_count = storage.count("questions")
    review_count = storage.count("reviews")
    cols = st.columns(3)
    with cols[0]:
        metric_card("岗位档案", profile_count, "已建立的求职目标")
    with cols[1]:
        metric_card("知识库题目", question_count, "累计沉淀的面试问题")
    with cols[2]:
        metric_card("正式复盘", review_count, "已完成的面试复盘")
    st.subheader("推荐训练路径")
    workflow(1 if profile_count == 0 else 3 if question_count == 0 else 4)
    if profile_count == 0:
        callout("建议下一步：进入“简历与 JD”，创建第一个岗位档案。系统会从岗位要求中定位简历证据差距。")
    elif question_count == 0:
        callout("岗位档案已就绪。建议开始一轮语音模拟面试，让 Agent 根据薄弱项生成针对性问题。")
    else:
        callout("训练数据已开始积累。优先到知识库筛选红色和黄色题目，完成强化后再进行下一轮模拟。", "success")
    callout("应用支持本地 Ollama 推理。安装语音扩展后，可使用 faster-whisper 在本机转写录音。")


elif page == "简历与 JD":
    page_header("岗位准备", "简历与岗位匹配", "用岗位要求校验简历证据，只强化真实经历，不制造无法验证的表述。")
    workflow(1)
    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            st.subheader("导入简历")
            st.caption("支持 PDF、DOCX、TXT、Markdown 和图片；也可以粘贴截图或文本。")
            resume_file = st.file_uploader(
                "简历文件", type=["pdf", "docx", "txt", "md", "png", "jpg", "jpeg", "webp"],
            )
            resume_manual = screenshot_text_input(
                paste_label="粘贴简历截图并识别",
                text_label="简历文本",
                text_key="resume_manual",
                paste_key="resume_screenshot",
                placeholder="可粘贴文本，也可使用上方按钮粘贴截图并自动识别。",
            )
    with right:
        with st.container(border=True):
            st.subheader("导入岗位 JD")
            st.caption("支持文件、截图和文本；建议提供完整职责、任职要求与加分项。")
            jd_file = st.file_uploader(
                "JD 文件", type=["pdf", "docx", "txt", "md", "png", "jpg", "jpeg", "webp"],
            )
            jd_manual = screenshot_text_input(
                paste_label="粘贴 JD 截图并识别",
                text_label="岗位描述",
                text_key="jd_manual",
                paste_key="jd_screenshot",
                placeholder="可粘贴文本，也可使用上方按钮粘贴截图并自动识别。",
            )
    name = st.text_input("岗位档案名称", placeholder="例如：Python 后端开发实习生")

    if st.button("分析并保存岗位档案", type="primary", use_container_width=True):
        try:
            resume_text = extract_text(resume_file.name, resume_file.getvalue()) if resume_file else resume_manual.strip()
            jd_text = extract_text(jd_file.name, jd_file.getvalue()) if jd_file else jd_manual.strip()
            if not resume_text or not jd_text or not name.strip():
                st.error("请填写档案名称，并提供简历和 JD。")
            else:
                with st.spinner("正在分析岗位要求和简历证据……"):
                    matrix, guidance = agent.analyze_resume(resume_text, jd_text)
                profile_id = storage.save_profile(name.strip(), resume_text, jd_text)
                st.session_state["latest_matrix"] = matrix
                st.session_state["latest_profile_id"] = profile_id
                st.session_state["resume_guidance"] = guidance
                st.success("岗位档案已保存。")
        except (ValueError, RuntimeError) as exc:
            st.error(str(exc))

    matrix = st.session_state.get("latest_matrix")
    if matrix:
        st.divider()
        st.subheader("岗位证据分析")
        summary = match_summary(matrix)
        cols = st.columns(4)
        cols[0].metric("证据覆盖分", f"{summary['score']}%")
        cols[1].metric("已覆盖", summary["covered"])
        cols[2].metric("证据偏弱", summary["weak"])
        cols[3].metric("缺失", summary["missing"])
        st.dataframe(
            [
                {"岗位要求": item.requirement, "状态": item.status, "简历证据": item.evidence, "修改建议": item.suggestion}
                for item in matrix
            ],
            use_container_width=True,
            hide_index=True,
        )
        callout("“缺失”不等于必须写进简历。没有真实经历时，应制定学习计划，而不是编造内容。", "warning")
        guidance = st.session_state.get("resume_guidance", "")
        if guidance:
            st.subheader("简历优化结果")
            st.text_area("修改稿 / 修改清单", value=guidance, height=320)
            st.download_button(
                "下载优化结果", guidance.encode("utf-8"), "resume_optimization.md", "text/markdown",
            )


elif page == "语音模拟面试":
    page_header("模拟训练", "沉浸式语音模拟面试", "听取面试官提问，用语音或文字作答；系统会评分、追问并自动沉淀薄弱题。")
    workflow(3)
    if not profile:
        callout("当前没有可用的岗位档案。请先在“简历与 JD”中创建档案，再开始针对性模拟。", "warning")
        st.stop()

    matrix = build_match_matrix(profile["resume_text"], profile["jd_text"])
    question_set_key = f"questions_{profile['id']}"
    index_key = f"question_index_{profile['id']}"
    if question_set_key not in st.session_state:
        try:
            generated = agent.make_questions(
                matrix, profile["resume_text"], profile["jd_text"],
            )
            weak_questions = storage.list_weak_questions(profile["id"])
            st.session_state[question_set_key] = list(dict.fromkeys(weak_questions + generated))
        except RuntimeError as exc:
            st.error(str(exc))
            st.stop()
        st.session_state[index_key] = 0

    questions = st.session_state[question_set_key]
    index = st.session_state[index_key]
    if index >= len(questions):
        st.success("本轮模拟面试已完成。请到“面试知识库”查看红黄题并复习。")
        if st.button("重新开始一轮"):
            st.session_state[index_key] = 0
            st.rerun()
        st.stop()

    question = questions[index]
    st.progress(index / len(questions), text=f"第 {index + 1} / {len(questions)} 题")
    question_card(question)
    speak_button(question)
    callout("建议先完整口述，再查看评分。录音默认保存在本地，不会自动上传到第三方服务。")

    with st.container(border=True):
        st.subheader("作答区")
        voice = st.audio_input("语音回答") if hasattr(st, "audio_input") else None
        answer_key = f"mock_answer_{profile['id']}_{index}"
        if voice and st.button("使用本地模型转写本题录音"):
            path = storage.save_audio(voice.getvalue(), ".wav")
            try:
                with st.spinner("正在本地转写……"):
                    st.session_state[answer_key] = transcribe(path)
                st.rerun()
            except RuntimeError as exc:
                st.error(str(exc))

        answer = st.text_area("回答文本", key=answer_key, height=180, placeholder="可直接输入，或先录音再使用本地模型转写。")
    if st.button("提交回答并进入下一题", type="primary", use_container_width=True):
        with st.spinner("面试官正在评价回答……"):
            evaluation = agent.score_answer(question, answer)
        storage.save_question(
            profile["id"], "模拟面试", question, answer, evaluation.score,
            evaluation.level, evaluation.feedback, evaluation.improved_answer,
        )
        if evaluation.score < 80 and len(questions) < 12:
            followup = agent.make_followup(question, answer, evaluation)
            if followup and followup not in questions:
                questions.insert(index + 1, followup)
        st.session_state["last_evaluation"] = evaluation
        st.session_state[index_key] = index + 1
        st.rerun()

    if st.session_state.get("last_evaluation"):
        last = st.session_state["last_evaluation"]
        tone = "success" if last.score >= 80 else "warning"
        callout(f"上一题：{last.score} 分 · {last.level} · {last.feedback}", tone)


elif page == "正式面试复盘":
    page_header("面试复盘", "正式面试录音与会后复盘", "记录真实面试、识别面试问题，并在会后分析回答不足和后续强化方向。")
    workflow(5)
    callout("录音前请获得所有参与者同意。本模式只做记录与会后复盘，不在面试过程中生成答案提示。", "warning")
    consent = st.checkbox("我确认已获得录音所需的同意，并会遵守适用规定和公司政策。")
    with st.container(border=True):
        st.subheader("面试记录")
        title = st.text_input("面试名称", placeholder="例如：某公司 Python 后端一面")
        recorded = st.audio_input("录制现场面试", disabled=not consent) if hasattr(st, "audio_input") else None
        uploaded = st.file_uploader(
            "或上传已有录音", type=["wav", "mp3", "m4a", "ogg", "webm"], disabled=not consent,
        )
    audio = recorded or uploaded

    if audio and st.button("使用本地模型转写录音"):
        suffix = Path(getattr(audio, "name", "recording.wav")).suffix or ".wav"
        audio_path = storage.save_audio(audio.getvalue(), suffix)
        st.session_state["formal_audio_path"] = audio_path
        try:
            with st.spinner("首次使用需要下载语音模型，请稍候……"):
                st.session_state["formal_transcript"] = transcribe(audio_path)
            st.rerun()
        except RuntimeError as exc:
            st.error(str(exc))

    with st.container(border=True):
        st.subheader("转写与校对")
        transcript = st.text_area(
            "面试转写（可校对或直接粘贴）",
            key="formal_transcript",
            height=300,
            placeholder="面试官：请介绍一下你最有代表性的项目？\n候选人：……",
        )
    if st.button("生成复盘并写入知识库", type="primary", use_container_width=True):
        if not consent:
            st.error("请先确认已获得录音和处理许可。")
        elif not title.strip() or not transcript.strip():
            st.error("请填写面试名称和转写内容。")
        else:
            with st.spinner("正在逐题分析正式面试表现……"):
                review = agent.review_formal(transcript)
            profile_id = profile["id"] if profile else None
            storage.save_review(
                profile_id, title.strip(), transcript, review.summary,
                st.session_state.get("formal_audio_path"),
            )
            evaluated_questions: set[str] = set()
            for question, answer, evaluation in review.evaluations:
                evaluated_questions.add(question)
                storage.save_question(
                    profile_id, "正式面试", question, answer, evaluation.score, evaluation.level,
                    evaluation.feedback, evaluation.improved_answer,
                )
            for question in review.questions:
                if question not in evaluated_questions:
                    storage.save_question(
                        profile_id, "正式面试", question, "待补充", 0, "红色",
                        "转写中没有识别到对应回答，请校对说话人并补充答案。",
                        "建议答案结构：结论 → 真实经历 → 技术取舍 → 结果 → 复盘。",
                    )
            st.session_state["formal_review"] = (review.summary, review.questions, review.evaluations)
            st.success("复盘已保存，识别到的正式面试题已进入知识库。")

    if st.session_state.get("formal_review"):
        summary, extracted, evaluations = st.session_state["formal_review"]
        st.subheader("复盘摘要")
        st.write(summary)
        st.subheader("识别到的问题")
        for number, question in enumerate(extracted, 1):
            st.write(f"{number}. {question}")
        if evaluations:
            st.subheader("逐题评价")
            for question, answer, evaluation in evaluations:
                with st.expander(f"[{evaluation.level} · {evaluation.score}分] {question}"):
                    st.write("**回答：**", answer or "未识别到回答")
                    st.write("**不足：**", evaluation.feedback)
                    st.write("**改进：**", evaluation.improved_answer)


elif page == "面试知识库":
    page_header("能力沉淀", "个人面试知识库", "集中复习模拟和正式面试中的问题，优先处理低分题与表达不准确的回答。")
    workflow(4)
    with st.container(border=True):
        filters = st.columns(3)
        query = filters[0].text_input("搜索题目、回答或不足", placeholder="例如：RAG")
        level = filters[1].selectbox("薄弱等级", ["全部", "红色", "黄色", "绿色"])
        source = filters[2].selectbox("题目来源", ["全部", "模拟面试", "正式面试"])
    items = storage.search_questions(
        query,
        None if level == "全部" else level,
        None if source == "全部" else source,
    )
    if not items:
        callout("知识库暂无题目。完成模拟面试或正式面试复盘后，问题与评价会自动写入这里。")
    else:
        totals = st.columns(3)
        red_count = sum(item["level"] == "红色" for item in items)
        yellow_count = sum(item["level"] == "黄色" for item in items)
        with totals[0]:
            metric_card("筛选结果", len(items), "当前符合条件的题目")
        with totals[1]:
            metric_card("红色题", red_count, "建议优先重新作答")
        with totals[2]:
            metric_card("黄色题", yellow_count, "需要补充证据与细节")
        st.dataframe(
            [
                {
                    "来源": item["source"], "等级": item["level"], "分数": item["score"],
                    "问题": item["question"], "不足": item["feedback"], "日期": item["created_at"][:10],
                }
                for item in items
            ],
            use_container_width=True,
            hide_index=True,
        )
        st.subheader("逐题复习")
        for item in items:
            with st.expander(f"[{item['level']}] {item['question']}"):
                st.write("**原回答：**", item["answer"])
                st.write("**不足：**", item["feedback"])
                st.write("**改进框架：**", item["improved_answer"])
