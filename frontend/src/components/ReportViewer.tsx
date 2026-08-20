import { useState } from "react";
import { reportMarkdownUrl } from "../api";
import type { Report } from "../types";
import { ComparisonTable, Prose, renderInline } from "./Markdown";
import SourceList from "./SourceList";

export default function ReportViewer({ report }: { report: Report }) {
  const [copied, setCopied] = useState(false);
  const citationLabels = new Set(report.structured.sources.map((_, index) => String(index + 1)));

  async function copyReport() {
    await navigator.clipboard.writeText(report.markdown);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <article className="report-card">
      <header className="report-card-header">
        <h2>{report.title}</h2>
        <div className="button-row">
          <a
            className="button"
            href={reportMarkdownUrl(report.run_id)}
            target="_blank"
            rel="noreferrer"
          >
            Download
          </a>
          <button onClick={copyReport}>{copied ? "Copied" : "Copy"}</button>
        </div>
      </header>

      <div className="report-lead">
        <Prose text={report.structured.executive_summary} citationLabels={citationLabels} />
      </div>

      {report.structured.comparison_table_markdown ? (
        <section className="report-section">
          <h3>Comparison</h3>
          <ComparisonTable markdown={report.structured.comparison_table_markdown} />
        </section>
      ) : null}

      {report.structured.sections.map((section) => (
        <section className="report-section" key={section.heading}>
          <h3>{section.heading}</h3>
          <Prose text={section.markdown} citationLabels={citationLabels} />
        </section>
      ))}

      <section className="report-section">
        <h3>Conclusions</h3>
        <ul className="conclusion-list">
          {report.structured.conclusions.map((conclusion) => (
            <li key={conclusion.conclusion}>
              <span>{renderInline(conclusion.conclusion, citationLabels)}</span>
              <span className="confidence-badge">
                {(conclusion.confidence * 100).toFixed(0)}%
              </span>
            </li>
          ))}
        </ul>
      </section>

      {report.structured.limitations.length ? (
        <section className="report-section">
          <h3>Limitations</h3>
          <ul className="limitation-list">
            {report.structured.limitations.map((limitation) => (
              <li key={limitation}>{limitation}</li>
            ))}
          </ul>
        </section>
      ) : null}

      <section className="report-section">
        <h3>Sources</h3>
        <SourceList sources={report.structured.sources} />
      </section>
    </article>
  );
}
