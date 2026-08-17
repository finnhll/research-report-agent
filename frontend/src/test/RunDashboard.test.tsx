import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import RunDashboard from "../components/RunDashboard";
import type { Report, Run, TaskRecord, WorkerAttempt } from "../types";

const mocks = vi.hoisted(() => ({
  getRun: vi.fn(),
  listTasks: vi.fn(),
  listAttempts: vi.fn(),
  listEvents: vi.fn(),
  getReport: vi.fn(),
  cancelRun: vi.fn(),
}));

vi.mock("../api", () => ({
  api: mocks,
  reportMarkdownUrl: vi.fn(() => "http://localhost:8000/report.md"),
}));

const run: Run = {
  run_id: "run_001",
  goal: "Compare EV battery chemistries",
  dimensions: ["cost", "safety"],
  phase: "terminal",
  status: "complete",
  budget: {
    max_parallel_workers: 3,
    max_reasoning_steps: 10,
    max_tool_calls_per_attempt: 6,
    attempt_timeout_seconds: 10,
    max_retries_per_task: 1,
    max_replans: 1,
  },
  usage: {
    llm_calls: 3,
    tool_calls: 9,
    search_calls: 3,
    tokens_used: 0,
    retries: 0,
    replans: 0,
  },
  created_at: "2026-08-16T00:00:00Z",
  updated_at: "2026-08-16T00:01:00Z",
  completed_at: "2026-08-16T00:01:00Z",
  error: null,
};

const task: TaskRecord = {
  run_id: "run_001",
  plan_id: "plan_001",
  plan_version: 1,
  task: {
    task_id: "task_001",
    question: "Identify battery chemistries",
    success_criteria: ["Identify three chemistries"],
    required_tools: ["web_search"],
    priority: "high",
    dependencies: [],
  },
  state: "completed",
  attempt_count: 1,
  produced_context: {},
};

const attempt: WorkerAttempt = {
  run_id: "run_001",
  plan_id: "plan_001",
  plan_version: 1,
  task_id: "task_001",
  attempt_id: "task_001_attempt_001",
  attempt_kind: "initial",
  state: "completed",
  started_at: "2026-08-16T00:00:01Z",
  completed_at: "2026-08-16T00:00:02Z",
  result: {
    task_id: "task_001",
    status: "completed",
    summary: "Found three relevant sources.",
    findings: [{}, {}],
    sources: [{}, {}, {}],
    gaps: [],
  },
  error: null,
};

const report: Report = {
  report_id: "report_001",
  run_id: "run_001",
  title: "Battery chemistry comparison",
  markdown: "# Battery chemistry comparison",
  structured: {
    executive_summary: "Evidence-based comparison of battery options.",
    sections: [{ heading: "Cost", markdown: "Cost tradeoffs differ by chemistry." }],
    comparison_table_markdown: "| Option | Evidence |",
    conclusions: [
      { conclusion: "Options involve tradeoffs", confidence: 0.75, basis: [] },
    ],
    limitations: ["Local deterministic evidence"],
    sources: [
      {
        source_id: "src_001",
        title: "Example source",
        url: "https://example.com",
        publisher: "Example publisher",
        published_at: null,
        retrieved_at: "2026-08-16T00:00:00Z",
        credibility: "medium-high",
        notes: null,
      },
    ],
  },
  guardrail_verdict: "allow",
  created_at: "2026-08-16T00:01:00Z",
};

function renderDashboard() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={["/runs/run_001"]}>
        <Routes>
          <Route path="/runs/:runId" element={<RunDashboard />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("RunDashboard", () => {
  it("renders tasks, attempts, trace, and report", async () => {
    mocks.getRun.mockResolvedValue(run);
    mocks.listTasks.mockResolvedValue([task]);
    mocks.listAttempts.mockResolvedValue([attempt]);
    mocks.listEvents.mockResolvedValue({
      events: [
        {
          sequence: 1,
          event_id: "event_001",
          run_id: "run_001",
          event_type: "run.completed",
          timestamp: "2026-08-16T00:01:00Z",
          task_id: null,
          attempt_id: null,
          data: {},
        },
      ],
    });
    mocks.getReport.mockResolvedValue(report);

    renderDashboard();

    expect(await screen.findByText("Compare EV battery chemistries")).toBeInTheDocument();
    expect(await screen.findByText("Identify battery chemistries")).toBeInTheDocument();
    expect(await screen.findByText("Found three relevant sources.")).toBeInTheDocument();
    expect(await screen.findByText("Battery chemistry comparison")).toBeInTheDocument();
    expect(screen.getByText("run.completed")).toBeInTheDocument();
    expect(screen.getByText("Example source")).toBeInTheDocument();
  });
});
