"""Quality critic agent."""

from __future__ import annotations

from research_report_agent.contracts import (
    CriticReview,
    CriticTaskReview,
    CriticVerdict,
    FollowUpTask,
    WorkerResult,
)


class Critic:
    """Review worker results and emit a structured graph action."""

    def review(self, results: list[WorkerResult]) -> CriticReview:
        reviews: list[CriticTaskReview] = []
        has_evidence = any(result.findings and result.sources for result in results)

        for result in results:
            acceptable = (
                result.status.value == "completed"
                and bool(result.findings)
                and bool(result.sources)
            )
            if acceptable:
                reviews.append(
                    CriticTaskReview(
                        task_id=result.task_id,
                        verdict=CriticVerdict.ACCEPT,
                        reason="The result has findings, sources, and meets its task boundary.",
                    )
                )
                continue

            reviews.append(
                CriticTaskReview(
                    task_id=result.task_id,
                    verdict=CriticVerdict.REVISE,
                    reason="The result is partial or lacks sufficient sourced findings.",
                    follow_up=FollowUpTask(
                        task_id=f"{result.task_id}_followup_001",
                        parent_task_id=result.task_id,
                        question="Normalize the evidence and address the reported gaps.",
                        constraints=[
                            "Do not introduce unsupported claims",
                            "Preserve existing source IDs where possible",
                            "Report unresolved gaps explicitly",
                        ],
                        max_tool_calls=3,
                    ),
                )
            )

        if not has_evidence:
            overall = CriticVerdict.FAIL
        elif all(review.verdict is CriticVerdict.ACCEPT for review in reviews):
            overall = CriticVerdict.ACCEPT
        else:
            overall = CriticVerdict.REVISE

        return CriticReview(
            review_id="review_001",
            run_id="run_pending",
            overall_verdict=overall,
            task_reviews=reviews,
        )


__all__ = ["Critic"]
