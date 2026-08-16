"""Intake and final-output guardrail agents."""

from __future__ import annotations

import re

from research_report_agent.contracts import (
    GuardrailCheck,
    GuardrailCheckStatus,
    GuardrailCheckType,
    GuardrailMode,
    GuardrailReview,
    GuardrailVerdict,
)


class IntakeGuardrail:
    """Review the user goal before planning or worker dispatch."""

    def review(self, goal: str) -> GuardrailReview:
        lowered = goal.lower()
        harmful = any(
            term in lowered
            for term in (
                "weapon",
                "explosive",
                "malware",
                "ransomware",
                "exploit",
                "doxx",
                "home address",
                "private data",
                "ignore previous instructions",
            )
        )
        privacy = any(term in lowered for term in ("home address", "private data", "doxx", "ssn"))
        override = "ignore previous instructions" in lowered

        checks = [
            GuardrailCheck(
                check=GuardrailCheckType.HARMFUL_CONTENT,
                status=GuardrailCheckStatus.BLOCKED if harmful else GuardrailCheckStatus.PASS,
            ),
            GuardrailCheck(
                check=GuardrailCheckType.PRIVACY,
                status=GuardrailCheckStatus.BLOCKED if privacy else GuardrailCheckStatus.PASS,
            ),
            GuardrailCheck(
                check=GuardrailCheckType.INSTRUCTION_OVERRIDE,
                status=GuardrailCheckStatus.BLOCKED if override else GuardrailCheckStatus.PASS,
            ),
        ]

        if harmful or privacy or override:
            return GuardrailReview(
                guardrail_id="guardrail_intake_001",
                run_id="run_pending",
                mode=GuardrailMode.INTAKE,
                verdict=GuardrailVerdict.BLOCK,
                risk_level="high",
                checks=checks,
                reason="The research goal requests unsafe or private information.",
                blocked_reason="This research goal is not allowed.",
            )

        return GuardrailReview(
            guardrail_id="guardrail_intake_001",
            run_id="run_pending",
            mode=GuardrailMode.INTAKE,
            verdict=GuardrailVerdict.ALLOW,
            risk_level="low",
            checks=checks,
            reason="General research comparison.",
            conditions=["Do not collect private personal data"],
        )


class FinalGuardrail:
    """Review rendered report content before delivery."""

    _DANGEROUS = re.compile(
        r"\b(build a weapon|make an explosive|write malware|steal|home address)\b",
        re.IGNORECASE,
    )
    _DIRECTIVE_ADVICE = re.compile(
        r"\b(you should (immediately )?(buy|invest in|use)|guaranteed safe|best investment)\b",
        re.IGNORECASE,
    )

    def review_markdown(self, markdown: str) -> GuardrailReview:
        dangerous = bool(self._DANGEROUS.search(markdown))
        directive = bool(self._DIRECTIVE_ADVICE.search(markdown))
        injected = "ignore previous instructions" in markdown.lower()

        checks = [
            GuardrailCheck(
                check=GuardrailCheckType.HARMFUL_CONTENT,
                status=GuardrailCheckStatus.BLOCKED if dangerous else GuardrailCheckStatus.PASS,
            ),
            GuardrailCheck(
                check=GuardrailCheckType.HIGH_RISK_ADVICE,
                status=GuardrailCheckStatus.FLAGGED if directive else GuardrailCheckStatus.PASS,
            ),
            GuardrailCheck(
                check=GuardrailCheckType.PROMPT_INJECTION_LEAKAGE,
                status=GuardrailCheckStatus.BLOCKED if injected else GuardrailCheckStatus.PASS,
            ),
        ]

        if dangerous or injected:
            return GuardrailReview(
                guardrail_id="guardrail_final_001",
                run_id="run_pending",
                mode=GuardrailMode.FINAL_OUTPUT,
                verdict=GuardrailVerdict.BLOCK,
                risk_level="critical",
                checks=checks,
                reason="Generated report contains unsafe content.",
                blocked_reason="The generated report is not safe to deliver.",
            )

        if directive:
            return GuardrailReview(
                guardrail_id="guardrail_final_001",
                run_id="run_pending",
                mode=GuardrailMode.FINAL_OUTPUT,
                verdict=GuardrailVerdict.REVISE,
                risk_level="medium",
                checks=checks,
                reason="Generated report gives overly directive purchasing advice.",
                revision_instructions=[
                    "Reframe the conclusion as an evidence-based technology tradeoff",
                    "State that the report is not purchasing, safety, legal, or financial advice",
                ],
            )

        return GuardrailReview(
            guardrail_id="guardrail_final_001",
            run_id="run_pending",
            mode=GuardrailMode.FINAL_OUTPUT,
            verdict=GuardrailVerdict.ALLOW,
            risk_level="low",
            checks=checks,
            reason="Generated report passes final-output policy checks.",
        )


__all__ = ["FinalGuardrail", "IntakeGuardrail"]
