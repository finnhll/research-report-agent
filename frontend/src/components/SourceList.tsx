import type { SourceRecord } from "../types";

export default function SourceList({ sources }: { sources: SourceRecord[] }) {
  return (
    <ol className="source-list">
      {sources.map((source, index) => (
        <li key={source.source_id} id={`source-${index + 1}`}>
          <span className="source-number">[{index + 1}]</span>
          <div className="source-body">
            <a href={source.url} target="_blank" rel="noreferrer">
              {source.title}
            </a>
            <small>
              {source.publisher}
              {source.credibility ? ` · credibility ${source.credibility}` : ""}
            </small>
          </div>
        </li>
      ))}
    </ol>
  );
}
