import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./api";
import ChatComposer from "./components/ChatComposer";
import ConversationTurn from "./components/ConversationTurn";
import ModelSettings from "./components/ModelSettings";

export default function App() {
  const [settingsOpen, setSettingsOpen] = useState(false);
  const queryClient = useQueryClient();

  const runsQuery = useQuery({
    queryKey: ["runs"],
    queryFn: api.listRuns,
    refetchInterval: 4000,
  });

  const createRun = useMutation({
    mutationFn: ({ goal, dimensions }: { goal: string; dimensions: string[] }) =>
      api.createRun(goal, dimensions),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["runs"] });
    },
  });

  const runs = [...(runsQuery.data ?? [])].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
  );

  return (
    <div className="app-shell chat-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">Orchestrator + worker agents</p>
          <h1>Research &amp; Report Agent</h1>
        </div>
        <div className="button-row">
          <button onClick={() => setSettingsOpen((open) => !open)}>⚙ Model API</button>
        </div>
      </header>

      {settingsOpen ? (
        <div className="settings-wrap">
          <ModelSettings onClose={() => setSettingsOpen(false)} />
        </div>
      ) : null}

      <main className="chat-main">
        <ChatComposer
          submitting={createRun.isPending}
          onSubmit={(goal, dimensions) => createRun.mutate({ goal, dimensions })}
        />
        {createRun.isError ? (
          <p className="error composer-error">{(createRun.error as Error).message}</p>
        ) : null}

        <div className="chat-feed">
          {runsQuery.isLoading ? <p className="muted">Loading…</p> : null}
          {runsQuery.isError ? (
            <p className="error">{(runsQuery.error as Error).message}</p>
          ) : null}
          {runs.length === 0 && !runsQuery.isLoading ? (
            <p className="empty chat-empty">
              Ask a research question above to see the agent plan, research, and report
              back — right here.
            </p>
          ) : null}
          {runs.map((run) => (
            <ConversationTurn key={run.run_id} run={run} />
          ))}
        </div>
      </main>
    </div>
  );
}
