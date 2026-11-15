import { useState } from "react";
import { Viewfinder } from "../components/viewfinder";
import { Button, Switch } from "../components/controls";
import { useAppData } from "../hooks/AppContext";
import { api } from "../lib/api";
import type { WsHand } from "../lib/types";

const TABLE_ROWS: { name: string; index: number }[] = [
  { name: "wrist", index: 0 },
  { name: "thumb tip", index: 4 },
  { name: "index mcp", index: 5 },
  { name: "index tip", index: 8 },
  { name: "middle tip", index: 12 },
  { name: "pinky tip", index: 20 },
];

function Inspector({
  hand,
  showSkeleton,
  showRegion,
  setShowSkeleton,
  setShowRegion,
  procMs,
}: {
  hand: WsHand | null;
  showSkeleton: boolean;
  showRegion: boolean;
  setShowSkeleton: (v: boolean) => void;
  setShowRegion: (v: boolean) => void;
  procMs: number | null;
}) {
  const fmt = (v: number) => v.toFixed(3);
  return (
    <div className="flex flex-col">
      <section className="border-b border-ink p-6" aria-label="Hands">
        <p className="font-label uppercase tracking-[0.06em] text-ink-muted">Hands</p>
        {hand ? (
          <dl className="mt-3 space-y-2 font-mono text-[13px] leading-5">
            <div className="flex justify-between"><dt className="text-ink-muted">hand</dt><dd>{hand.hand}</dd></div>
            <div className="flex justify-between"><dt className="text-ink-muted">role</dt><dd>{hand.role}</dd></div>
            <div className="flex justify-between"><dt className="text-ink-muted">confidence</dt><dd>{hand.confidence.toFixed(2)}</dd></div>
          </dl>
        ) : (
          <p className="mt-3 font-mono text-[13px] text-ink-muted">—</p>
        )}
        <p className="mt-4 font-label uppercase tracking-[0.06em] text-ink-muted">Finger state</p>
        <div className="mt-2 flex gap-2">
          {[0, 1, 2, 3, 4].map((i) => (
            <span
              key={i}
              className={`h-6 w-6 border border-ink ${hand?.finger_states?.[i] ? "bg-ink" : ""}`}
              title={["thumb", "index", "middle", "ring", "pinky"][i]}
            />
          ))}
        </div>
      </section>
      <section className="border-b border-ink p-6" aria-label="Landmarks">
        <p className="font-label uppercase tracking-[0.06em] text-ink-muted">Landmarks</p>
        <table className="mt-3 w-full font-mono text-[13px] leading-5">
          <thead>
            <tr className="font-label uppercase tracking-[0.06em] text-ink-muted">
              <th className="text-left font-medium">pt</th>
              <th className="text-right font-medium">x</th>
              <th className="text-right font-medium">y</th>
              <th className="text-right font-medium">z</th>
            </tr>
          </thead>
          <tbody>
            {TABLE_ROWS.map(({ name, index }) => {
              const lm = hand?.landmarks?.[index];
              return (
                <tr key={index} className="border-t border-ink">
                  <td className="py-1">{String(index).padStart(2, "0")} {name}</td>
                  <td className="text-right">{lm ? fmt(lm[0]) : "—"}</td>
                  <td className="text-right">{lm ? fmt(lm[1]) : "—"}</td>
                  <td className="text-right">{lm ? fmt(lm[2]) : "—"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </section>
      <section className="flex flex-1 flex-wrap items-center gap-4 p-6" aria-label="Tools">
        <span className="flex items-center gap-2">
          <span className="font-label uppercase tracking-[0.06em]">Skeleton</span>
          <Switch checked={showSkeleton} onChange={setShowSkeleton} label="Show skeleton" />
        </span>
        <span className="flex items-center gap-2">
          <span className="font-label uppercase tracking-[0.06em]">Active region</span>
          <Switch checked={showRegion} onChange={setShowRegion} label="Show active region" />
        </span>
        <Button variant="secondary" onClick={() => api.camera.stop().catch(() => {})}>
          Stop camera
        </Button>
        <span className="font-mono text-[13px] text-ink-muted">
          Proc {procMs != null ? `${procMs} ms` : "—"}
        </span>
      </section>
    </div>
  );
}

export function CameraPage() {
  const { status, state, hands, procMs, detectedGesture, confidence, cameraOpen } = useAppData();
  const [showSkeleton, setShowSkeleton] = useState(true);
  const [showRegion, setShowRegion] = useState(true);

  const primary = hands.find((h) => h.role === "primary") ?? hands[0] ?? null;
  const busy = Boolean(status?.camera.busy) && !cameraOpen;

  return (
    <div className="grid grid-cols-4 divide-x divide-ink border-b border-ink">
      <div className="col-span-3 p-8">
        <Viewfinder
          cameraOpen={cameraOpen}
          hands={showSkeleton ? hands : []}
          state={state}
          gesture={detectedGesture}
          confidence={confidence}
          cursor={null}
          showActiveRegion={showRegion}
          emptyLabel={busy ? "Camera busy" : "Camera off"}
          onEmptyAction={
            cameraOpen ? undefined : (
              <Button variant="secondary" onClick={() => api.camera.start().catch(() => {})}>
                Start camera
              </Button>
            )
          }
        />
      </div>
      <Inspector
        hand={primary}
        showSkeleton={showSkeleton}
        showRegion={showRegion}
        setShowSkeleton={setShowSkeleton}
        setShowRegion={setShowRegion}
        procMs={procMs}
      />
    </div>
  );
}
