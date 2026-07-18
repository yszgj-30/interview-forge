from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_all_pages_render_with_demo_data(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("INTERVIEW_FORGE_DB", str(tmp_path / "app.db"))
    monkeypatch.setenv("INTERVIEW_FORGE_DISABLE_OLLAMA", "1")
    app_path = Path(__file__).parents[1] / "app.py"
    app = AppTest.from_file(str(app_path), default_timeout=15).run()
    assert not app.exception

    demo_button = next(button for button in app.button if button.label == "载入脱敏演示数据")
    demo_button.click().run()
    assert not app.exception

    expected_titles = {
        "工作台": "让每一次训练，都转化为下一次面试的确定性",
        "简历与 JD": "简历与岗位匹配",
        "语音模拟面试": "沉浸式语音模拟面试",
        "正式面试复盘": "正式面试录音与会后复盘",
        "面试知识库": "个人面试知识库",
    }
    for page, title in expected_titles.items():
        app.radio[0].set_value(page).run()
        assert not app.exception
        rendered = "\n".join(str(element.value) for element in app.markdown)
        assert title in rendered
