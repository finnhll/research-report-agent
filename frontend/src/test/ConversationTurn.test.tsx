import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, expect, it, vi } from "vitest";
import ConversationTurn from "../components/ConversationTurn";
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
    attempt_timeout_seconds: 240,
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

function renderTurn() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <ConversationTurn run={run} />
    </QueryClientProvider>,
  );
}

describe("ConversationTurn", () => {
  it("renders the goal, the formatted report, and an expandable trace", async () => {
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

    renderTurn();

    expect(await screen.findByText("Compare EV battery chemistries")).toBeInTheDocument();
    expect(await screen.findByText("Battery chemistry comparison")).toBeInTheDocument();
    expect(screen.getByText("Example source")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "[1]" })).toHaveAttribute("href", "#source-1");

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /show research trace/i }));

    expect(await screen.findByText("Identify battery chemistries")).toBeInTheDocument();
    expect(await screen.findByText("Found three relevant sources.")).toBeInTheDocument();
    expect(screen.getByText("run.completed")).toBeInTheDocument();
  });
});
