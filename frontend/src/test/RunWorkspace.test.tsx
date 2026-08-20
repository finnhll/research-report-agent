import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, expect, it, vi } from "vitest";
import RunWorkspace from "../components/RunWorkspace";
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
  API_BASE: "http://localhost:8000",
}));

const run: Run = {
  run_id: "run_001",
  goal: "Compare EV battery chemistries",
  dimensions: ["cost", "risks"],
  phase: "terminal",
  status: "complete",
  budget: { max_retries_per_task: 1, max_replans: 1 },
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
    executive_summary: "Evidence-based comparison of battery options [1].",
    sections: [{ heading: "Cost", markdown: "Cost tradeoffs differ by chemistry." }],
    comparison_table_markdown: "| Option | Evidence |\n|---|---|\n| LFP | Cheaper |",
    conclusions: [{ conclusion: "Options involve tradeoffs", confidence: 0.75, basis: [] }],
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

function renderWorkspace(overrides: Partial<Run> = {}, traceOpen = false) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <RunWorkspace
        run={{ ...run, ...overrides }}
        traceOpen={traceOpen}
        onToggleTrace={() => {}}
        onToggleRail={() => {}}
      />
    </QueryClientProvider>,
  );
}

describe("RunWorkspace", () => {
  it("renders the goal, focus tags, and the cited report", async () => {
    mocks.getRun.mockResolvedValue(run);
    mocks.listTasks.mockResolvedValue([task]);
    mocks.listAttempts.mockResolvedValue([attempt]);
    mocks.listEvents.mockResolvedValue({ events: [] });
    mocks.getReport.mockResolvedValue(report);

    renderWorkspace();

    expect(await screen.findByTitle("Compare EV battery chemistries")).toBeInTheDocument();
    expect(await screen.findByText("Battery chemistry comparison")).toBeInTheDocument();
    expect(screen.getByText("Example source")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "[1]" })).toHaveAttribute("href", "#source-1");
    // the run's focus areas are shown back to the user
    expect(screen.getByText("cost")).toBeInTheDocument();
    expect(screen.getByText("risks")).toBeInTheDocument();
  });

  it("maps the backend phase onto the five human stages", async () => {
    mocks.getRun.mockResolvedValue({ ...run, phase: "executing", status: "running" });
    mocks.listTasks.mockResolvedValue([task]);
    mocks.listAttempts.mockResolvedValue([attempt]);
    mocks.listEvents.mockResolvedValue({ events: [] });

    renderWorkspace({ phase: "executing", status: "running" });

    for (const stage of ["Check", "Plan", "Research", "Review", "Write"]) {
      expect(await screen.findByText(stage)).toBeInTheDocument();
    }
    // the worker's real question is shown, not an opaque task id
    expect(await screen.findByText("Identify battery chemistries")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /stop/i })).toBeInTheDocument();
  });

  it("explains a blocked run instead of showing a raw error", async () => {
    mocks.getRun.mockResolvedValue(run);
    mocks.listTasks.mockResolvedValue([]);
    mocks.listAttempts.mockResolvedValue([]);
    mocks.listEvents.mockResolvedValue({ events: [] });
    mocks.getReport.mockRejectedValue(new Error("no report"));

    renderWorkspace({ status: "blocked", error: "Personal data gathering is refused." });

    expect(await screen.findByText(/this one didn't run/i)).toBeInTheDocument();
    expect(screen.getByText(/personal data gathering is refused/i)).toBeInTheDocument();
  });

  it("shows the trace inspector when it is open", async () => {
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

    renderWorkspace({}, true);

    expect(await screen.findByText("run.completed")).toBeInTheDocument();
    expect(await screen.findByText("Found three relevant sources.")).toBeInTheDocument();
    expect(screen.getByText("task_001")).toBeInTheDocument();
  });
});
