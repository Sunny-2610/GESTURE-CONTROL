import { api } from "../../lib/api";
import type { EventEntry } from "../../lib/types";

export type AlertVariant = "stopped" | "disconnected";

export function AlertStrip({
  variant,
  stamp,
  detail,
  connected,
}: {
  variant: AlertVariant;
  stamp?: string;
  detail?: string;
  connected: boolean;
}) {
  const action =
    variant === "stopped"
      ? {
          label: "Re-arm",
          run: () => api.controller.rearm().catch(() => {}),
        }
      : {
          label: "Retry now",
          run: () => window.location.reload(),
        };
  return (
    <div className="flex h-alert items-center justify-between border-b border-ink bg-paper px-6">
      {variant === "stopped" ? (
        <p className="font-label uppercase tracking-[0.06em] text-ink">
          Stopped {stamp ?? ""}
          {detail ? ` · ${detail}` : ""}
        </p>
      ) : (
        <p className="font-label uppercase tracking-[0.06em] text-signal-text">
          {connected ? "Control disabled automatically" : "Backend lost"}
          {stamp ? ` · ${stamp}` : ""}
        </p>
      )}
      <button
        type="button"
        onClick={action.run}
        className="h-8 border border-ink px-4 font-label uppercase tracking-[0.06em] text-ink hover:bg-ink hover:text-paper"
      >
        {action.label}
      </button>
    </div>
  );
}

export interface Alert {
  variant: AlertVariant;
  stamp?: string;
  detail?: string;
}

export function alertVariantFor(
  state: string,
  events: EventEntry[],
  connected: boolean,
): Alert | null {
  if (state === "HALT") {
    const halt = events.find((e) => e.event === "EMERGENCY STOP");
    return { variant: "stopped", stamp: halt?.ts, detail: halt?.detail || undefined };
  }
  if (!connected) return { variant: "disconnected" };
  return null;
}
