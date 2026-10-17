"""Minimal OpenAI-compatible chat client. Structured output is requested, but callers must still
validate with pydantic: local models drift."""
import json

import httpx
from pydantic import BaseModel

from app.config import get_settings


class LLMUnavailable(Exception):
    pass


class LLMClient:
    def __init__(self, base_url: str | None = None, model: str | None = None, api_key: str | None = None,
                 transport: httpx.BaseTransport | None = None, timeout: float = 120):
        s = get_settings()
        self.base_url = (base_url or s.llm_base_url).rstrip("/")
        self.model = model or s.llm_model
        self.api_key = api_key if api_key is not None else s.llm_api_key
        self._http = httpx.Client(transport=transport, timeout=timeout)

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.model)

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

    def reachable(self) -> bool:
        if not self.configured:
            return False
        try:
            return self._http.get(f"{self.base_url}/models", headers=self._headers(), timeout=5).status_code < 500
        except httpx.HTTPError:
            return False

    def chat_json(self, system: str, user: str, schema: type[BaseModel]) -> BaseModel:
        """Returns a validated model instance. Raises LLMUnavailable if the host can't be reached,
        ValueError if the reply isn't valid for the schema."""
        if not self.configured:
            raise LLMUnavailable("LLM_BASE_URL / LLM_MODEL not set")
        payload = {
            "model": self.model, "temperature": 0,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "response_format": {"type": "json_schema", "json_schema": {
                "name": schema.__name__, "schema": schema.model_json_schema(), "strict": True}},
        }
        try:
            r = self._http.post(f"{self.base_url}/chat/completions", json=payload, headers=self._headers())
        except httpx.HTTPError as exc:
            raise LLMUnavailable(str(exc)) from exc
        if r.status_code >= 500 or r.status_code == 429:
            raise LLMUnavailable(f"HTTP {r.status_code}")
        if r.status_code != 200:
            raise ValueError(f"LLM HTTP {r.status_code}: {r.text[:200]}")
        try:
            content = r.json()["choices"][0]["message"]["content"]
            return schema.model_validate(json.loads(_strip_fence(content)))
        except Exception as exc:  # malformed JSON, wrong shape, missing keys
            raise ValueError(f"invalid LLM output: {exc}") from exc


def _strip_fence(s: str) -> str:
    s = s.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[1] if "\n" in s else s
        s = s.rsplit("```", 1)[0]
    return s
