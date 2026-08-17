from __future__ import annotations

from httpx import ASGITransport, AsyncClient

from research_report_agent.api import create_app
from research_report_agent.storage import Database


async def make_client() -> tuple[AsyncClient, object]:
    database = Database.in_memory()
    await database.create_schema()
    app = create_app(database=database)
    client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    return client, app.state


async def test_health_endpoint() -> None:
    client, _ = await make_client()
    async with client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_create_run_validates_goal() -> None:
    client, _ = await make_client()
    async with client:
        response = await client.post("/api/runs", json={"goal": ""})

    assert response.status_code == 422


async def test_full_run_api_round_trip() -> None:
    client, state = await make_client()
    async with client:
        created = await client.post(
            "/api/runs",
            json={
                "goal": "Compare EV battery chemistries for cost and safety",
                "dimensions": ["cost", "safety"],
            },
        )
        run_id = created.json()["run_id"]
        await state.orchestrator.wait(run_id)

        run = await client.get(f"/api/runs/{run_id}")
        tasks = await client.get(f"/api/runs/{run_id}/tasks")
        attempts = await client.get(f"/api/runs/{run_id}/attempts")
        events = await client.get(f"/api/runs/{run_id}/events")
        report = await client.get(f"/api/runs/{run_id}/report")
        markdown = await client.get(f"/api/runs/{run_id}/report.md")

    assert created.status_code == 201
    assert run.json()["status"] == "complete"
    assert len(tasks.json()) == 3
    assert len(attempts.json()) == 3
    assert events.json()["events"]
    assert report.json()["guardrail_verdict"] == "allow"
    assert "## Sources" in markdown.text


async def test_unknown_run_returns_404() -> None:
    client, _ = await make_client()
    async with client:
        response = await client.get("/api/runs/run_missing")

    assert response.status_code == 404


async def test_sse_stream_ends_after_terminal_event() -> None:
    client, state = await make_client()
    async with client:
        created = await client.post(
            "/api/runs",
            json={
                "goal": "Compare EV battery chemistries for cost and safety",
                "dimensions": ["cost", "safety"],
            },
        )
        run_id = created.json()["run_id"]
        await state.orchestrator.wait(run_id)
        response = await client.get(f"/api/runs/{run_id}/stream")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "event: run.phase.changed" in response.text
    assert "event: run.completed" in response.text


async def test_cancel_run() -> None:
    client, state = await make_client()
    async with client:
        created = await client.post(
            "/api/runs",
            json={"goal": "Compare technologies", "dimensions": ["cost"]},
        )
        run_id = created.json()["run_id"]
        await state.orchestrator.cancel(run_id)
        response = await client.delete(f"/api/runs/{run_id}")

    assert response.status_code == 409
    assert response.json()["detail"] == "Run is not active"
