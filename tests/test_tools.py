from __future__ import annotations

import pytest

from research_report_agent.runtime_contracts import ToolRequest
from research_report_agent.tools import ToolExecutor


@pytest.fixture
def executor() -> ToolExecutor:
    return ToolExecutor()


def request(executor: ToolExecutor, tool: str, payload: dict[str, object]) -> ToolRequest:
    return ToolRequest(
        request_id=f"tool_req_{executor.call_count + 1}",
        attempt_id="task_001_attempt_001",
        tool=tool,
        input=payload,
    )


async def test_web_search_returns_source_metadata(executor: ToolExecutor) -> None:
    result = await executor.execute(
        request(executor, "web_search", {"query": "EV battery cost safety"})
    )

    assert result.status.value == "success"
    assert result.output["results"]
    assert all("url" in item for item in result.output["results"])


async def test_web_search_requires_query(executor: ToolExecutor) -> None:
    result = await executor.execute(request(executor, "web_search", {}))

    assert result.status.value == "error"
    assert result.error == "query is required"


async def test_fetch_page_rejects_private_network(executor: ToolExecutor) -> None:
    result = await executor.execute(
        request(executor, "fetch_page", {"url": "http://127.0.0.1:8000/admin"})
    )

    assert result.status.value == "blocked"
    assert "non-public address" in result.error


async def test_fetch_page_returns_local_catalog_document(executor: ToolExecutor) -> None:
    result = await executor.execute(
        request(executor, "fetch_page", {"url": "https://example.com/ev-battery-overview"})
    )

    assert result.status.value == "success"
    assert result.output["title"] == "EV Battery Chemistry Overview"


async def test_calculator_evaluates_without_exec(executor: ToolExecutor) -> None:
    result = await executor.execute(request(executor, "calculator", {"expression": "(2 + 3) * 4"}))

    assert result.status.value == "success"
    assert result.output["value"] == 20


@pytest.mark.parametrize("expression", ["2 +", "import os", "__import__('os')"])
async def test_calculator_rejects_invalid_expression(
    executor: ToolExecutor,
    expression: str,
) -> None:
    result = await executor.execute(request(executor, "calculator", {"expression": expression}))

    assert result.status.value == "error"


async def test_unknown_tool_is_rejected(executor: ToolExecutor) -> None:
    result = await executor.execute(request(executor, "shell", {"command": "ls"}))

    assert result.status.value == "error"
