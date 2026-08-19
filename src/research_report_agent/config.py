"""Model API configuration: file-backed with environment variable fallback.

Mirrors the sibling ``sentinel`` project's ``src/config.ts`` so both products in this
workspace behave the same way: settings saved through the web UI are persisted to a
gitignored ``model-config.json`` and take priority over environment variables, so the
raw key is never round-tripped through the browser after it is first saved.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel

_CONFIG_PATH = Path(os.getenv("RESEARCH_REPORT_AGENT_CONFIG", "model-config.json"))


class ModelConfig(BaseModel):
    """Effective model configuration used to build an LLM client."""

    model: str = "gpt-4o-mini"
    base_url: str | None = None
    api_key: str | None = None


class ModelConfigInfo(BaseModel):
    """UI-safe view of the configuration: the raw key is never exposed."""

    model: str
    base_url: str | None
    api_key_masked: str | None
    key_source: str | None


def _read_file() -> dict[str, Any]:
    try:
        return json.loads(_CONFIG_PATH.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def load_config() -> ModelConfig:
    """Effective config: file values override environment variables."""

    file = _read_file()
    return ModelConfig(
        model=file.get("model") or os.getenv("AGENT_MODEL") or "gpt-4o-mini",
        base_url=file.get("base_url") or os.getenv("OPENAI_BASE_URL") or None,
        api_key=file.get("api_key") or os.getenv("OPENAI_API_KEY") or None,
    )


def save_config(
    *,
    model: str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
) -> None:
    """Persist updates. An empty api_key means "keep the existing key"."""

    file = _read_file()
    if model:
        file["model"] = model
    if base_url is not None:
        if base_url:
            file["base_url"] = base_url
        else:
            file.pop("base_url", None)
    if api_key:
        file["api_key"] = api_key
    _CONFIG_PATH.write_text(json.dumps(file, indent=2) + "\n")


def mask_key(key: str | None) -> str | None:
    if not key:
        return None
    if len(key) <= 8:
        return "••••••••"
    return f"{key[:5]}…{key[-4:]}"


def get_config_info() -> ModelConfigInfo:
    file = _read_file()
    config = load_config()
    return ModelConfigInfo(
        model=config.model,
        base_url=config.base_url,
        api_key_masked=mask_key(config.api_key),
        key_source="file" if file.get("api_key") else ("env" if config.api_key else None),
    )


__all__ = [
    "ModelConfig",
    "ModelConfigInfo",
    "get_config_info",
    "load_config",
    "mask_key",
    "save_config",
]
