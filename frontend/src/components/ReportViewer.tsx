import { useState } from "react";
import { reportMarkdownUrl } from "../api";
import type { Report } from "../types";
import SourceList from "./SourceList";

export default function ReportViewer({ report }: { report: Report }) {
  const [copied, setCopied] = useState(false);

  async function copyReport() {
    await navigator.clipboard.writeText(report.markdown);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <section className="panel report">
      <div className="panel-heading">
        <h2>{report.title}</h2>
        <div className="button-row">
          <a
            className="button"
            href={reportMarkdownUrl(report.run_id)}
            target="_blank"
            rel="noreferrer"
          >
            Download Markdown
          </a>
          <button onClick={copyReport}>{copied ? "Copied" : "Copy report"}</button>
        </div>
      </div>
      <p className="summary">{report.structured.executive_summary}</p>
      {report.structured.comparison_table_markdown ? (
        <pre className="comparison">{report.structured.comparison_table_markdown}</pre>
      ) : null}
      {report.structured.sections.map((section) => (
        <article key={section.heading}>
          <h3>{section.heading}</h3>
          <p>{section.markdown}</p>
        </article>
      ))}
      <h3>Conclusions</h3>
      <ul>
        {report.structured.conclusions.map((conclusion) => (
          <li key={conclusion.conclusion}>
            {conclusion.conclusion}{" "}
            <em>confidence {(conclusion.confidence * 100).toFixed(0)}%</em>
          </li>
        ))}
      </ul>
      <h3>Limitations</h3>
      <ul>
        {report.structured.limitations.map((limitation) => (
          <li key={limitation}>{limitation}</li>
        ))}
      </ul>
      <h3>Sources</h3>
      <SourceList sources={report.structured.sources} />
    </section>
  );
}
