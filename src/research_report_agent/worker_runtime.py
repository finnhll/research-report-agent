"""Bounded ReAct runtime for worker agents."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

from research_report_agent.contracts import Finding, Source, WorkerResult, WorkerStatus
from research_report_agent.runtime_contracts import (
    ToolName,
    ToolRequest,
    ToolResult,
    WorkerAttemptRequest,
    utc_now,
)
from research_report_agent.tools import ToolExecutor


class WorkerRuntime:
    """Execute exactly one bounded worker attempt."""

    def __init__(self, tool_executor: ToolExecutor | None = None) -> None:
        self.tools = tool_executor or ToolExecutor()

    async def execute_attempt(
        self,
        request: WorkerAttemptRequest,
        *,
        cancel_event: asyncio.Event | None = None,
    ) -> WorkerResult:
        observations: list[ToolResult] = []

        if cancel_event is not None and cancel_event.is_set():
            return self._failed(request, "Attempt was cancelled before execution.")

        if ToolName.WEB_SEARCH not in request.allowed_tools:
            return WorkerResult(
                task_id=request.task_id,
                status=WorkerStatus.BLOCKED,
                summary="The required web_search tool is not allowed for this attempt.",
                gaps=["web_search permission is required for external research"],
                tool_trace_ref=self._trace_ref(request, observations),
            )

        search_result = await self._call_tool(
            request,
            ToolName.WEB_SEARCH,
            {"query": self._search_query(request)},
            observations,
        )
        search_items = search_result.output.get("results", [])
        if not isinstance(search_items, list):
            search_items = []

        if not search_items:
            return WorkerResult(
                task_id=request.task_id,
                status=WorkerStatus.PARTIAL,
                summary="No matching documents were found in the local search catalog.",
                gaps=["No source matched the research question"],
                tool_trace_ref=self._trace_ref(request, observations),
            )

        fetched_urls: list[str] = []
        if ToolName.FETCH_PAGE in request.allowed_tools:
            for item in search_items:
                if cancel_event is not None and cancel_event.is_set():
                    return self._failed(request, "Attempt was cancelled during tool use.")
                if len(observations) >= request.limits.max_tool_calls_per_attempt:
                    break
                url = item.get("url")
                if not isinstance(url, str) or url in fetched_urls:
                    continue
                result = await self._call_tool(
                    request,
                    ToolName.FETCH_PAGE,
                    {"url": url},
                    observations,
                )
                if result.status.value == "success":
                    fetched_urls.append(url)

        sources = self._sources(search_items)
        findings = self._findings(request, sources)

        fetched_enough = len(fetched_urls) >= min(2, len(search_items))
        completed = len(sources) >= 2 and fetched_enough and bool(findings)

        return WorkerResult(
            task_id=request.task_id,
            status=WorkerStatus.COMPLETED if completed else WorkerStatus.PARTIAL,
            summary=(
                f"Found {len(sources)} relevant sources and produced "
                f"{len(findings)} sourced findings."
            ),
            findings=findings,
            sources=sources,
            gaps=(
                []
                if completed
                else ["Additional page fetches are needed to fully satisfy success criteria"]
            ),
            contradictions=[],
            tool_trace_ref=self._trace_ref(request, observations),
            produced_context=self._context(search_items),
        )

    async def _call_tool(
        self,
        request: WorkerAttemptRequest,
        tool: ToolName,
        payload: dict[str, Any],
        observations: list[ToolResult],
    ) -> ToolResult:
        tool_request = ToolRequest(
            request_id=f"{request.attempt_id}_tool_{len(observations) + 1:03d}",
            attempt_id=request.attempt_id,
            tool=tool.value,
            input=payload,
        )
        result = await self.tools.execute(tool_request)
        observations.append(result)
        return result

    def _search_query(self, request: WorkerAttemptRequest) -> str:
        entities = request.upstream_context.get("selected_entities")
        if isinstance(entities, list) and entities:
            return f"{request.question} {' '.join(str(item) for item in entities)}"
        return request.question

    def _sources(self, items: list[dict[str, Any]]) -> list[Source]:
        sources: list[Source] = []
        for index, item in enumerate(items, start=1):
            url = item.get("url")
            title = item.get("title")
            publisher = item.get("publisher")
            if not isinstance(url, str) or not isinstance(title, str):
                continue
            published_raw = item.get("published_at")
            published = (
                datetime.fromisoformat(str(published_raw)).replace(tzinfo=UTC)
                if isinstance(published_raw, str)
                else None
            )
            sources.append(
                Source(
                    source_id=f"src_{index:03d}",
                    title=title,
                    url=url,
                    publisher=str(publisher or "Unknown publisher"),
                    published_at=published,
                    retrieved_at=utc_now(),
                    credibility="medium-high",
                    notes=str(item.get("snippet", "")),
                )
            )
        return sources

    def _findings(
        self,
        request: WorkerAttemptRequest,
        sources: list[Source],
    ) -> list[Finding]:
        findings: list[Finding] = []
        for index, source in enumerate(sources, start=1):
            evidence = source.notes or source.title
            findings.append(
                Finding(
                    finding_id=f"finding_{index:03d}",
                    claim=f"Evidence relevant to {request.question.lower()}",
                    evidence=evidence,
                    source_ids=[source.source_id],
                    confidence=0.72,
                    limitations=["Local deterministic catalog evidence; verify with live sources"],
                )
            )
        return findings

    def _context(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        text = " ".join(
            str(item.get("title", "")) + " " + str(item.get("snippet", "")) for item in items
        ).lower()
        entities = [name for name in ("lfp", "nmc", "sodium-ion") if name in text]
        dimensions = [name for name in ("cost", "safety") if name in text]
        return {
            "selected_entities": entities,
            "covered_dimensions": dimensions,
        }

    def _trace_ref(
        self,
        request: WorkerAttemptRequest,
        observations: list[ToolResult],
    ) -> str:
        tool_names = [observation.tool for observation in observations]
        return f"{request.attempt_id}:{'+'.join(tool_names) or 'no-tool'}"

    def _failed(self, request: WorkerAttemptRequest, message: str) -> WorkerResult:
        return WorkerResult(
            task_id=request.task_id,
            status=WorkerStatus.FAILED,
            summary=message,
            gaps=[message],
        )


__all__ = ["WorkerRuntime"]
