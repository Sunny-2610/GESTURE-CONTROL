import type { EventEntry } from "../../lib/types";

export function EventLog({ events, max = 12 }: { events: EventEntry[]; max?: number }) {
  const visible = events.slice(0, max);
  return (
    <div className="p-6" aria-live="polite">
      {visible.length === 0 ? (
        <p className="font-mono text-[13px] leading-5 text-ink-muted">NO EVENTS</p>
      ) : (
        <ul className="space-y-1">
          {visible.map((entry, i) => (
            <li
              key={`${entry.ts}-${entry.event}-${i}`}
              className={`flex font-mono text-[13px] leading-5 ${
                entry.event.startsWith("EMERGENCY")
                  ? "text-signal-text"
                  : i >= 3
                    ? "text-ink-muted"
                    : "text-ink"
              }`}
            >
              <span className="w-20 shrink-0">{entry.ts}</span>
              <span className="w-40 shrink-0 truncate uppercase">{entry.event}</span>
              <span className="truncate text-ink-muted">{entry.detail}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
