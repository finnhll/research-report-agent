from __future__ import annotations

from pathlib import Path

import pytest

from research_report_agent import config


@pytest.fixture(autouse=True)
def isolated_config_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "_CONFIG_PATH", tmp_path / "model-config.json")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AGENT_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)


def test_load_config_defaults_without_file_or_env() -> None:
    loaded = config.load_config()

    assert loaded.model == "gpt-4o-mini"
    assert loaded.base_url is None
    assert loaded.api_key is None


def test_env_vars_are_used_when_no_file_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")
    monkeypatch.setenv("AGENT_MODEL", "env-model")

    loaded = config.load_config()

    assert loaded.model == "env-model"
    assert loaded.api_key == "env-key"


def test_saved_file_overrides_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")
    config.save_config(model="file-model", api_key="file-key")

    loaded = config.load_config()

    assert loaded.model == "file-model"
    assert loaded.api_key == "file-key"


def test_save_config_without_api_key_keeps_existing_key() -> None:
    config.save_config(model="model-a", api_key="secret")

    config.save_config(model="model-b")

    loaded = config.load_config()
    assert loaded.model == "model-b"
    assert loaded.api_key == "secret"


def test_mask_key_short_and_long() -> None:
    assert config.mask_key(None) is None
    assert config.mask_key("short") == "••••••••"
    assert config.mask_key("sk-1234567890") == "sk-12…7890"


def test_get_config_info_reports_key_source() -> None:
    config.save_config(model="model-a", api_key="secret")

    info = config.get_config_info()

    assert info.key_source == "file"
    assert info.api_key_masked is not None
