"""Research & Report Agent package."""

from research_report_agent.contracts import (
    CriticReview,
    GuardrailReview,
    ResearchPlan,
    ResearchReport,
    WorkerResult,
)

__version__ = "0.1.0"

__all__ = [
    "CriticReview",
    "GuardrailReview",
    "ResearchPlan",
    "ResearchReport",
    "WorkerResult",
    "__version__",
]
