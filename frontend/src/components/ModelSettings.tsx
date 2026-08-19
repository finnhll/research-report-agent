import { useEffect, useState } from "react";
import { api } from "../api";
import type { ModelConfigInfo } from "../types";

export default function ModelSettings({ onClose }: { onClose: () => void }) {
  const [info, setInfo] = useState<ModelConfigInfo | null>(null);
  const [model, setModel] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [busy, setBusy] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testMessage, setTestMessage] = useState<{ ok: boolean; text: string } | null>(null);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getModelConfig()
      .then((config) => {
        setInfo(config);
        setModel(config.model);
        setBaseUrl(config.base_url ?? "");
      })
      .catch(() => setError("Failed to load model configuration"));
  }, []);

  async function save() {
    setBusy(true);
    setError(null);
    setSaved(false);
    try {
      const config = await api.saveModelConfig({
        model,
        base_url: baseUrl,
        api_key: apiKey || undefined,
      });
      setInfo(config);
      setApiKey("");
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function test() {
    setTesting(true);
    setTestMessage(null);
    try {
      const result = await api.testModelConfig();
      if (!result.ok) {
        setTestMessage({ ok: false, text: result.error ?? "Connection failed" });
      } else if (result.model_found) {
        setTestMessage({ ok: true, text: `Connection OK — model "${result.model}" found` });
      } else {
        setTestMessage({
          ok: true,
          text: `Connection OK, but "${result.model}" was not in the model list — custom gateways may still work`,
        });
      }
    } catch (err) {
      setTestMessage({ ok: false, text: err instanceof Error ? err.message : String(err) });
    } finally {
      setTesting(false);
    }
  }

  return (
    <section className="panel">
      <div className="panel-heading">
        <h3>⚙ Model API configuration</h3>
        <button onClick={onClose}>Close</button>
      </div>
      <p className="hint">
        Stored server-side in <code>model-config.json</code> (gitignored). The key is never
        returned to the browser — only a masked preview. Works with any OpenAI-compatible
        endpoint via Base URL. Planner, worker, critic, guardrail, and synthesizer agents all
        need this configured before a run can start.
      </p>
      <div className="settings-grid">
        <label>
          Model
          <input value={model} onChange={(event) => setModel(event.target.value)} placeholder="gpt-4o-mini" />
        </label>
        <label>
          Base URL (optional — for gateways / proxies)
          <input
            value={baseUrl}
            onChange={(event) => setBaseUrl(event.target.value)}
            placeholder="https://api.openai.com/v1"
          />
        </label>
        <label>
          API key
          <input
            type="password"
            value={apiKey}
            onChange={(event) => setApiKey(event.target.value)}
            placeholder={
              info?.api_key_masked ? `current: ${info.api_key_masked} (${info.key_source})` : "sk-…"
            }
          />
        </label>
      </div>
      <div className="controls">
        <button className="primary" onClick={save} disabled={busy || !model.trim()}>
          {busy ? (
            <>
              <span className="spinner" /> Saving…
            </>
          ) : (
            "Save"
          )}
        </button>
        <button onClick={test} disabled={testing}>
          {testing ? (
            <>
              <span className="spinner" /> Testing…
            </>
          ) : (
            "Test connection"
          )}
        </button>
        {saved ? <span className="ok-note">Saved</span> : null}
      </div>
      {error ? <p className="error">{error}</p> : null}
      {testMessage ? (
        <p className={testMessage.ok ? "test-ok" : "error"}>{testMessage.text}</p>
      ) : null}
    </section>
  );
}
