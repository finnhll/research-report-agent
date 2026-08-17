import type { EventRecord } from "../types";

export default function EventTimeline({ events }: { events: EventRecord[] }) {
  const reversed = [...events].reverse();
  return (
    <ol className="timeline">
      {reversed.map((event) => (
        <li key={event.event_id}>
          <div>
            <strong>{event.event_type}</strong>
            <span>{new Date(event.timestamp).toLocaleTimeString()}</span>
          </div>
          {event.task_id ? <small>{event.task_id}</small> : null}
        </li>
      ))}
    </ol>
  );
}
