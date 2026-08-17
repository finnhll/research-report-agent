import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
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

function renderApp() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("App", () => {
  it("renders the new run interface", async () => {
    mocks.listRuns.mockResolvedValue([]);
    renderApp();

    expect(await screen.findByText("Start research")).toBeInTheDocument();
    expect(screen.getByLabelText(/research goal/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /start run/i })).toBeDisabled();
  });

  it("submits a research goal with selected dimensions", async () => {
    mocks.listRuns.mockResolvedValue([]);
    mocks.createRun.mockResolvedValue({ run_id: "run_001" });
    const user = userEvent.setup();
    renderApp();

    await user.type(await screen.findByLabelText(/research goal/i), "Compare battery chemistries");
    await user.click(screen.getByRole("button", { name: /start run/i }));

    await vi.waitFor(() =>
      expect(mocks.createRun).toHaveBeenCalledWith("Compare battery chemistries", [
        "cost",
        "safety",
      ]),
    );
  });
});
