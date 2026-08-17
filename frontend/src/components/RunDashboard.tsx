import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api";
import { useRunStream } from "../hooks/useRunStream";
import AttemptCard from "./AttemptCard";
import EventTimeline from "./EventTimeline";
import ReportViewer from "./ReportViewer";
import TaskCard from "./TaskCard";

export default function RunDashboard() {
  const { runId = "" } = useParams();
  const queryClient = useQueryClient();
  const runQuery = useQuery({
    queryKey: ["run", runId],
    queryFn: () => api.getRun(runId),
    refetchInterval: (query) =>
      query.state.data?.status === "running" ? 1000 : false,
  });
  const run = runQuery.data;
  const active = run?.status === "running";
  useRunStream(runId, active);

  const tasksQuery = useQuery({
    queryKey: ["run-data", runId, "tasks"],
    queryFn: () => api.listTasks(runId),
    enabled: Boolean(run),
    refetchInterval: active ? 1000 : false,
  });
  const attemptsQuery = useQuery({
    queryKey: ["run-data", runId, "attempts"],
    queryFn: () => api.listAttempts(runId),
    enabled: Boolean(run),
    refetchInterval: active ? 1000 : false,
  });
  const eventsQuery = useQuery({
    queryKey: ["run-data", runId, "events"],
    queryFn: () => api.listEvents(runId),
    enabled: Boolean(run),
    refetchInterval: active ? 1000 : false,
  });
  const reportQuery = useQuery({
    queryKey: ["run-data", runId, "report"],
    queryFn: () => api.getReport(runId),
    enabled: run !== undefined && !active,
    retry: false,
  });
  const cancel = useMutation({
    mutationFn: () => api.cancelRun(runId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["run", runId] });
      queryClient.invalidateQueries({ queryKey: ["run-data", runId] });
    },
  });

  if (runQuery.isLoading) return <p className="panel">Loading run…</p>;
  if (runQuery.isError) {
    return <p className="panel error">{(runQuery.error as Error).message}</p>;
  }
  if (!run) return <p className="panel">Run not found.</p>;

  return (
    <div className="dashboard">
      <section className="panel run-summary">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">{run.run_id}</p>
            <h2>{run.goal}</h2>
          </div>
          <div className="button-row">
            <Link className="button" to="/">
              New run
            </Link>
            {active ? (
              <button
                className="danger"
                onClick={() => cancel.mutate()}
                disabled={cancel.isPending}
              >
                {cancel.isPending ? "Cancelling…" : "Cancel"}
              </button>
            ) : null}
          </div>
        </div>
        <div className="status-grid">
          <span className={`status ${run.status}`}>
            {run.status.replace(/_/g, " ")}
          </span>
          <span>phase: {run.phase.replace(/_/g, " ")}</span>
          <span>LLM calls: {run.usage.llm_calls}</span>
          <span>tool calls: {run.usage.tool_calls}</span>
          <span>workers parallel limit: {run.budget.max_parallel_workers}</span>
          <span>replans: {run.usage.replans}</span>
        </div>
        {run.error ? <p className="error">{run.error}</p> : null}
      </section>

      <div className="dashboard-grid">
        <section className="panel">
          <h2>Tasks</h2>
          <div className="task-list">
            {tasksQuery.data?.map((task) => (
              <TaskCard key={task.task.task_id} record={task} />
            ))}
          </div>
        </section>
        <section className="panel">
          <h2>Worker attempts</h2>
          <div className="task-list">
            {attemptsQuery.data?.map((attempt) => (
              <AttemptCard key={attempt.attempt_id} attempt={attempt} />
            ))}
          </div>
        </section>
      </div>

      <section className="panel">
        <h2>Event trace</h2>
        <EventTimeline events={eventsQuery.data?.events ?? []} />
      </section>

      {reportQuery.data ? <ReportViewer report={reportQuery.data} /> : null}
      {reportQuery.isError && !active ? (
        <p className="panel muted">No report was produced for this run.</p>
      ) : null}
    </div>
  );
}
