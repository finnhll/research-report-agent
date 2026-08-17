"""FastAPI service for the Research & Report Agent."""

from __future__ import annotations

import asyncio
import json
import os
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from research_report_agent.orchestrator import Orchestrator
from research_report_agent.runtime_contracts import RunRecord, RunStatus
from research_report_agent.storage import Database


class RunCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    goal: str = Field(min_length=3, max_length=2000)
    dimensions: list[str] = Field(default_factory=list, max_length=5)


class EventListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    events: list[dict[str, Any]]


def get_database(request: Request) -> Database:
    return request.app.state.database


DatabaseDep = Annotated[Database, Depends(get_database)]


def create_app(
    *,
    database: Database | None = None,
    orchestrator: Orchestrator | None = None,
) -> FastAPI:
    """Create a configured FastAPI application."""

    if database is None:
        database_path = Path(
            os.getenv("RESEARCH_REPORT_AGENT_DB", ".data/research-report-agent.sqlite3")
        )
        database_path.parent.mkdir(parents=True, exist_ok=True)
        database = Database.sqlite(database_path)

    runtime_orchestrator = orchestrator or Orchestrator(database)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        await database.create_schema()
        try:
            yield
        finally:
            await database.dispose()

    app = FastAPI(
        title="Research & Report Agent",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.database = database
    app.state.orchestrator = runtime_orchestrator

    allowed_origins = [
        origin.strip()
        for origin in os.getenv(
            "RESEARCH_REPORT_AGENT_ALLOWED_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ).split(",")
        if origin.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post(
        "/api/runs",
        response_model=RunRecord,
        status_code=status.HTTP_201_CREATED,
    )
    async def create_run(
        request: RunCreateRequest,
        db: DatabaseDep,
    ) -> RunRecord:
        run_id = f"run_{uuid.uuid4().hex[:16]}"
        run = RunRecord(
            run_id=run_id,
            goal=request.goal,
            dimensions=request.dimensions,
        )
        await db.runs.create(run)
        app.state.orchestrator.start(run_id, request.goal, request.dimensions)
        return run

    @app.get("/api/runs", response_model=list[RunRecord])
    async def list_runs(db: DatabaseDep) -> list[RunRecord]:
        return await db.runs.list()

    @app.get("/api/runs/{run_id}", response_model=RunRecord)
    async def get_run(run_id: str) -> RunRecord:
        run = await app.state.database.runs.get(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")
        return run

    @app.delete("/api/runs/{run_id}", response_model=RunRecord)
    async def cancel_run(
        run_id: str,
    ) -> RunRecord:
        run = await app.state.database.runs.get(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")
        if run.status is not RunStatus.RUNNING:
            raise HTTPException(status_code=409, detail="Run is not active")
        await app.state.orchestrator.cancel(run.run_id)
        updated = await app.state.database.runs.get(run.run_id)
        if updated is None:
            raise HTTPException(status_code=404, detail="Run not found")
        return updated

    @app.get("/api/runs/{run_id}/tasks")
    async def list_tasks(
        run_id: str,
    ) -> list[Any]:
        run = await app.state.database.runs.get(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")
        return await app.state.database.tasks.list(run.run_id)

    @app.get("/api/runs/{run_id}/attempts")
    async def list_attempts(
        run_id: str,
    ) -> list[Any]:
        run = await app.state.database.runs.get(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")
        return await app.state.database.attempts.list(run.run_id)

    @app.get("/api/runs/{run_id}/events", response_model=EventListResponse)
    async def list_events(
        run_id: str,
        after: int = Query(default=0, ge=0),
    ) -> EventListResponse:
        run = await app.state.database.runs.get(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")
        rows = await app.state.database.events.list(run.run_id, after_sequence=after)
        events = []
        for sequence, event in rows:
            payload = event.model_dump(mode="json")
            events.append({"sequence": sequence, **payload})
        return EventListResponse(events=events)

    @app.get("/api/runs/{run_id}/stream")
    async def stream_run(
        run_id: str,
        db: DatabaseDep,
    ) -> Response:
        run = await db.runs.get(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")
        terminal_events = {"run.completed", "run.terminated", "run.cancelled"}
        target_run_id = run.run_id

        async def event_stream() -> AsyncIterator[str]:
            last_sequence = 0
            while True:
                rows = await db.events.list(target_run_id, after_sequence=last_sequence)
                for sequence, event in rows:
                    last_sequence = sequence
                    payload = event.model_dump(mode="json")
                    yield (
                        f"id: {sequence}\n"
                        f"event: {event.event_type}\n"
                        f"data: {json.dumps(payload, separators=(',', ':'))}\n\n"
                    )
                    if event.event_type in terminal_events:
                        return
                await asyncio.sleep(0.15)

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    @app.get("/api/runs/{run_id}/report")
    async def get_report(
        run_id: str,
    ) -> Any:
        run = await app.state.database.runs.get(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")
        report = await app.state.database.reports.get(run.run_id)
        if report is None:
            raise HTTPException(status_code=404, detail="Report not available")
        return report

    @app.get("/api/runs/{run_id}/report.md")
    async def get_report_markdown(
        run_id: str,
    ) -> Response:
        run = await app.state.database.runs.get(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")
        report = await app.state.database.reports.get(run.run_id)
        if report is None:
            raise HTTPException(status_code=404, detail="Report not available")
        return Response(
            content=report.markdown,
            media_type="text/markdown",
            headers={"Content-Disposition": 'inline; filename="report.md"'},
        )

    return app


__all__ = ["RunCreateRequest", "create_app"]
