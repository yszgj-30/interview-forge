from __future__ import annotations

from html import escape

import streamlit as st


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --if-primary: #6D28D9;
            --if-primary-hover: #5B21B6;
            --if-secondary: #4F46E5;
            --if-accent: #DB2777;
            --if-bg: #F8F7FC;
            --if-surface: #FFFFFF;
            --if-surface-muted: #F5F3FF;
            --if-text: #111827;
            --if-text-muted: #5B6474;
            --if-border: #E5E1EF;
            --if-success: #047857;
            --if-warning: #B45309;
            --if-danger: #B91C1C;
            --if-radius-sm: 8px;
            --if-radius-md: 12px;
            --if-radius-lg: 16px;
            --if-shadow-sm: 0 1px 2px rgba(17, 24, 39, .04);
            --if-shadow-md: 0 8px 24px rgba(76, 29, 149, .07);
        }

        html, body, [class*="css"] {
            font-family: Inter, "Microsoft YaHei", "PingFang SC", system-ui, sans-serif;
            color: var(--if-text);
        }

        .stApp { background: var(--if-bg); }
        .block-container { max-width: 1200px; padding: 2rem 2rem 4rem; }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stToolbar"] { right: 1rem; }

        h1, h2, h3 { color: var(--if-text); letter-spacing: -.02em; }
        h1 { font-size: clamp(1.75rem, 3vw, 2.35rem) !important; line-height: 1.18 !important; }
        h2 { font-size: 1.35rem !important; }
        h3 { font-size: 1.05rem !important; }
        p, label, .stCaption { line-height: 1.6; }

        [data-testid="stSidebar"] {
            background: #171229;
            border-right: 1px solid rgba(255,255,255,.08);
        }
        [data-testid="stSidebar"] * { color: #F7F4FF; }
        [data-testid="stSidebar"] .stCaption,
        [data-testid="stSidebar"] small { color: #BDB5D1 !important; }
        [data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.12); }
        [data-testid="stSidebar"] [data-baseweb="select"] > div,
        [data-testid="stSidebar"] input {
            background: #251D3A !important;
            border-color: #4B3E67 !important;
            color: #FFFFFF !important;
        }
        [data-testid="stSidebar"] [data-testid="stExpander"] {
            background: rgba(255,255,255,.04);
            border-color: rgba(255,255,255,.1);
            border-radius: var(--if-radius-md);
        }
        [data-testid="stSidebar"] .stButton > button {
            background: var(--if-primary); border-color: var(--if-primary); color: #FFFFFF !important;
        }
        [data-testid="stSidebar"] .stButton > button:hover {
            background: var(--if-primary-hover); border-color: var(--if-primary-hover); color: #FFFFFF !important;
        }
        [data-testid="stSidebar"] [role="radiogroup"] label {
            min-height: 44px;
            padding: .5rem .65rem;
            border-radius: 8px;
            transition: background-color 180ms ease;
        }
        [data-testid="stSidebar"] [role="radiogroup"] label:hover {
            background: rgba(255,255,255,.07);
        }

        .if-brand { display: flex; align-items: center; gap: 12px; margin: 4px 0 20px; }
        .if-brand-mark {
            display: grid; place-items: center; width: 38px; height: 38px;
            border-radius: 10px; background: var(--if-primary); color: white;
            font-weight: 800; font-size: 14px; letter-spacing: -.04em;
            box-shadow: 0 8px 20px rgba(109,40,217,.32);
        }
        .if-brand-name { color: white; font-size: 1.02rem; font-weight: 750; line-height: 1.2; }
        .if-brand-note { color: #BDB5D1; font-size: .76rem; margin-top: 2px; }
        .if-status {
            margin: 12px 0 4px; padding: 10px 12px; border-radius: 10px;
            background: rgba(16,185,129,.10); border: 1px solid rgba(52,211,153,.22);
            color: #D1FAE5 !important; font-size: .78rem; line-height: 1.45;
        }
        .if-status-dot {
            display: inline-block; width: 7px; height: 7px; margin-right: 7px;
            border-radius: 50%; background: #34D399; box-shadow: 0 0 0 3px rgba(52,211,153,.12);
        }

        .if-header { margin-bottom: 1.35rem; }
        .if-eyebrow {
            color: var(--if-primary); font-size: .73rem; font-weight: 800;
            letter-spacing: .1em; text-transform: uppercase; margin-bottom: .45rem;
        }
        .if-title { margin: 0; color: var(--if-text) !important; font-size: clamp(1.75rem, 3vw, 2.35rem); line-height: 1.18; font-weight: 780; }
        .if-subtitle { margin: .65rem 0 0; color: var(--if-text-muted); max-width: 760px; font-size: .98rem; }

        .if-hero {
            position: relative; overflow: hidden; padding: clamp(1.5rem, 4vw, 2.5rem);
            border: 1px solid #E7E0F5; border-radius: 20px; background: var(--if-surface);
            box-shadow: var(--if-shadow-md); margin-bottom: 1.35rem;
        }
        .if-hero::after {
            content: ""; position: absolute; width: 220px; height: 220px; right: -90px; top: -110px;
            border-radius: 50%; background: rgba(109,40,217,.08); pointer-events: none;
        }
        .if-hero-kicker { color: var(--if-primary); font-size: .76rem; font-weight: 800; letter-spacing: .08em; }
        .if-hero h1 { max-width: 700px; margin: .55rem 0 .7rem; color: var(--if-text) !important; }
        .if-hero p { max-width: 700px; color: var(--if-text-muted); margin: 0; }

        .if-metric {
            min-height: 126px; padding: 1.15rem 1.2rem; background: var(--if-surface);
            border: 1px solid var(--if-border); border-radius: var(--if-radius-lg);
            box-shadow: var(--if-shadow-sm); margin-bottom: .5rem;
        }
        .if-metric-label { color: var(--if-text-muted); font-size: .78rem; font-weight: 650; }
        .if-metric-value { margin: .35rem 0 .2rem; color: var(--if-text); font-size: 1.9rem; font-weight: 780; line-height: 1.1; }
        .if-metric-note { color: var(--if-text-muted); font-size: .76rem; }

        .if-stepper {
            display: grid; grid-template-columns: repeat(5, minmax(0,1fr)); gap: 8px;
            margin: 1rem 0 1.4rem;
        }
        .if-step {
            padding: .75rem .8rem; border: 1px solid var(--if-border); border-radius: 10px;
            background: var(--if-surface); color: var(--if-text-muted); font-size: .75rem; font-weight: 650;
        }
        .if-step span { display: block; color: #8B8498; font-size: .66rem; margin-bottom: 3px; }
        .if-step.active { background: var(--if-surface-muted); border-color: #C4B5FD; color: var(--if-primary); }
        .if-step.done { border-color: #A7F3D0; background: #F0FDF4; color: var(--if-success); }

        .if-callout {
            margin: 1rem 0; padding: .9rem 1rem; border-radius: var(--if-radius-md);
            border: 1px solid #DDD6FE; border-left: 4px solid var(--if-primary);
            background: #F8F7FF; color: #3F3A4A; font-size: .88rem; line-height: 1.65;
        }
        .if-callout.warning { border-color: #FED7AA; border-left-color: var(--if-warning); background: #FFFBEB; }
        .if-callout.success { border-color: #A7F3D0; border-left-color: var(--if-success); background: #F0FDF4; }

        .if-question {
            padding: 1.35rem 1.45rem; border: 1px solid #DDD6FE; border-radius: var(--if-radius-lg);
            background: var(--if-surface); box-shadow: var(--if-shadow-sm); margin: .85rem 0 1rem;
        }
        .if-question-label { color: var(--if-primary); font-size: .72rem; font-weight: 800; letter-spacing: .08em; }
        .if-question-text { color: var(--if-text); font-size: 1.18rem; font-weight: 680; line-height: 1.55; margin-top: .45rem; }

        [data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--if-surface); border-color: var(--if-border) !important;
            border-radius: var(--if-radius-lg) !important; box-shadow: var(--if-shadow-sm);
        }
        [data-testid="stMetric"] {
            background: var(--if-surface); border: 1px solid var(--if-border);
            padding: 1rem; border-radius: var(--if-radius-md); box-shadow: var(--if-shadow-sm);
        }
        [data-testid="stDataFrame"] { border: 1px solid var(--if-border); border-radius: var(--if-radius-md); overflow: hidden; }
        [data-testid="stExpander"] { border-color: var(--if-border); border-radius: var(--if-radius-md); background: var(--if-surface); }

        .stButton > button, .stDownloadButton > button {
            min-height: 44px; border-radius: var(--if-radius-sm); font-weight: 680;
            border-color: #D7D0E3; transition: background-color 180ms ease, border-color 180ms ease, box-shadow 180ms ease;
        }
        .stButton > button:hover, .stDownloadButton > button:hover {
            border-color: var(--if-primary); color: var(--if-primary); box-shadow: 0 4px 12px rgba(109,40,217,.09);
        }
        .stButton > button[kind="primary"] {
            background: var(--if-primary); border-color: var(--if-primary); color: white;
        }
        .stButton > button[kind="primary"]:hover { background: var(--if-primary-hover); border-color: var(--if-primary-hover); color: white; }
        .stButton > button:focus-visible, .stDownloadButton > button:focus-visible,
        input:focus-visible, textarea:focus-visible, [role="combobox"]:focus-visible {
            outline: 3px solid rgba(109,40,217,.25) !important; outline-offset: 2px;
        }
        input, textarea, [data-baseweb="select"] > div {
            border-radius: var(--if-radius-sm) !important; border-color: #D9D4E2 !important;
        }
        textarea:focus, input:focus { border-color: var(--if-primary) !important; }
        [data-testid="stFileUploaderDropzone"] { background: #FBFAFE; border-color: #D8D0E8; }
        [data-testid="stProgress"] > div > div { background: var(--if-primary); }

        @media (max-width: 760px) {
            .block-container { padding: 1.25rem 1rem 3rem; }
            .if-stepper { grid-template-columns: 1fr; }
            .if-step { padding: .6rem .75rem; }
            .if-metric { min-height: 108px; }
        }
        @media (prefers-reduced-motion: reduce) {
            *, *::before, *::after { scroll-behavior: auto !important; transition-duration: .01ms !important; animation-duration: .01ms !important; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def sidebar_brand() -> None:
    st.sidebar.markdown(
        """
        <div class="if-brand">
          <div class="if-brand-mark notranslate" translate="no">IF</div>
          <div><div class="if-brand-name notranslate" translate="no">Interview Forge</div>
          <div class="if-brand-note">求职准备工作台</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def model_status(label: str, *, model_enabled: bool) -> None:
    headline = "模型推理已就绪" if model_enabled else "规则引擎已就绪"
    st.sidebar.markdown(
        f'<div class="if-status"><span class="if-status-dot"></span>{headline}<br>{escape(label)}</div>',
        unsafe_allow_html=True,
    )


def page_header(eyebrow: str, title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="if-header">
          <div class="if-eyebrow">{escape(eyebrow)}</div>
          <h1 class="if-title">{escape(title)}</h1>
          <p class="if-subtitle">{escape(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def hero(kicker: str, title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="if-hero">
          <div class="if-hero-kicker">{escape(kicker)}</div>
          <h1>{escape(title)}</h1>
          <p>{escape(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str | int, note: str) -> None:
    st.markdown(
        f"""
        <div class="if-metric">
          <div class="if-metric-label">{escape(label)}</div>
          <div class="if-metric-value">{escape(str(value))}</div>
          <div class="if-metric-note">{escape(note)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def workflow(active: int) -> None:
    labels = ("岗位档案", "证据分析", "模拟面试", "薄弱强化", "正式复盘")
    cards = []
    for index, label in enumerate(labels, 1):
        state = "active" if index == active else "done" if index < active else ""
        cards.append(f'<div class="if-step {state}"><span>步骤 {index}</span>{label}</div>')
    st.markdown(f'<div class="if-stepper">{"".join(cards)}</div>', unsafe_allow_html=True)


def callout(text: str, tone: str = "info") -> None:
    class_name = "if-callout" if tone == "info" else f"if-callout {tone}"
    st.markdown(f'<div class="{class_name}">{escape(text)}</div>', unsafe_allow_html=True)


def question_card(question: str) -> None:
    st.markdown(
        f'<div class="if-question"><div class="if-question-label">面试官提问</div>'
        f'<div class="if-question-text">{escape(question)}</div></div>',
        unsafe_allow_html=True,
    )
