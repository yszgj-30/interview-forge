import requests
import pytest

from interview_forge.llm import LLMClient, LLMConfig


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def test_ollama_uses_native_chat_and_json_mode(monkeypatch):
    captured = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return FakeResponse({"message": {"content": '{"score": 88}'}})

    monkeypatch.setattr(requests, "post", fake_post)
    client = LLMClient(LLMConfig("http://127.0.0.1:11434/v1", "qwen3:4b"))

    assert client.complete_json("system", "user") == {"score": 88}
    assert captured["url"] == "http://127.0.0.1:11434/api/chat"
    assert captured["json"]["think"] is False
    assert captured["json"]["format"] == "json"
    assert captured["json"]["options"]["num_predict"] == 512
    assert "Authorization" not in captured["headers"]


def test_openai_compatible_path_and_api_key(monkeypatch):
    captured = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return FakeResponse({"choices": [{"message": {"content": "ok"}}]})

    monkeypatch.setattr(requests, "post", fake_post)
    client = LLMClient(LLMConfig("https://llm.example/v1", "demo", "secret"))

    assert client.complete("system", "user") == "ok"
    assert captured["url"] == "https://llm.example/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer secret"


def test_llm_network_failure_becomes_domain_error(monkeypatch):
    def fail(*args, **kwargs):
        raise requests.ConnectionError("offline")

    monkeypatch.setattr(requests, "post", fail)
    client = LLMClient(LLMConfig("http://127.0.0.1:11434/v1", "qwen3:4b"))

    with pytest.raises(RuntimeError, match="大模型服务调用失败"):
        client.complete("system", "user")
