import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, expect, it, vi } from "vitest";
import App from "../App";

const mocks = vi.hoisted(() => ({
  createRun: vi.fn(),
  listRuns: vi.fn(),
}));

vi.mock("../api", () => ({
  api: {
    createRun: mocks.createRun,
    listRuns: mocks.listRuns,
  },
  reportMarkdownUrl: vi.fn(() => "http://localhost:8000/report.md"),
}));

function makeRun(overrides: Record<string, unknown> = {}) {
  return {
    run_id: "run_001",
    goal: "Compare battery chemistries",
    dimensions: [],
    phase: "planning",
    status: "running",
    budget: {},
    usage: {
      llm_calls: 0,
      tool_calls: 0,
      search_calls: 0,
      tokens_used: 0,
      retries: 0,
      replans: 0,
    },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    completed_at: null,
    error: null,
    ...overrides,
  };
}

function renderApp() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <App />
    </QueryClientProvider>,
  );
}

describe("App", () => {
  it("renders the composer and the empty run rail", async () => {
    mocks.listRuns.mockResolvedValue([]);
    renderApp();

    expect(await screen.findByText(/what do you want researched/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/research goal/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /send/i })).toBeDisabled();
    expect(await screen.findByText(/no runs yet/i)).toBeInTheDocument();
  });

  it("submits a research goal with no dimensions preselected", async () => {
    mocks.listRuns.mockResolvedValue([]);
    mocks.createRun.mockResolvedValue(makeRun());
    const user = userEvent.setup();
    renderApp();

    await user.type(
      await screen.findByLabelText(/research goal/i),
      "Compare battery chemistries",
    );
    await user.click(screen.getByRole("button", { name: /send/i }));

    await vi.waitFor(() =>
      expect(mocks.createRun).toHaveBeenCalledWith("Compare battery chemistries", []),
    );
  });

  it("submits the dimensions the user picked, including a custom focus", async () => {
    mocks.listRuns.mockResolvedValue([]);
    mocks.createRun.mockResolvedValue(makeRun());
    const user = userEvent.setup();
    renderApp();

    await user.type(
      await screen.findByLabelText(/research goal/i),
      "Compare battery chemistries",
    );
    await user.click(screen.getByRole("button", { name: "cost" }));
    await user.click(screen.getByRole("button", { name: /add focus/i }));
    await user.type(screen.getByLabelText(/add a focus area/i), "supply chain{Enter}");
    await user.click(screen.getByRole("button", { name: /send/i }));

    await vi.waitFor(() =>
      expect(mocks.createRun).toHaveBeenCalledWith("Compare battery chemistries", [
        "cost",
        "supply chain",
      ]),
    );
  });

  it("stops the user selecting more than two dimensions", async () => {
    mocks.listRuns.mockResolvedValue([]);
    const user = userEvent.setup();
    renderApp();

    await user.click(await screen.findByRole("button", { name: "cost" }));
    await user.click(screen.getByRole("button", { name: "risks" }));

    expect(screen.getByRole("button", { name: "tradeoffs" })).toBeDisabled();
    expect(screen.getByRole("button", { name: /add focus/i })).toBeDisabled();
    expect(screen.getByText(/2 of 2 focus areas/i)).toBeInTheDocument();
  });

  it("lets the user swap a dimension once at the limit", async () => {
    mocks.listRuns.mockResolvedValue([]);
    const user = userEvent.setup();
    renderApp();

    await user.click(await screen.findByRole("button", { name: "cost" }));
    await user.click(screen.getByRole("button", { name: "risks" }));
    await user.click(screen.getByRole("button", { name: "cost" }));

    expect(screen.getByRole("button", { name: "tradeoffs" })).toBeEnabled();
  });
});
