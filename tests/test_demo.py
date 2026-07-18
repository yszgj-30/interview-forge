from pathlib import Path

from interview_forge.demo import DEMO_PROFILE_NAME, seed_demo
from interview_forge.storage import Storage


def test_demo_seed_is_complete_and_idempotent(tmp_path: Path):
    storage = Storage(tmp_path / "demo.db")
    examples = Path(__file__).parents[1] / "examples"

    assert seed_demo(storage, examples) is True
    assert seed_demo(storage, examples) is False
    assert storage.count("profiles") == 1
    assert storage.count("questions") == 3
    assert storage.count("reviews") == 1
    assert storage.list_profiles()[0]["name"] == DEMO_PROFILE_NAME


def test_demo_material_is_explicitly_fictional():
    resume = (Path(__file__).parents[1] / "examples" / "sample_resume.md").read_text(encoding="utf-8")
    assert "虚构示例" in resume
    assert "仅用于产品演示" in resume
