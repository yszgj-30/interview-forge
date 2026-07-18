import builtins

import pytest

from interview_forge.documents import extract_text
from interview_forge.speech import transcribe


def test_text_extraction_supports_utf8_and_gb18030():
    assert extract_text("resume.md", "项目经历".encode("utf-8")) == "项目经历"
    assert extract_text("resume.txt", "岗位要求".encode("gb18030")) == "岗位要求"


def test_unsupported_document_type_has_clear_error():
    with pytest.raises(ValueError, match="仅支持"):
        extract_text("resume.xlsx", b"not-a-workbook")


def test_missing_speech_extension_has_recovery_command(monkeypatch):
    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "faster_whisper":
            raise ImportError("missing")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(RuntimeError, match="requirements-audio.txt"):
        transcribe("recording.wav")
