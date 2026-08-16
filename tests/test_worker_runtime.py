from __future__ import annotations

import asyncio

from research_report_agent.runtime_contracts import RunBudget, WorkerAttemptRequest
from research_report_agent.worker_runtime import WorkerRuntime


def request(
    *,
    question: str = "Compare EV battery chemistries for cost and safety",
    allowed_tools: list[str] | None = None,
) -> WorkerAttemptRequest:
    return WorkerAttemptRequest(
        run_id="run_001",
        plan_id="plan_001",
        plan_version=1,
        task_id="task_001",
        attempt_id="task_001_attempt_001",
        question=question,
        success_criteria=["Find at least two sources"],
        allowed_tools=allowed_tools or ["web_search", "fetch_page"],
        limits=RunBudget(max_tool_calls_per_attempt=3),
    )


async def test_worker_completes_with_sourced_findings() -> None:
    runtime = WorkerRuntime()

    result = await runtime.execute_attempt(request())

    assert result.status.value == "completed"
    assert result.findings
    assert len(result.sources) >= 2
    assert result.produced_context


async def test_worker_returns_partial_when_search_has_no_results() -> None:
    runtime = WorkerRuntime()

    result = await runtime.execute_attempt(request(question="qqqqzzzz unrelated topic"))

    assert result.status.value == "partial"
    assert result.gaps


async def test_worker_respects_tool_allowlist() -> None:
    runtime = WorkerRuntime()

    result = await runtime.execute_attempt(request(allowed_tools=["calculator"]))

    assert result.status.value == "blocked"
    assert "web_search" in result.gaps[0]


async def test_worker_enforces_tool_limit() -> None:
    runtime = WorkerRuntime()

    result = await runtime.execute_attempt(
        request().model_copy(
            update={"limits": RunBudget(max_tool_calls_per_attempt=1)},
        )
    )

    assert result.status.value == "partial"
    assert result.sources


async def test_worker_supports_cancellation() -> None:
    runtime = WorkerRuntime()
    cancelled = asyncio.Event()
    cancelled.set()

    result = await runtime.execute_attempt(request(), cancel_event=cancelled)

    assert result.status.value == "failed"
