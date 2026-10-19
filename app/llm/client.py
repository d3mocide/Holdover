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
                 transport: httpx.BaseTransport | None = None, timeout: float | None = None):
        s = get_settings()
        self.base_url = (base_url or s.llm_base_url).rstrip("/")
        self.model = model or s.llm_model
        self.api_key = api_key if api_key is not None else s.llm_api_key
        self._http = httpx.Client(transport=transport, timeout=timeout if timeout is not None else s.llm_timeout)

    @classmethod
    def for_extraction(cls) -> "LLMClient":
        """The client for the weekly report extraction: LLM_EXTRACT_MODEL (or the usual model) with the long extraction timeout."""
        s = get_settings()
        return cls(model=s.llm_extract_model or s.llm_model, timeout=s.llm_extract_timeout)

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

    def models(self) -> list[str] | None:
        """Model ids the server lists (OpenAI-style GET /models), or None if it cannot be asked."""
        try:
            r = self._http.get(f"{self.base_url}/models", headers=self._headers(), timeout=5)
            return [m["id"] for m in r.json()["data"]] if r.status_code == 200 else None
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            return None

    def status_line(self) -> str:
        """One sentence for the startup log that says what is wrong, because a bad setting otherwise shows up only as 500s later."""
        if not self.configured:
            return "not configured (set LLM_BASE_URL and LLM_MODEL): reports use plain templates, which is fine"
        ids = self.models()
        if ids is None:
            return f"{self.base_url} did not answer GET /models: check LLM_BASE_URL (OpenAI-compatible, usually ending in /v1)"
        if self.model not in ids:
            return f"{self.base_url} is up but does not list model '{self.model}'. It has: {', '.join(ids) or 'none'}. Use one of those exactly, with no provider prefix"
        return f"{self.base_url} model '{self.model}' is available"

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
            message = r.json()["choices"][0]["message"]
            # Reasoning models served by llama.cpp-style servers can leave "content" empty and put the answer in
            # "reasoning_content" (or "reasoning"). The JSON is the same; read whichever holds it.
            content = message.get("content") or message.get("reasoning_content") or message.get("reasoning") or ""
            return schema.model_validate(_fit(json.loads(_strip_fence(content)), schema))
        except Exception as exc:  # malformed JSON, wrong shape, missing keys
            raise ValueError(f"invalid LLM output: {exc}") from exc


def _strip_fence(s: str) -> str:
    s = s.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[1] if "\n" in s else s
        s = s.rsplit("```", 1)[0]
    return s


def _fit(data, schema: type[BaseModel]):
    """Some local servers do not enforce the JSON schema and answer with the bare list a schema wraps in an object
    (`[...]` instead of `{"items": [...]}`). Wrap that one case; everything is still validated strictly afterwards."""
    fields = schema.model_fields
    if isinstance(data, list) and len(fields) == 1:
        return {next(iter(fields)): data}
    return data
