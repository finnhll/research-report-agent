from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import IntegrityError

from research_report_agent.contracts import ResearchTask
from research_report_agent.runtime_contracts import (
    AgentEvent,
    RunRecord,
    TaskState,
    WorkerAttempt,
    WorkerResult,
)
from research_report_agent.storage import Database


@pytest.fixture
async def database() -> Database:
    db = Database.in_memory()
    await db.create_schema()
    return db


async def test_run_round_trip(database: Database) -> None:
    run = RunRecord(run_id="run_001", goal="Compare technologies")
    await database.runs.create(run)
    await database.runs.set_phase("run_001", "executing")
    stored = await database.runs.get("run_001")

    assert stored is not None
    assert stored.goal == "Compare technologies"
    assert stored.phase.value == "executing"
    assert stored.status.value == "running"


async def test_duplicate_run_id_rejected(database: Database) -> None:
    await database.runs.create(RunRecord(run_id="run_001", goal="One"))

    with pytest.raises(IntegrityError):
        await database.runs.create(RunRecord(run_id="run_001", goal="Two"))


async def test_task_attempt_and_event_persistence(database: Database) -> None:
    await database.runs.create(RunRecord(run_id="run_001", goal="Compare technologies"))
    task = ResearchTask(
        task_id="task_001",
        question="Identify technologies",
        success_criteria=["Identify three technologies"],
        required_tools=["web_search"],
        priority="high",
    )
    await database.tasks.replace("run_001", "plan_001", 1, [task])
    await database.tasks.set_state("run_001", "task_001", TaskState.RUNNING)

    now = datetime.now(UTC)
    attempt = WorkerAttempt(
        run_id="run_001",
        plan_id="plan_001",
        plan_version=1,
        task_id="task_001",
        attempt_id="task_001_attempt_001",
        state=TaskState.COMPLETED,
        started_at=now,
        completed_at=now,
        result=WorkerResult(
            task_id="task_001",
            status="completed",
            summary="Identified technologies.",
        ),
    )
    await database.attempts.add(attempt)
    await database.events.append(
        AgentEvent(
            event_id="event_001",
            run_id="run_001",
            event_type="worker.attempt.completed",
            task_id="task_001",
            attempt_id="task_001_attempt_001",
        )
    )

    tasks = await database.tasks.list("run_001")
    attempts = await database.attempts.list("run_001")
    events = await database.events.list("run_001")

    assert tasks[0].state is TaskState.RUNNING
    assert attempts[0].result is not None
    assert events[0][1].event_type == "worker.attempt.completed"


async def test_report_round_trip(database: Database) -> None:
    from research_report_agent.runtime_contracts import ReportDocument

    await database.runs.create(RunRecord(run_id="run_001", goal="Compare technologies"))
    report = ReportDocument(
        report_id="report_001",
        run_id="run_001",
        title="Technology comparison",
        markdown="# Technology comparison",
        structured={},
        guardrail_verdict="allow",
    )
    await database.reports.save(report)
    stored = await database.reports.get("run_001")

    assert stored is not None
    assert stored.markdown.startswith("#")
