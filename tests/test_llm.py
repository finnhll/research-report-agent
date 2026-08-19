from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from pydantic import BaseModel, ConfigDict, Field

from research_report_agent.config import ModelConfig
from research_report_agent.llm import LLMClient, LLMError


class _Schema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: int = Field(gt=0)


class _FakeCompletions:
    def __init__(self, contents: list[str]) -> None:
        self._contents = list(contents)
        self.calls = 0

    async def create(self, **_kwargs: object) -> SimpleNamespace:
        self.calls += 1
        content = self._contents.pop(0)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


def _client(contents: list[str]) -> tuple[LLMClient, _FakeCompletions]:
    client = LLMClient(ModelConfig(model="test-model", api_key="test-key"))
    completions = _FakeCompletions(contents)
    client._client = SimpleNamespace(chat=SimpleNamespace(completions=completions))  # type: ignore[attr-defined]
    return client, completions


def test_missing_api_key_raises_llm_error() -> None:
    with pytest.raises(LLMError):
        LLMClient(ModelConfig(model="test-model", api_key=None))


async def test_complete_structured_returns_valid_response_first_try() -> None:
    client, completions = _client([json.dumps({"value": 5})])

    result = await client.complete_structured(system="s", user="u", schema=_Schema)

    assert result.value == 5
    assert completions.calls == 1


async def test_complete_structured_repairs_invalid_json() -> None:
    client, completions = _client(["not json at all", json.dumps({"value": 7})])

    result = await client.complete_structured(system="s", user="u", schema=_Schema)

    assert result.value == 7
    assert completions.calls == 2


async def test_complete_structured_repairs_schema_violation() -> None:
    client, completions = _client([json.dumps({"value": -1}), json.dumps({"value": 3})])

    result = await client.complete_structured(system="s", user="u", schema=_Schema)

    assert result.value == 3
    assert completions.calls == 2


async def test_complete_structured_raises_after_exhausting_repairs() -> None:
    client, completions = _client([json.dumps({"value": -1}), json.dumps({"value": -2})])

    with pytest.raises(LLMError):
        await client.complete_structured(system="s", user="u", schema=_Schema, max_repairs=1)

    assert completions.calls == 2
