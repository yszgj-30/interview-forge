from __future__ import annotations

import os
from functools import lru_cache


def transcribe(audio_path: str) -> str:
    """Transcribe locally when faster-whisper is installed."""
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError("未安装本地语音包，请运行 pip install -r requirements-audio.txt") from exc

    model = _model(WhisperModel, os.getenv("WHISPER_MODEL", "base"))
    segments, _ = model.transcribe(audio_path, vad_filter=True, language="zh")
    return "".join(segment.text for segment in segments).strip()


@lru_cache(maxsize=2)
def _model(model_class, model_name: str):
    return model_class(model_name, device="cpu", compute_type="int8")
