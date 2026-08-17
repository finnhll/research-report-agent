import type { SourceRecord } from "../types";

export default function SourceList({ sources }: { sources: SourceRecord[] }) {
  return (
    <ul className="source-list">
      {sources.map((source) => (
        <li key={source.source_id}>
          <a href={source.url} target="_blank" rel="noreferrer">
            {source.title}
          </a>
          <small>
            {source.publisher} · credibility {source.credibility}
          </small>
        </li>
      ))}
    </ul>
  );
}
