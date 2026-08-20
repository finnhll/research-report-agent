import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api";
import { useRunStream } from "../hooks/useRunStream";
import type { Run, WorkerAttempt } from "../types";
import EventTimeline from "./EventTimeline";
import ReportViewer from "./ReportViewer";
import TaskResult from "./TaskResult";

const PHASE_LABELS: Record<string, string> = {
  created: "Getting started",
  intake_guardrail: "Checking your request",
  planning: "Planning the research",
  plan_repair: "Refining the plan",
  scheduling: "Scheduling research tasks",
  executing: "Researching",
  worker_repair: "Retrying a research step",
  reviewing: "Reviewing findings",
  revising: "Following up on gaps",
  replanning: "Adjusting the plan",
  synthesizing: "Writing your report",
  report_repair: "Refining your report",
  final_guardrail: "Running a final safety check",
  finalizing: "Wrapping up",
  terminal: "Done",
};

const STATUS_LABELS: Record<string, string> = {
  running: "Working",
  complete: "Complete",
  complete_with_caveats: "Complete (with caveats)",
  failed: "Failed",
  blocked: "Blocked",
  cancelled: "Cancelled",
};

function timeAgo(iso: string): string {
  const minutes = Math.floor((Date.now() - new Date(iso).getTime()) / 60000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return new Date(iso).toLocaleDateString();
}

export default function ConversationTurn({ run: initialRun }: { run: Run }) {
  const [detailsOpen, setDetailsOpen] = useState(false);
  const queryClient = useQueryClient();

  const runQuery = useQuery({
    queryKey: ["run", initialRun.run_id],
    queryFn: () => api.getRun(initialRun.run_id),
    initialData: initialRun,
    refetchInterval: (query) => (query.state.data?.status === "running" ? 1500 : false),
  });
  const run = runQuery.data ?? initialRun;
  const active = run.status === "running";
  useRunStream(run.run_id, active);

  const tasksQuery = useQuery({
    queryKey: ["run-data", run.run_id, "tasks"],
    queryFn: () => api.listTasks(run.run_id),
    refetchInterval: active ? 1500 : false,
  });
  const attemptsQuery = useQuery({
    queryKey: ["run-data", run.run_id, "attempts"],
    queryFn: () => api.listAttempts(run.run_id),
    enabled: detailsOpen,
    refetchInterval: active && detailsOpen ? 1500 : false,
  });
  const eventsQuery = useQuery({
    queryKey: ["run-data", run.run_id, "events"],
    queryFn: () => api.listEvents(run.run_id),
    enabled: detailsOpen,
    refetchInterval: active && detailsOpen ? 1500 : false,
  });
  const reportQuery = useQuery({
    queryKey: ["run-data", run.run_id, "report"],
    queryFn: () => api.getReport(run.run_id),
    enabled: !active,
    retry: false,
  });

  const cancel = useMutation({
    mutationFn: () => api.cancelRun(run.run_id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["run", run.run_id] });
      queryClient.invalidateQueries({ queryKey: ["run-data", run.run_id] });
    },
  });

  const tasks = tasksQuery.data ?? [];
  const completedCount = tasks.filter((task) => task.state === "completed").length;
  const attemptsByTask = new Map<string, WorkerAttempt[]>();
  for (const attempt of attemptsQuery.data ?? []) {
    const existing = attemptsByTask.get(attempt.task_id) ?? [];
    existing.push(attempt);
    attemptsByTask.set(attempt.task_id, existing);
  }

  return (
    <div className="chat-turn">
      <div className="chat-message chat-message-user">
        <div className="chat-avatar chat-avatar-user">You</div>
        <div className="chat-bubble">
          <p className="chat-goal">{run.goal}</p>
          {run.dimensions.length ? (
            <div className="chat-dimension-tags">
              {run.dimensions.map((dimension) => (
                <span key={dimension} className="tag">
                  {dimension}
                </span>
              ))}
            </div>
          ) : null}
          <span className="chat-timestamp">{timeAgo(run.created_at)}</span>
        </div>
      </div>

      <div className="chat-message chat-message-assistant">
        <div className="chat-avatar chat-avatar-assistant">R</div>
        <div className="chat-bubble chat-bubble-assistant">
          <div className="chat-status-row">
            <span className={`status ${run.status}`}>
              {STATUS_LABELS[run.status] ?? run.status}
            </span>
            {active ? (
              <>
                <span className="spinner" />
                <span className="working-label">{PHASE_LABELS[run.phase] ?? run.phase}…</span>
                <button
                  className="link-button danger-link"
                  onClick={() => cancel.mutate()}
                  disabled={cancel.isPending}
                >
                  {cancel.isPending ? "Cancelling…" : "Stop"}
                </button>
              </>
            ) : null}
          </div>

          {run.error ? <p className="error">{run.error}</p> : null}

          {active && tasks.length ? (
            <div className="task-chip-row">
              {tasks.map((task) => (
                <span
                  key={task.task.task_id}
                  className={`state-pill ${task.state}`}
                  title={task.task.question}
                >
                  {task.task.task_id.replace("task_", "T")}
                </span>
              ))}
              <span className="muted">
                {completedCount}/{tasks.length} tasks complete
              </span>
            </div>
          ) : null}

          {reportQuery.data ? <ReportViewer report={reportQuery.data} /> : null}
          {!active && reportQuery.isError ? (
            <p className="muted">No report was produced for this run.</p>
          ) : null}

          <button
            type="button"
            className="link-button details-toggle"
            onClick={() => setDetailsOpen((open) => !open)}
          >
            {detailsOpen ? "Hide research trace" : "Show research trace"}
          </button>
          {detailsOpen ? (
            <div className="chat-details">
              <section>
                <h4>Research tasks</h4>
                <div className="task-result-list">
                  {tasks.map((task) => (
                    <TaskResult
                      key={task.task.task_id}
                      record={task}
                      attempts={attemptsByTask.get(task.task.task_id) ?? []}
                    />
                  ))}
                </div>
              </section>
              <section>
                <h4>Event trace</h4>
                <EventTimeline events={eventsQuery.data?.events ?? []} />
              </section>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
