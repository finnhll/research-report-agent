"""Async LLM client: JSON-mode chat completion validated against a Pydantic schema.

Same design decision as the sibling ``sentinel`` project's ``moderator.ts``: the model
produces raw structured judgments; validation and the repair-retry policy live in code,
not in a prompt hope. Every agent in this package calls ``complete_structured`` and
trusts only the validated Pydantic object it returns.
"""

from __future__ import annotations

from typing import TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError

from research_report_agent.config import ModelConfig

SchemaT = TypeVar("SchemaT", bound=BaseModel)


class LLMError(RuntimeError):
    """Raised when the model cannot produce schema-valid output after repairs."""


class LLMClient:
    """Chat-completion client bound to one model/endpoint, with schema repair."""

    def __init__(self, config: ModelConfig) -> None:
        if not config.api_key:
            raise LLMError("No model API key configured")
        self._model = config.model
        self._client = AsyncOpenAI(api_key=config.api_key, base_url=config.base_url)

    async def complete_structured(
        self,
        *,
        system: str,
        user: str,
        schema: type[SchemaT],
        max_repairs: int = 1,
    ) -> SchemaT:
        """Call the model and validate its JSON reply against ``schema``.

        On invalid JSON or a schema validation failure, retries up to ``max_repairs``
        times with the error fed back to the model, matching the repair policy
        documented in ``docs/spec/design.md`` (planner/worker/report schema repair).
        """

        messages: list[dict[str, str]] = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        last_error: Exception | None = None

        for attempt in range(max_repairs + 1):
            response = await self._client.chat.completions.create(
                model=self._model,
                temperature=0,
                response_format={"type": "json_object"},
                messages=messages,  # type: ignore[arg-type]
            )
            content = response.choices[0].message.content or ""
            try:
                return schema.model_validate_json(content)
            except ValidationError as exc:
                last_error = exc
                feedback = f"That response failed schema validation:\n{exc}"
            except ValueError as exc:
                last_error = exc
                feedback = f"That response was not valid JSON: {exc}"

            if attempt >= max_repairs:
                break
            messages.append({"role": "assistant", "content": content})
            repair_prompt = (
                f"{feedback}\n\nReturn corrected JSON only, matching the required shape."
            )
            messages.append({"role": "user", "content": repair_prompt})

        raise LLMError(
            f"Model failed to produce valid {schema.__name__} after repairs: {last_error}"
        )

    async def list_model_ids(self) -> list[str]:
        """Used only by the Settings panel's "Test connection" action."""

        response = await self._client.models.list()
        return [item.id for item in response.data]


__all__ = ["LLMClient", "LLMError"]
