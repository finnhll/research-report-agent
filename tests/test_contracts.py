from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from research_report_agent.contracts import (
    CriticVerdict,
    Finding,
    GuardrailMode,
    GuardrailReview,
    GuardrailVerdict,
    ResearchPlan,
    ResearchTask,
    Source,
    WorkerResult,
    WorkerStatus,
)

NOW = datetime(2026, 8, 16, tzinfo=UTC)


def make_task(task_id: str, dependencies: list[str] | None = None) -> ResearchTask:
    return ResearchTask(
        task_id=task_id,
        question=f"Research question {task_id}",
        success_criteria=["Find at least two independent sources"],
        required_tools=["web_search"],
        priority="high",
        dependencies=dependencies or [],
    )


def make_source(source_id: str = "src_001") -> Source:
    return Source(
        source_id=source_id,
        title="Example source",
        url="https://example.com/source",
        publisher="Example publisher",
        retrieved_at=NOW,
        credibility="medium",
    )


def test_valid_plan_requires_three_to_six_tasks() -> None:
    plan = ResearchPlan(
        plan_id="plan_001",
        objective="Compare three technologies.",
        tasks=[make_task(f"task_{index}") for index in range(3)],
    )

    assert len(plan.tasks) == 3


@pytest.mark.parametrize("task_count", [0, 1, 2, 7])
def test_plan_rejects_invalid_task_count(task_count: int) -> None:
    with pytest.raises(ValidationError, match="tasks"):
        ResearchPlan(
            plan_id="plan_001",
            objective="Compare technologies.",
            tasks=[make_task(f"task_{index}") for index in range(task_count)],
        )


def test_plan_rejects_circular_dependencies() -> None:
    tasks = [
        make_task("task_001", ["task_003"]),
        make_task("task_002", ["task_001"]),
        make_task("task_003", ["task_002"]),
    ]

    with pytest.raises(ValidationError, match="circular dependency"):
        ResearchPlan(plan_id="plan_001", objective="Compare technologies.", tasks=tasks)


def test_worker_result_rejects_finding_without_source() -> None:
    finding = Finding(
        finding_id="finding_001",
        claim="Example claim",
        evidence="Example evidence",
        source_ids=["src_missing"],
        confidence=0.8,
        limitations=[],
    )

    with pytest.raises(ValidationError, match="src_missing"):
        WorkerResult(
            task_id="task_001",
            status=WorkerStatus.COMPLETED,
            summary="Example summary",
            findings=[finding],
            sources=[make_source()],
            gaps=[],
            contradictions=[],
        )


def test_guardrail_review_accepts_bounded_verdicts() -> None:
    review = GuardrailReview(
        guardrail_id="guardrail_001",
        run_id="run_001",
        mode=GuardrailMode.INTAKE,
        verdict=GuardrailVerdict.ALLOW,
        risk_level="low",
        checks=[],
        reason="General research comparison.",
        conditions=[],
        revision_instructions=[],
    )

    assert review.verdict is GuardrailVerdict.ALLOW
    assert review.mode is GuardrailMode.INTAKE


def test_critic_verdicts_are_closed_set() -> None:
    expected = {"accept", "revise", "replan", "degrade", "fail"}

    assert {member.value for member in CriticVerdict} == expected
