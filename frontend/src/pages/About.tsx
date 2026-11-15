import { useAppData } from "../hooks/AppContext";

export function AboutPage() {
  const { status } = useAppData();
  const system = status?.system;
  const checks = status?.checks;

  const rows = [
    ["Backend", system?.backend],
    ["Vision", system?.vision],
    ["Model", system?.model],
    ["Frontend", system?.frontend],
    ["Session", system?.session],
    ["Input mode", status ? (status.input_live ? "LIVE" : "DRY RUN") : undefined],
  ] as const;

  const checkRows = [
    ["Camera access", checks?.camera_access],
    ["Model loaded", checks?.model_loaded],
    ["Input backend", checks?.input_backend],
    ["Volume backend", checks?.volume_backend],
  ] as const;

  return (
    <div className="grid grid-cols-2 divide-x divide-ink border-b border-ink">
      <div className="p-8">
        <h1 className="font-sans font-semibold text-ink" style={{ fontSize: "72px", lineHeight: "72px" }}>
          Gesture Control
        </h1>
        <p className="mt-6 max-w-[60ch] font-body text-ink-muted">
          A measuring device pointed at your hand. The camera reads the hand skeleton;
          control is gated behind arming, an emergency stop and automatic fail-safes.
        </p>
        <div className="mt-8 space-y-3">
          <p className="border-l-2 border-ink pl-3 font-body">
            Nothing is sent until control is armed. Arming requires three explicit confirmations.
          </p>
          <p className="border-l-2 border-ink pl-3 font-body">
            The emergency stop is always reachable: on screen, and with the global hotkey.
          </p>
          <p className="border-l-2 border-ink pl-3 font-body">
            Losing the hand or the link disables control automatically. Nothing moves on its own.
          </p>
        </div>
      </div>
      <div className="p-8">
        <table className="w-full font-mono text-[13px] leading-5">
          <thead>
            <tr className="font-label uppercase tracking-[0.06em] text-ink-muted">
              <th className="pb-2 text-left font-medium">System</th>
              <th className="pb-2 text-left font-medium">Value</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(([k, v]) => (
              <tr key={k} className="border-t border-ink">
                <td className="py-2 text-ink-muted">{k}</td>
                <td className="py-2">{v ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="mt-8 font-label uppercase tracking-[0.06em] text-ink-muted">System check</p>
        <table className="mt-2 w-full font-mono text-[13px] leading-5">
          <tbody>
            {checkRows.map(([k, v]) => (
              <tr key={k} className="border-t border-ink">
                <td className="py-2 text-ink-muted">{k}</td>
                <td className="py-2">{v ?? "FAIL"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
