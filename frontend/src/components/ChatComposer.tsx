import { useRef, useState } from "react";

const DIMENSIONS = ["cost", "safety", "performance", "supply chain"];

export default function ChatComposer({
  onSubmit,
  submitting,
}: {
  onSubmit: (goal: string, dimensions: string[]) => void;
  submitting: boolean;
}) {
  const [goal, setGoal] = useState("");
  const [selected, setSelected] = useState<string[]>(["cost", "safety"]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  function toggleDimension(dimension: string) {
    setSelected((current) =>
      current.includes(dimension)
        ? current.filter((item) => item !== dimension)
        : [...current, dimension].slice(0, 5),
    );
  }

  function autoGrow() {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 220)}px`;
  }

  function send() {
    const trimmed = goal.trim();
    if (trimmed.length < 3 || submitting) return;
    onSubmit(trimmed, selected);
    setGoal("");
    requestAnimationFrame(autoGrow);
  }

  return (
    <div className="composer">
      <div className="composer-dimensions">
        {DIMENSIONS.map((dimension) => (
          <button
            key={dimension}
            type="button"
            className={`chip ${selected.includes(dimension) ? "chip-active" : ""}`}
            onClick={() => toggleDimension(dimension)}
          >
            {dimension}
          </button>
        ))}
      </div>
      <div className="composer-input-row">
        <textarea
          ref={textareaRef}
          className="composer-input"
          value={goal}
          rows={1}
          aria-label="Research goal"
          placeholder="Ask a research question — e.g. Compare Rust and Go for a new backend service."
          onChange={(event) => {
            setGoal(event.target.value);
            autoGrow();
          }}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              send();
            }
          }}
        />
        <button
          type="button"
          className="composer-send"
          onClick={send}
          disabled={goal.trim().length < 3 || submitting}
          aria-label="Send"
        >
          {submitting ? <span className="spinner" /> : "↑"}
        </button>
      </div>
    </div>
  );
}
