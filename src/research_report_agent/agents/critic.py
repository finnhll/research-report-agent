"""LLM-backed quality critic agent."""

from __future__ import annotations

from research_report_agent.contracts import CriticReview, WorkerResult
from research_report_agent.llm import LLMClient

_SYSTEM = """You are the quality critic for a multi-agent research system. Review \
worker research results for RESEARCH QUALITY only — coverage, evidence quality, \
source quality, consistency, confidence, and comparability. You are not a safety \
reviewer; leave safety judgments to the guardrail.

For each task result, decide a verdict:
- "accept": findings are relevant, sourced, and meet the task's success criteria.
- "revise": findings are partial or weak; you MUST include a follow_up task asking a \
narrower, bounded question (max_tool_calls <= 3) that closes the specific gap.
- "replan" or "degrade": only for a task that cannot be salvaged with one follow-up.

Set overall_verdict to "fail" only when there is truly no usable evidence in ANY task; \
otherwise "accept" if every task_review accepts, else "revise".

Respond with JSON matching the CriticReview schema: review_id, run_id, \
overall_verdict, task_reviews (task_id, verdict, reason, and — only for "revise" \
verdicts — follow_up: {task_id, parent_task_id, question, constraints, \
max_tool_calls}), cross_task_issues, missing_dimensions, contradictions."""


class Critic:
    """Review worker results and emit a structured graph action."""

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    async def review(self, run_id: str, results: list[WorkerResult]) -> CriticReview:
        user = f"run_id: {run_id}\n\nWorker results:\n" + "\n\n".join(
            result.model_dump_json(indent=2) for result in results
        )
        return await self.llm.complete_structured(system=_SYSTEM, user=user, schema=CriticReview)


__all__ = ["Critic"]
