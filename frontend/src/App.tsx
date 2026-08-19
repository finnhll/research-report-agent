import { useState } from "react";
import { Route, Routes } from "react-router-dom";
import RunDashboard from "./components/RunDashboard";
import ModelSettings from "./components/ModelSettings";
import NewRunForm from "./components/NewRunForm";
import RunList from "./components/RunList";

export default function App() {
  const [settingsOpen, setSettingsOpen] = useState(false);

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">Orchestrator + worker agents</p>
          <h1>Research &amp; Report Agent</h1>
        </div>
        <div className="button-row">
          <span className="stack-badge">Python · LangGraph · FastAPI · React</span>
          <button onClick={() => setSettingsOpen((open) => !open)}>⚙ Model API</button>
        </div>
      </header>
      {settingsOpen ? (
        <div className="home-layout" style={{ gridTemplateColumns: "1fr", maxWidth: 1280, margin: "0 auto 20px" }}>
          <ModelSettings onClose={() => setSettingsOpen(false)} />
        </div>
      ) : null}
      <main>
        <Routes>
          <Route
            path="/"
            element={
              <section className="home-layout">
                <NewRunForm />
                <RunList />
              </section>
            }
          />
          <Route path="/runs/:runId" element={<RunDashboard />} />
        </Routes>
      </main>
    </div>
  );
}
