import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../api";

export default function RunList() {
  const query = useQuery({
    queryKey: ["runs"],
    queryFn: api.listRuns,
    refetchInterval: 3000,
  });

  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>Recent runs</h2>
        <button onClick={() => query.refetch()} disabled={query.isFetching}>
          {query.isFetching ? "Refreshing…" : "Refresh"}
        </button>
      </div>
      {query.isLoading ? <p>Loading runs…</p> : null}
      {query.isError ? (
        <p className="error">{(query.error as Error).message}</p>
      ) : null}
      {query.data?.length === 0 ? (
        <p className="empty">No research runs yet. Start one to see live orchestration.</p>
      ) : null}
      <div className="run-list">
        {query.data?.map((run) => (
          <Link to={`/runs/${run.run_id}`} key={run.run_id} className="run-row">
            <span className={`status ${run.status}`}>
              {run.status.replace(/_/g, " ")}
            </span>
            <span className="run-goal">{run.goal}</span>
            <span className="run-time">
              {new Date(run.created_at).toLocaleString()}
            </span>
          </Link>
        ))}
      </div>
    </section>
  );
}
