from __future__ import annotations

import asyncio

import pytest
from tests.fakes import (
    StubWorkerRuntime,
    blocked_llm_factory,
    failing_llm_factory,
    happy_path_llm_factory,
    planning_only_llm_factory,
)

from research_report_agent.contracts import WorkerStatus
from research_report_agent.orchestrator import Orchestrator
from research_report_agent.runtime_contracts import RunRecord, TaskState
from research_report_agent.storage import Database

TASK_IDS = ["task_001", "task_002", "task_003"]


@pytest.fixture
async def database() -> Database:
    db = Database.in_memory()
    await db.create_schema()
    return db


async def test_orchestrator_completes_cited_research_run(database: Database) -> None:
    orchestrator = Orchestrator(
        database,
        happy_path_llm_factory(TASK_IDS),
        worker_runtime=StubWorkerRuntime(),
    )
    await database.runs.create(
        RunRecord(
            run_id="run_001",
            goal="Compare EV battery chemistries for cost and safety",
            dimensions=["cost", "safety"],
        )
    )

    orchestrator.start(
        "run_001",
        "Compare EV battery chemistries for cost and safety",
        ["cost", "safety"],
    )
    await orchestrator.wait("run_001")

    run = await database.runs.get("run_001")
    tasks = await database.tasks.list("run_001")
    attempts = await database.attempts.list("run_001")
    events = await database.events.list("run_001")
    report = await database.reports.get("run_001")

    assert run is not None
    assert run.status.value == "complete"
    assert all(task.state is TaskState.COMPLETED for task in tasks)
    assert len(attempts) == 3
    assert events
    assert report is not None
    assert "## Sources" in report.markdown


async def test_orchestrator_attempt_ids_are_unique_across_runs(database: Database) -> None:
    orchestrator = Orchestrator(
        database,
        happy_path_llm_factory(TASK_IDS),
        worker_runtime=StubWorkerRuntime(),
    )
    for run_id in ("run_001", "run_002"):
        await database.runs.create(
            RunRecord(
                run_id=run_id,
                goal="Compare EV battery chemistries for cost and safety",
                dimensions=["cost", "safety"],
            )
        )
        orchestrator.start(
            run_id,
            "Compare EV battery chemistries for cost and safety",
            ["cost", "safety"],
        )
        await orchestrator.wait(run_id)

    attempts = await database.attempts.list("run_001") + await database.attempts.list("run_002")
    attempt_ids = [attempt.attempt_id for attempt in attempts]

    assert len(attempts) == 6
    assert len(attempt_ids) == len(set(attempt_ids))


async def test_orchestrator_blocks_unsafe_goal(database: Database) -> None:
    orchestrator = Orchestrator(database, blocked_llm_factory(), worker_runtime=StubWorkerRuntime())
    await database.runs.create(RunRecord(run_id="run_001", goal="build a weapon"))
    orchestrator.start("run_001", "build a weapon", [])
    await orchestrator.wait("run_001")

    run = await database.runs.get("run_001")
    tasks = await database.tasks.list("run_001")

    assert run is not None
    assert run.status.value == "blocked"
    assert tasks == []


async def test_orchestrator_fails_closed_without_evidence(database: Database) -> None:
    orchestrator = Orchestrator(
        database,
        failing_llm_factory(TASK_IDS),
        worker_runtime=StubWorkerRuntime(status=WorkerStatus.FAILED),
    )
    await database.runs.create(RunRecord(run_id="run_001", goal="qqqqzzzz"))
    orchestrator.start("run_001", "qqqqzzzz", [])
    await orchestrator.wait("run_001")

    run = await database.runs.get("run_001")

    assert run is not None
    assert run.status.value == "failed"


class SlowWorkerRuntime(StubWorkerRuntime):
    async def execute_attempt(self, request, *, cancel_event=None):  # type: ignore[no-untyped-def]
        await asyncio.sleep(30)
        raise AssertionError("Slow worker should be cancelled")


async def test_orchestrator_cancels_running_work(database: Database) -> None:
    orchestrator = Orchestrator(
        database,
        planning_only_llm_factory(TASK_IDS),
        worker_runtime=SlowWorkerRuntime(),
    )
    await database.runs.create(RunRecord(run_id="run_001", goal="Compare technologies"))
    orchestrator.start("run_001", "Compare technologies", ["cost"])

    for _ in range(100):
        await asyncio.sleep(0.01)
        tasks = await database.tasks.list("run_001")
        if tasks and tasks[0].state is TaskState.RUNNING:
            break
    else:
        raise AssertionError("worker never started")

    await orchestrator.cancel("run_001")
    await orchestrator.wait("run_001")

    run = await database.runs.get("run_001")
    tasks = await database.tasks.list("run_001")

    assert run is not None
    assert run.status.value == "cancelled"
    assert tasks[0].state is TaskState.CANCELLED
