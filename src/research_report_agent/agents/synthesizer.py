"""Deterministic synthesizer agent."""

from __future__ import annotations

from research_report_agent.contracts import (
    Finding,
    ReportConclusion,
    ReportSection,
    ResearchReport,
    Source,
    WorkerResult,
)
from research_report_agent.runtime_contracts import ReportDocument


class Synthesizer:
    """Combine accepted worker findings into a cited report."""

    def synthesize(
        self,
        *,
        run_id: str,
        goal: str,
        results: list[WorkerResult],
    ) -> ReportDocument:
        findings, sources = self._merge_evidence(results)
        if not findings or not sources:
            raise ValueError("Cannot synthesize a report without accepted evidence")

        accepted_ids = [finding.finding_id for finding in findings]
        citation_map = {
            f"[{index}]": source.source_id for index, source in enumerate(sources, start=1)
        }
        confidence = sum(finding.confidence for finding in findings) / len(findings)
        limitations = self._limitations(results)
        report = ResearchReport(
            report_id=f"{run_id}_report_001",
            run_id=run_id,
            title=self._title(goal),
            executive_summary=(
                "This report compares the researched options using the accepted evidence below. "
                "Conclusions are evidence-scoped and should not be interpreted as "
                "professional advice."
            ),
            sections=self._sections(results),
            comparison_table_markdown=(
                "| Option | Evidence summary | Confidence |\n|---|---|---:|\n"
                + "\n".join(
                    f"| Evidence {index} | {finding.evidence} | {finding.confidence:.2f} |"
                    for index, finding in enumerate(findings, start=1)
                )
            ),
            conclusions=[
                ReportConclusion(
                    conclusion=(
                        "The evidence supports comparing options by their documented tradeoffs "
                        "rather than selecting a universally superior option."
                    ),
                    confidence=confidence,
                    basis=accepted_ids,
                )
            ],
            limitations=limitations,
            accepted_finding_ids=accepted_ids,
            sources=sources,
            citation_map=citation_map,
        )
        return ReportDocument(
            report_id=report.report_id,
            run_id=run_id,
            title=report.title,
            markdown=self._markdown(report),
            structured=report.model_dump(mode="json"),
            guardrail_verdict="allow",
        )

    def _merge_evidence(
        self,
        results: list[WorkerResult],
    ) -> tuple[list[Finding], list[Source]]:
        findings: list[Finding] = []
        sources: list[Source] = []
        source_id_by_task: dict[tuple[str, str], str] = {}
        source_id_by_url: dict[str, str] = {}

        for result in results:
            for source in result.sources:
                if source.url in source_id_by_url:
                    global_id = source_id_by_url[source.url]
                else:
                    global_id = f"{result.task_id}_{source.source_id}"
                    source_id_by_url[source.url] = global_id
                    sources.append(source.model_copy(update={"source_id": global_id}))
                source_id_by_task[(result.task_id, source.source_id)] = global_id

            for finding in result.findings:
                mapped_ids = [
                    source_id_by_task[(result.task_id, source_id)]
                    for source_id in finding.source_ids
                ]
                findings.append(
                    finding.model_copy(
                        update={
                            "finding_id": f"{result.task_id}_{finding.finding_id}",
                            "source_ids": mapped_ids,
                        }
                    )
                )

        return findings, sources

    def _sections(self, results: list[WorkerResult]) -> list[ReportSection]:
        return [
            ReportSection(
                heading=result.task_id.replace("_", " ").title(),
                markdown=f"{result.summary}\n\n" + "\n".join(item for item in result.gaps),
            )
            for result in results
        ]

    def _limitations(self, results: list[WorkerResult]) -> list[str]:
        limitations = [limitation for result in results for limitation in result.gaps]
        limitations.append("This MVP uses deterministic local evidence for reproducible testing.")
        return limitations

    def _title(self, goal: str) -> str:
        clean = " ".join(goal.split())
        return clean[:120].capitalize() if clean else "Research Report"

    def _markdown(self, report: ResearchReport) -> str:
        lines = [f"# {report.title}", "", report.executive_summary, ""]
        if report.comparison_table_markdown:
            lines.extend(["## Comparison", "", report.comparison_table_markdown, ""])
        for section in report.sections:
            lines.extend([f"## {section.heading}", "", section.markdown, ""])
        lines.extend(["## Conclusions", ""])
        for conclusion in report.conclusions:
            lines.append(f"- {conclusion.conclusion} _(confidence: {conclusion.confidence:.2f})_")
        lines.extend(["", "## Limitations", ""])
        lines.extend(f"- {item}" for item in report.limitations)
        lines.extend(["", "## Sources", ""])
        for label, source_id in report.citation_map.items():
            source = next(item for item in report.sources if item.source_id == source_id)
            lines.append(f"- {label}: {source.title} — {source.publisher} — {source.url}")
        return "\n".join(lines) + "\n"


__all__ = ["Synthesizer"]
