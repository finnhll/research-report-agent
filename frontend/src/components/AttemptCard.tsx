import type { WorkerAttempt } from "../types";

export default function AttemptCard({ attempt }: { attempt: WorkerAttempt }) {
  return (
    <article className="attempt-card">
      <div className="card-title-row">
        <span className={`state-pill ${attempt.state}`}>{attempt.state}</span>
        <span className="task-id">{attempt.attempt_id}</span>
      </div>
      <p>{attempt.result?.summary ?? attempt.error ?? "Waiting for result…"}</p>
      <div className="metric-row">
        <span>{attempt.result?.findings.length ?? 0} findings</span>
        <span>{attempt.result?.sources.length ?? 0} sources</span>
        <span>{attempt.attempt_kind.replace(/_/g, " ")}</span>
      </div>
    </article>
  );
}
