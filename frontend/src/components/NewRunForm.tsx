import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api } from "../api";

const dimensions = ["cost", "safety", "performance", "supply chain"];

export default function NewRunForm() {
  const [goal, setGoal] = useState("");
  const [selected, setSelected] = useState<string[]>(["cost", "safety"]);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: () => api.createRun(goal.trim(), selected),
    onSuccess: (run) => {
      queryClient.invalidateQueries({ queryKey: ["runs"] });
      navigate(`/runs/${run.run_id}`);
    },
  });

  function toggleDimension(dimension: string) {
    setSelected((current) =>
      current.includes(dimension)
        ? current.filter((item) => item !== dimension)
        : [...current, dimension].slice(0, 5),
    );
  }

  return (
    <section className="panel new-run">
      <h2>Start research</h2>
      <label className="field-label" htmlFor="goal">
        Research goal
      </label>
      <textarea
        id="goal"
        value={goal}
        rows={5}
        placeholder="Compare the top 3 EV battery chemistries for cost and safety."
        onChange={(event) => setGoal(event.target.value)}
      />
      <fieldset>
        <legend>Required dimensions</legend>
        <div className="dimension-grid">
          {dimensions.map((dimension) => (
            <label key={dimension} className="checkbox">
              <input
                type="checkbox"
                checked={selected.includes(dimension)}
                onChange={() => toggleDimension(dimension)}
              />
              <span>{dimension}</span>
            </label>
          ))}
        </div>
      </fieldset>
      <button
        className="primary"
        disabled={goal.trim().length < 3 || mutation.isPending}
        onClick={() => mutation.mutate()}
      >
        {mutation.isPending ? "Starting…" : "Start run"}
      </button>
      {mutation.isError ? (
        <p className="error">{(mutation.error as Error).message}</p>
      ) : null}
    </section>
  );
}
