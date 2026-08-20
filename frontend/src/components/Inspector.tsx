import type { EventRecord, Run, TaskRecord, WorkerAttempt } from "../types";

function budgetRows(run: Run): Array<{ label: string; used: number; cap: number | null }> {
  return [
    { label: "Model calls", used: run.usage.llm_calls, cap: null },
    { label: "Searches", used: run.usage.search_calls, cap: null },
    {
      label: "Retries",
      used: run.usage.retries,
      cap: run.budget.max_retries_per_task ?? null,
    },
    { label: "Replans", used: run.usage.replans, cap: run.budget.max_replans ?? null },
  ];
}

export default function Inspector({
  run,
  tasks,
  attempts,
  events,
  onClose,
}: {
  run: Run;
  tasks: TaskRecord[];
  attempts: WorkerAttempt[];
  events: EventRecord[];
  onClose: () => void;
}) {
  const attemptsByTask = new Map<string, WorkerAttempt[]>();
  for (const attempt of attempts) {
    const list = attemptsByTask.get(attempt.task_id) ?? [];
    list.push(attempt);
    attemptsByTask.set(attempt.task_id, list);
  }
  const recent = [...events].reverse();

  return (
    <aside className="inspector" aria-label="Research trace">
      <div className="insp-head">
        <b>Research trace</b>
        <span className="spacer" />
        <button className="x" onClick={onClose} aria-label="Close trace">
          ✕
        </button>
      </div>
      <div className="insp-body">
        <section className="insp-sec">
          <h4>Budget used</h4>
          <div className="stat-grid">
            {budgetRows(run).map((row) => (
              <div className="stat" key={row.label}>
                <b>
                  {row.used}
                  {row.cap !== null ? <small>/{row.cap}</small> : null}
                </b>
                <small>{row.label}</small>
              </div>
            ))}
          </div>
        </section>

        <section className="insp-sec">
          <h4>Plan</h4>
          {tasks.length === 0 ? <p className="muted">No tasks planned yet.</p> : null}
          {tasks.map((record) => {
            const taskAttempts = attemptsByTask.get(record.task.task_id) ?? [];
            const latest = taskAttempts[taskAttempts.length - 1];
            return (
              <article className="task-i" key={record.task.task_id}>
                <div className="task-i-top">
                  <span className="tid">{record.task.task_id}</span>
                  <span className={`pill ${record.state}`}>{record.state}</span>
                </div>
                <p>{record.task.question}</p>
                <div className="counts">
                  <span>{latest?.result?.findings.length ?? 0} findings</span>
                  <span>{latest?.result?.sources.length ?? 0} sources</span>
                  <span>
                    {record.attempt_count} attempt{record.attempt_count === 1 ? "" : "s"}
                  </span>
                </div>
                {latest?.result?.summary ? (
                  <p className="task-i-summary">{latest.result.summary}</p>
                ) : null}
              </article>
            );
          })}
        </section>

        <section className="insp-sec">
          <h4>Events</h4>
          {recent.length === 0 ? <p className="muted">No events yet.</p> : null}
          <ol className="log">
            {recent.map((event, index) => (
              <li key={event.event_id} className={index === 0 ? "hi" : ""}>
                <span className="ev">{event.event_type}</span>
                <span className="ts">
                  {new Date(event.timestamp).toLocaleTimeString()}
                  {event.task_id ? ` · ${event.task_id}` : ""}
                </span>
              </li>
            ))}
          </ol>
        </section>
      </div>
    </aside>
  );
}
