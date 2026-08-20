import { useState } from "react";
import type { TaskRecord, WorkerAttempt } from "../types";
import AttemptCard from "./AttemptCard";

export default function TaskResult({
  record,
  attempts,
}: {
  record: TaskRecord;
  attempts: WorkerAttempt[];
}) {
  const [expanded, setExpanded] = useState(false);
  const latest = attempts[attempts.length - 1];
  const findings = latest?.result?.findings.length ?? 0;
  const sources = latest?.result?.sources.length ?? 0;

  return (
    <article className="task-result">
      <button
        type="button"
        className="task-result-toggle"
        onClick={() => setExpanded((open) => !open)}
        aria-expanded={expanded}
      >
        <span className={`state-pill ${record.state}`}>{record.state}</span>
        <span className="task-result-question">{record.task.question}</span>
        <span className="task-result-meta">
          {latest ? `${findings} findings · ${sources} sources` : "no attempts yet"}
        </span>
        <span className={`task-result-chevron ${expanded ? "open" : ""}`} aria-hidden="true">
          ›
        </span>
      </button>
      {expanded ? (
        <div className="task-result-body">
          <dl>
            <div>
              <dt>Priority</dt>
              <dd>{record.task.priority}</dd>
            </div>
            <div>
              <dt>Dependencies</dt>
              <dd>
                {record.task.dependencies.length ? record.task.dependencies.join(", ") : "none"}
              </dd>
            </div>
            <div>
              <dt>Attempts</dt>
              <dd>{record.attempt_count}</dd>
            </div>
          </dl>
          <div className="task-list">
            {attempts.map((attempt) => (
              <AttemptCard key={attempt.attempt_id} attempt={attempt} />
            ))}
          </div>
        </div>
      ) : null}
    </article>
  );
}
