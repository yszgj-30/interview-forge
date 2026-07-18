from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

import requests


@dataclass(frozen=True)
class LLMConfig:
    base_url: str = ""
    model: str = ""
    api_key: str = ""
    timeout: int = 90

    @property
    def enabled(self) -> bool:
        return bool(self.base_url.strip() and self.model.strip())


class LLMClient:
    """Small OpenAI-compatible client that also works with Ollama's /v1 API."""

    def __init__(self, config: LLMConfig) -> None:
        self.config = config

    def complete(self, system: str, user: str, temperature: float = 0.2) -> str:
        return self._complete(system, user, temperature, json_mode=False)

    def _complete(
        self, system: str, user: str, temperature: float = 0.2, json_mode: bool = False,
    ) -> str:
        if not self.config.enabled:
            raise RuntimeError("未配置大模型服务。")
        base_url = self.config.base_url.rstrip("/")
        is_ollama = ":11434" in base_url
        url = base_url.removesuffix("/v1") + "/api/chat" if is_ollama else base_url + "/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        if is_ollama:
            request_body: dict[str, Any] = {
                "model": self.config.model,
                "messages": messages,
                "stream": False,
                "think": False,
                "options": {"temperature": temperature, "num_predict": 512 if json_mode else 1200},
            }
            if json_mode:
                request_body["format"] = "json"
        else:
            request_body = {
                "model": self.config.model,
                "messages": messages,
                "temperature": temperature,
            }
        try:
            response = requests.post(
                url,
                headers=headers,
                json=request_body,
                timeout=self.config.timeout,
            )
            response.raise_for_status()
            payload = response.json()
            if is_ollama:
                return payload["message"]["content"].strip()
            return payload["choices"][0]["message"]["content"].strip()
        except (requests.RequestException, KeyError, TypeError, ValueError) as exc:
            raise RuntimeError(f"大模型服务调用失败：{exc}") from exc

    def complete_json(self, system: str, user: str) -> Any:
        text = self._complete(
            system + "\n只输出合法 JSON，不要使用 Markdown 代码块。",
            user,
            json_mode=True,
        )
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"(\{.*\}|\[.*\])", cleaned, flags=re.S)
            if not match:
                raise RuntimeError("模型没有返回可解析的 JSON。")
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError as exc:
                raise RuntimeError("模型返回的 JSON 格式不正确。") from exc
