# Fullstack Research & Report Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the approved Python/LangGraph orchestrator-workers backend, FastAPI service, React frontend, tests, and browser-ready end-to-end workflow.

**Architecture:** FastAPI owns external requests and persistence. An async orchestrator owns run state, scheduling, retries, budgets, events, cancellation, and terminal outcomes. Workers execute one bounded ReAct attempt and return typed results. React consumes REST plus SSE and never contacts model providers or tools directly.

**Tech Stack:** Python 3.11, LangGraph, FastAPI, Pydantic, SQLAlchemy async SQLite, pytest, React, TypeScript, Vite, TanStack Query, React Router, Vitest, Testing Library.

**Spec:** `docs/spec/design.md`

## Global Constraints

- Default backend port: `8000`.
- Default frontend dev port: `5173`.
- Runtime mode defaults to deterministic local agents and tools.
- External model/search credentials must come from environment variables.
- Frontend must not call model or tool providers directly.
- Orchestrator is the sole owner of shared state and transitions.
- Every worker attempt is immutable and identity-bound.
- Worker loops enforce reasoning-step, tool-call, and timeout limits.
- Every run reaches `complete`, `complete_with_caveats`, `failed`, `blocked`, or `cancelled`.
- All backend schemas reject undeclared fields.
- All API list endpoints are ordered deterministically.
- CI must run backend lint/tests and frontend typecheck/tests/build.

---

### Task 1: Runtime contracts

**Files:**
- Modify: `src/research_report_agent/contracts.py`
- Create: `src/research_report_agent/runtime_contracts.py`
- Test: `tests/test_runtime_contracts.py`

**Interfaces:**
- Produces `RunPhase`, `RunStatus`, `TaskState`, `WorkerAttempt`, `WorkerAttemptRequest`, `RunBudget`, `RunUsage`, `AgentEvent`, `ToolRequest`, `ToolResult`, `ReportDocument`

- [ ] Write failing tests for:
  - Phase/status/task-state enum values
  - Budget limits
  - Immutable worker attempt IDs
  - Tool result timestamps
  - Event payload shape
- [ ] Implement strict Pydantic runtime models.
- [ ] Run `pytest tests/test_runtime_contracts.py -q`.
- [ ] Commit: `feat: add runtime contracts`

### Task 2: Persistence

**Files:**
- Create: `src/research_report_agent/storage.py`
- Test: `tests/test_storage.py`

**Interfaces:**
- Produces `Database`
- Produces `RunRepository.create_run`
- Produces `RunRepository.list_runs`
- Produces `RunRepository.get_run`
- Produces `RunRepository.set_terminal_state`
- Produces `TaskRepository.replace_tasks`
- Produces `AttemptRepository.add_result`
- Produces `EventRepository.append`
- Produces `ReportRepository.save`

- [ ] Write failing tests using an in-memory SQLite database.
- [ ] Implement async SQLAlchemy models and repositories.
- [ ] Enforce unique run/task/attempt IDs.
- [ ] Store JSON payloads as normalized JSON strings.
- [ ] Run `pytest tests/test_storage.py -q`.
- [ ] Commit: `feat: add persistent run storage`

### Task 3: Deterministic agent tools

**Files:**
- Create: `src/research_report_agent/tools.py`
- Test: `tests/test_tools.py`

**Interfaces:**
- Produces `ToolExecutor.execute(request: ToolRequest) -> ToolResult`
- Supports tool names `web_search`, `fetch_page`, `calculator`

- [ ] Write tests for successful search, fetch, calculator, invalid input, unknown tool, timeout, and call limits.
- [ ] Implement deterministic local search corpus.
- [ ] Implement URL parsing and SSRF blocking for loopback/private/link-local/reserved addresses.
- [ ] Implement deterministic arithmetic parser without `eval`.
- [+- ] Run `pytest tests/test_tools.py -q`.
- [ ] Commit: `feat: add bounded worker tools`

### Task 4: Worker ReAct runtime

**Files:**
- Create: `src/research_report_agent/worker_runtime.py`
- Test: `tests/test_worker_runtime.py`

**Interfaces:**
- Produces `WorkerRuntime.execute_attempt(request: WorkerAttemptRequest) -> WorkerResult`

- [ ] Write tests for completion, partial result, tool exhaustion, invalid output, and cancellation.
- [ ] Implement bounded loop:
  - Assess evidence
  - Select next tool
  - Execute typed request
  - Sanitize observation
  - Enforce limits
  - Return structured result
- [ ] Run `pytest tests/test_worker_runtime.py -q`.
- [ ] Commit: `feat: add worker react runtime`

### Task 5: Agents

**Files:**
- Create: `src/research_report_agent/agents/__init__.py`
- Create: `src/research_report_agent/agents/guardrail.py`
- Create: `src/research_report_agent/agents/planner.py`
- Create: `src/research_report_agent/agents/critic.py`
- Create: `src/research_report_agent/agents/synthesizer.py`
- Test: `tests/test_agents.py`

**Interfaces:**
- Produces `IntakeGuardrail.review(goal: str) -> GuardrailReview`
- Produces `Planner.create_plan(goal: str, dimensions: list[str]) -> ResearchPlan`
- Produces `Critic.review(results: list[WorkerResult]) -> CriticReview`
- Produces `Synthesizer.synthesize(...) -> ReportDocument`

- [ ] Write deterministic tests for safe/unsafe intake, valid plan, weak result revision, and cited synthesis.
- [ ] Implement deterministic local MVP agents with typed outputs.
- [ ] Ensure synthesizer uses accepted findings only.
- [ ] Commit: `feat: add typed agent nodes`

### Task 6: Orchestrator supervisor

**Files:**
- Create: `src/research_report_agent/orchestrator.py`
- Test: `tests/test_orchestrator.py`

**Interfaces:**
- Produces `Orchestrator.start(run_id, goal, dimensions)`
- Produces `Orchestrator.cancel(run_id)`

- [ ] Write tests for successful run, unsafe input, partial failure, cancellation, and terminal state.
- [ ] Implement async supervisor loop with:
  - Intake guardrail
  - Planning
  - Dependency scheduling
  - Bounded parallel dispatch
  - Immutable attempt persistence
  - Critic
  - Synthesizer
  - Final guardrail
  - Event emission
  - Terminal transitions
- [ ] Commit: `feat: add orchestrator supervisor`

### Task 7: FastAPI application

**Files:**
- Create: `src/research_report_agent/api.py`
- Create: `src/research_report_agent/main.py`
- Test: `tests/test_api.py`

**Interfaces:**
- Produces `create_app(database: Database | None = None) -> FastAPI`
- Exposes `/health`
- Exposes `/api/runs`
- Exposes `/api/runs/{run_id}`
- Exposes `/api/runs/{run_id}/tasks`
- Exposes `/api/runs/{run_id}/attempts`
- Exposes `/api/runs/{run_id}/events`
- Exposes `/api/runs/{run_id}/stream`
- Exposes `/api/runs/{run_id}/report`
- Exposes `/api/runs/{run_id}/report.md`

- [ ] Write API tests with `httpx.AsyncClient`.
- [ ] Implement Pydantic request/response schemas.
- [ ] Implement SSE event stream from persisted events plus live subscriber queue.
- [ ] Implement cancellation.
- [ ] Commit: `feat: add fastapi service`

### Task 8: Frontend foundation

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/api.ts`
- Create: `frontend/src/types.ts`
- Create: `frontend/src/styles.css`

**Interfaces:**
- Produces `api.createRun`
- Produces `api.listRuns`
- Produces `api.getRun`
- Produces `api.listTasks`
- Produces `api.listAttempts`
- Produces `api.listEvents`
- Produces `api.getReport`
- Produces `api.cancelRun`

- [ ] Add React/Vite/TypeScript dependencies and scripts.
- [ ] Implement typed API client.
- [ ] Implement routes `/` and `/runs/:runId`.
- [ ] Commit: `feat: add react frontend foundation`

### Task 9: Frontend run dashboard

**Files:**
- Create: `frontend/src/components/NewRunForm.tsx`
- Create: `frontend/src/components/RunList.tsx`
- Create: `frontend/src/components/RunDashboard.tsx`
- Create: `frontend/src/components/TaskCard.tsx`
- Create: `frontend/src/components/AttemptCard.tsx`
- Create: `frontend/src/components/EventTimeline.tsx`
- Create: `frontend/src/hooks/useRunStream.ts`

**Interfaces:**
- Produces live run refresh through SSE.
- Produces cancellation action.
- Produces task/attempt/event rendering.

- [ ] Implement form validation and submission.
- [ ] Implement status/phase badges.
- [ ] Implement live event stream and query invalidation.
- [ ] Implement report and trace sections.
- [ ] Commit: `feat: add live run dashboard`

### Task 10: Report viewer

**Files:**
- Create: `frontend/src/components/ReportViewer.tsx`
- Create: `frontend/src/components/SourceList.tsx`

**Interfaces:**
- Renders structured report.
- Downloads Markdown from backend.

- [ ] Render executive summary, sections, comparison table, conclusions, confidence, limitations, and sources.
- [ ] Add Markdown download/copy actions.
- [ ] Commit: `feat: add report viewer`

### Task 11: Frontend tests

**Files:**
- Create: `frontend/src/test/setup.ts`
- Create: `frontend/src/test/App.test.tsx`
- Create: `frontend/src/test/RunDashboard.test.tsx`
- Create: `frontend/vitest.config.ts`

- [ ] Test run creation form.
- [ ] Test dashboard rendering.
- [ ] Test SSE refresh.
- [ ] Test report viewer.
- [ ] Commit: `test: add frontend coverage`

### Task 12: CI and documentation

**Files:**
- Modify: `.github/workflows/ci.yml`
- Modify: `README.md`
- Modify: `pyproject.toml`

- [ ] Add backend dependencies: `fastapi`, `uvicorn`, `sqlalchemy`, `aiosqlite`, `httpx`.
- [ ] Add frontend scripts: `typecheck`, `test`, `build`.
- [ ] Add CI frontend job.
- [ ] Document local setup and API surface.
- [ ] Commit: `ci: validate fullstack application`

### Task 13: End-to-end verification

**Files:**
- Create: `scripts/dev.sh`

- [ ] Start backend and frontend.
- [ ] Create a run through the UI.
- [ ] Verify SSE progress.
- [ ] Verify final report.
- [ ] Verify cancellation endpoint.
- [ ] Run all checks:

```bash
.venv/bin/ruff format --check .
.venv/bin/ruff check .
.venv/bin/pytest -q
cd frontend && npm run typecheck && npm run test -- --run && npm run build
```

- [ ] Commit: `test: verify fullstack workflow`

### Task 14: Pull request

- [ ] Push `feat/fullstack-agent-platform`.
- [ ] Open PR into `main`.
- [ ] Confirm CI passes.
- [ ] Provide browser and API verification summary.
