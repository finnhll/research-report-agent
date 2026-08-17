import type { TaskRecord } from "../types";

export default function TaskCard({ record }: { record: TaskRecord }) {
  return (
    <article className={`task-card ${record.state}`}>
      <div className="card-title-row">
        <span className={`state-pill ${record.state}`}>{record.state}</span>
        <span className="task-id">{record.task.task_id}</span>
      </div>
      <p>{record.task.question}</p>
      <dl>
        <div>
          <dt>Attempts</dt>
          <dd>{record.attempt_count}</dd>
        </div>
        <div>
          <dt>Priority</dt>
          <dd>{record.task.priority}</dd>
        </div>
        <div>
          <dt>Dependencies</dt>
          <dd>
            {record.task.dependencies.length
              ? record.task.dependencies.join(", ")
              : "none"}
          </dd>
        </div>
      </dl>
    </article>
  );
}
