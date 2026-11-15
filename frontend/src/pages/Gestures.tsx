import { useEffect, useState } from "react";
import { GestureCell } from "../components/gestures";
import { Sheet } from "../components/controls";
import { PoseDrawing } from "../components/gestures/PoseDrawing";
import { api } from "../lib/api";
import type { GestureInfo } from "../lib/types";
import { useAppData } from "../hooks/AppContext";

export function GesturesPage() {
  const [gestures, setGestures] = useState<GestureInfo[]>([]);
  const [detail, setDetail] = useState<GestureInfo | null>(null);
  const { detectedGesture } = useAppData();

  useEffect(() => {
    api.gestures().then(setGestures).catch(() => {});
  }, []);

  const toggle = (name: string, enabled: boolean) => {
    api
      .toggleGesture(name, enabled)
      .then((updated) =>
        setGestures((gs) => gs.map((g) => (g.name === updated.name ? { ...g, enabled } : g))),
      )
      .catch(() => {});
  };

  return (
    <>
      <div className="grid grid-cols-3 grid-rows-2 divide-x divide-y divide-ink border-b border-ink max-[1023px]:grid-cols-2 max-[1023px]:grid-rows-3">
        {gestures.map((g) => (
          <GestureCell
            key={g.name}
            gesture={g}
            detected={detectedGesture === g.name}
            onToggle={(enabled) => toggle(g.name, enabled)}
            onOpen={() => setDetail(g)}
          />
        ))}
      </div>
      <p className="px-6 py-4 font-label uppercase tracking-[0.06em] text-ink-muted">
        Higher priority overrides lower. One action at a time.
      </p>

      <Sheet open={detail !== null} onClose={() => setDetail(null)} title={detail?.title ?? ""}>
        <div className="p-8">
          <div className="mb-6 border-b border-ink pb-4">
            <p className="font-label uppercase tracking-[0.06em] text-ink-muted">
              Gesture {detail ? String(detail.priority).padStart(2, "0") : ""}
            </p>
            <h1 className="mt-1 font-heading text-[20px] font-semibold">{detail?.title}</h1>
          </div>
          <div className="flex justify-center">
            <PoseDrawing pose={detail?.name ?? ""} color="#1A1916" />
          </div>
          <dl className="mt-6 space-y-3 font-body">
            <div>
              <dt className="font-label uppercase tracking-[0.06em] text-ink-muted">Pose</dt>
              <dd className="mt-1">{detail?.pose}</dd>
            </div>
            <div>
              <dt className="font-label uppercase tracking-[0.06em] text-ink-muted">Action</dt>
              <dd className="mt-1">{detail?.action}</dd>
            </div>
          </dl>
        </div>
      </Sheet>
    </>
  );
}
