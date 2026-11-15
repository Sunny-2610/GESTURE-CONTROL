import type { Status } from "../../lib/types";

export function StatusLine({
  status,
  connected,
  fps,
  latency,
}: {
  status: Status | null;
  connected: boolean;
  fps?: number | null;
  latency?: number | null;
}) {
  const fpsValue = fps ?? status?.fps ?? null;
  const latValue = latency ?? status?.latency_ms ?? null;
  return (
    <div className="h-status border-b border-ink bg-paper px-6">
      {!connected ? (
        <p className="flex items-center gap-2 font-label uppercase tracking-[0.06em] text-ink-muted">
          <span className="font-label font-semibold uppercase tracking-[0.06em] text-signal-text">
            Link lost
          </span>
          <span>· retry in 4 s</span>
        </p>
      ) : (
        <p className="flex items-center font-label uppercase tracking-[0.06em] text-ink-muted">
          <span>Link 127.0.0.1:8000</span>
          <span aria-hidden> · </span>
          <span>Cam {status?.camera.open ? "0" : "—"}</span>
          <span aria-hidden> · </span>
          <span>{status?.camera.resolution ?? "—"}</span>
          <span aria-hidden> · </span>
          <span>{fpsValue != null ? `${fpsValue.toFixed(1)} FPS` : "FPS —"}</span>
          <span aria-hidden> · </span>
          <span>{latValue != null ? `Lat ${Math.round(latValue)} ms` : "Lat —"}</span>
        </p>
      )}
    </div>
  );
}
