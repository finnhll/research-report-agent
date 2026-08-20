from __future__ import annotations

import asyncio

from httpx import ASGITransport, AsyncClient
from tests.fakes import StubWorkerRuntime, happy_path_llm_factory

from research_report_agent.api import create_app
from research_report_agent.orchestrator import Orchestrator
from research_report_agent.storage import Database

TASK_IDS = ["task_001", "task_002", "task_003"]


async def make_client() -> tuple[AsyncClient, object]:
    database = Database.in_memory()
    await database.create_schema()
    orchestrator = Orchestrator(
        database,
        happy_path_llm_factory(TASK_IDS),
        worker_runtime=StubWorkerRuntime(),
    )
    app = create_app(database=database, orchestrator=orchestrator)
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


async def test_list_model_providers() -> None:
    client, _ = await make_client()
    async with client:
        response = await client.get("/api/model-providers")

    assert response.status_code == 200
    body = response.json()
    ids = {item["id"] for item in body}
    assert ids == {"openai", "deepseek", "anthropic"}
    deepseek = next(item for item in body if item["id"] == "deepseek")
    assert deepseek["base_url"] == "https://api.deepseek.com"
    assert "deepseek-v4-flash" in deepseek["models"]


async def test_get_model_config_defaults() -> None:
    client, _ = await make_client()
    async with client:
        response = await client.get("/api/model-config")

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "openai"
    assert body["model"] == "gpt-4o-mini"
    assert body["api_key_masked"] is None


async def test_update_model_config_masks_the_key() -> None:
    client, _ = await make_client()
    async with client:
        response = await client.post(
            "/api/model-config",
            json={
                "model": "gpt-4.1",
                "base_url": "https://gateway.example.com/v1",
                "api_key": "sk-test-secret",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["model"] == "gpt-4.1"
    assert body["base_url"] == "https://gateway.example.com/v1"
    assert body["api_key_masked"] is not None
    assert "sk-test-secret" not in response.text


async def test_update_model_config_switches_provider() -> None:
    client, _ = await make_client()
    async with client:
        response = await client.post(
            "/api/model-config",
            json={"provider": "anthropic", "model": "claude-opus-5", "api_key": "sk-ant-test"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "anthropic"
    assert body["model"] == "claude-opus-5"


async def test_update_model_config_rejects_bad_base_url() -> None:
    client, _ = await make_client()
    async with client:
        response = await client.post("/api/model-config", json={"base_url": "not-a-url"})

    assert response.status_code == 400


async def test_test_model_config_without_key() -> None:
    client, _ = await make_client()
    async with client:
        response = await client.post("/api/model-config/test")

    assert response.status_code == 200
    assert response.json() == {"ok": False, "error": "No API key configured"}


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


async def test_cancel_active_run_through_http() -> None:
    class SlowWorkerRuntime(StubWorkerRuntime):
        async def execute_attempt(self, request, *, cancel_event=None):  # type: ignore[no-untyped-def]
            await asyncio.sleep(30)
            raise AssertionError("Slow worker should be cancelled")

    database = Database.in_memory()
    await database.create_schema()
    orchestrator = Orchestrator(
        database,
        happy_path_llm_factory(TASK_IDS),
        worker_runtime=SlowWorkerRuntime(),
    )
    app = create_app(database=database, orchestrator=orchestrator)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        created = await client.post(
            "/api/runs",
            json={"goal": "Compare technologies", "dimensions": ["cost"]},
        )
        run_id = created.json()["run_id"]

        for _ in range(100):
            await asyncio.sleep(0.01)
            tasks = await database.tasks.list(run_id)
            if tasks and tasks[0].state.value == "running":
                break
        else:
            raise AssertionError("Worker did not start")

        response = await client.delete(f"/api/runs/{run_id}")

        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"
        assert (await database.tasks.list(run_id))[0].state.value == "cancelled"
