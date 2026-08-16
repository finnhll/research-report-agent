"""Bounded tool layer for worker agents.

The default implementation is deterministic and local. It provides the complete
tool interface and safety controls without requiring external credentials.
"""

from __future__ import annotations

import ast
import asyncio
import ipaddress
import math
import operator
import socket
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from research_report_agent.runtime_contracts import ToolRequest, ToolResult, utc_now


@dataclass(frozen=True)
class SearchDocument:
    title: str
    url: str
    publisher: str
    published_at: str
    snippet: str
    content: str


SEARCH_DOCUMENTS: tuple[SearchDocument, ...] = (
    SearchDocument(
        title="EV Battery Chemistry Overview",
        url="https://example.com/ev-battery-overview",
        publisher="Example Energy Research",
        published_at="2026-01-15",
        snippet="LFP, NMC, and sodium-ion dominate current EV battery deployment discussions.",
        content=(
            "LFP, NMC, and sodium-ion are commercially relevant EV battery chemistries. "
            "LFP is commonly associated with lower material cost and strong thermal stability. "
            "NMC offers higher energy density but uses more expensive materials. "
            "Sodium-ion is emerging as a potentially lower-cost alternative "
            "with good safety characteristics."
        ),
    ),
    SearchDocument(
        title="Battery Cost Survey",
        url="https://example.com/battery-cost-survey",
        publisher="Example Manufacturing Institute",
        published_at="2026-03-02",
        snippet="Pack-level costs differ by chemistry, manufacturing scale, and region.",
        content=(
            "LFP packs are generally less expensive per kWh at scale "
            "because of lower material costs. "
            "NMC packs remain costlier but can deliver more energy from a smaller, lighter pack. "
            "Sodium-ion has projected cost advantages, but commercial deployment remains younger."
        ),
    ),
    SearchDocument(
        title="Battery Safety and Thermal Stability Review",
        url="https://example.com/battery-safety-review",
        publisher="Example Transportation Safety Lab",
        published_at="2026-02-11",
        snippet="Thermal stability varies by chemistry, cell design, and pack engineering.",
        content=(
            "LFP generally has higher thermal runaway onset temperature than NMC. "
            "NMC requires careful thermal and electrical management, "
            "especially at high charge states. "
            "Sodium-ion can offer good thermal stability, though field data is less mature."
        ),
    ),
)

_BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_UNARY_OPERATORS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "for",
    "from",
    "into",
    "of",
    "or",
    "the",
    "this",
    "to",
    "with",
}


class ToolExecutor:
    """Execute typed tool requests with validation and bounded behavior."""

    def __init__(self) -> None:
        self.call_count = 0
        self.search_count = 0
        self._lock = asyncio.Lock()

    async def execute(self, request: ToolRequest) -> ToolResult:
        started_at = utc_now()
        async with self._lock:
            self.call_count += 1

        handler = {
            "web_search": self._web_search,
            "fetch_page": self._fetch_page,
            "calculator": self._calculator,
        }.get(request.tool)

        if handler is None:
            return self._error(request, "unsupported tool", started_at)

        try:
            output = await handler(request.input)
            status = "success" if output.get("status") != "error" else "error"
            output.pop("status", None)
            error = output.pop("error", None)
            if output.get("blocked"):
                status = "blocked"
                output.pop("blocked")
            return ToolResult(
                request_id=request.request_id,
                attempt_id=request.attempt_id,
                tool=request.tool,
                status=status,
                output=output,
                error=error,
                started_at=started_at,
                completed_at=utc_now(),
            )
        except Exception as exc:  # Tool boundaries must fail closed.
            return self._error(request, str(exc), started_at)

    async def _web_search(self, payload: dict[str, Any]) -> dict[str, Any]:
        query = payload.get("query")
        if not isinstance(query, str) or not query.strip():
            return {"status": "error", "error": "query is required"}

        async with self._lock:
            self.search_count += 1

        terms = [
            term for term in query.lower().split() if len(term) >= 3 and term not in _STOPWORDS
        ]
        results = []
        for document in SEARCH_DOCUMENTS:
            haystack = f"{document.title} {document.snippet} {document.content}".lower()
            score = sum(1 for term in terms if term in haystack)
            if score:
                results.append(
                    {
                        "title": document.title,
                        "url": document.url,
                        "publisher": document.publisher,
                        "published_at": document.published_at,
                        "snippet": document.snippet,
                        "score": score,
                    }
                )

        results.sort(key=lambda item: (-item["score"], item["title"]))
        return {"query": query, "results": results[:5]}

    async def _fetch_page(self, payload: dict[str, Any]) -> dict[str, Any]:
        url = payload.get("url")
        if not isinstance(url, str) or not url.strip():
            return {"status": "error", "error": "url is required"}

        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return {"status": "error", "error": "only absolute http(s) URLs are allowed"}

        document = next((item for item in SEARCH_DOCUMENTS if item.url == url), None)
        if document is None:
            try:
                addresses = await asyncio.get_running_loop().getaddrinfo(
                    parsed.hostname,
                    parsed.port or 80,
                    type=socket.SocketKind.SOCK_STREAM,
                )
            except OSError as exc:
                return {"status": "error", "error": f"could not resolve host: {exc}"}

            for family, _, _, _, sockaddr in addresses:
                del family
                ip = ipaddress.ip_address(sockaddr[0])
                if not ip.is_global:
                    return {
                        "status": "error",
                        "blocked": True,
                        "error": f"non-public address is not allowed: {ip}",
                    }
            return {"status": "error", "error": "document not found in local catalog"}

        return {
            "url": document.url,
            "title": document.title,
            "publisher": document.publisher,
            "published_at": document.published_at,
            "content_type": "text/plain",
            "content": document.content,
            "bytes_read": len(document.content.encode("utf-8")),
        }

    async def _calculator(self, payload: dict[str, Any]) -> dict[str, Any]:
        expression = payload.get("expression")
        if not isinstance(expression, str) or not expression.strip():
            return {"status": "error", "error": "expression is required"}

        try:
            value = _evaluate_arithmetic(expression)
        except (SyntaxError, ValueError, ZeroDivisionError, OverflowError) as exc:
            return {"status": "error", "error": f"invalid arithmetic expression: {exc}"}

        if not math.isfinite(value):
            return {"status": "error", "error": "expression must produce a finite number"}
        return {"value": value, "expression": expression}

    def _error(
        self,
        request: ToolRequest,
        message: str,
        started_at: Any,
    ) -> ToolResult:
        return ToolResult(
            request_id=request.request_id,
            attempt_id=request.attempt_id,
            tool=request.tool,
            status="error",
            error=message,
            started_at=started_at,
            completed_at=utc_now(),
        )


def _evaluate_arithmetic(expression: str) -> float:
    tree = ast.parse(expression, mode="eval")
    return float(_evaluate_node(tree.body))


def _evaluate_node(node: ast.AST) -> float | int:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
        left = _evaluate_node(node.left)
        right = _evaluate_node(node.right)
        if type(node.op) is ast.Pow and abs(float(right)) > 100:
            raise ValueError("exponent too large")
        return _BINARY_OPERATORS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPERATORS:
        return _UNARY_OPERATORS[type(node.op)](_evaluate_node(node.operand))
    raise ValueError(f"unsupported expression node: {type(node).__name__}")


__all__ = ["ToolExecutor"]
