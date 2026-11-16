import { useEffect, useState } from "react";
import { GestureCell } from "../components/gestures";
import { Sheet } from "../components/controls";
import { PoseDrawing } from "../components/gestures/PoseDrawing";
import { api } from "../lib/api";
import type { GestureInfo } from "../lib/types";
import { useAppData } from "../hooks/AppContext";

const HOW_TO: Record<string, string[]> = {
  closed_fist: [
    "Curl all four fingers into your palm.",
    "Tuck the thumb across them.",
    "Hold: everything pauses until you open your hand.",
  ],
  pinch_click: [
    "Touch your thumb tip to your index tip.",
    "Keep the other fingers relaxed.",
    "A click fires each time the pinch closes.",
  ],
  three_finger: [
    "Raise your index, middle and ring fingers.",
    "Curl the pinky and thumb in.",
    "Move your hand up or down to change the volume.",
  ],
  two_finger_scroll: [
    "Raise your index and middle finger in a V.",
    "Curl the ring and pinky fingers.",
    "Move your hand up or down to scroll; farther means faster.",
  ],
  pointer: [
    "Raise only your index finger.",
    "Move your hand to aim the cursor.",
    "Hold still for a moment to dwell-click (when enabled).",
  ],
  open_palm: [
    "Spread all five fingers.",
    "Sweep your hand quickly left or right.",
    "Each swipe goes back or forward in the browser.",
  ],
};

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
            <PoseDrawing pose={detail?.name ?? ""} color="#1A1916" size={240} />
          </div>
          <dl className="mt-6 space-y-3 font-body">
            <div>
              <dt className="font-label uppercase tracking-[0.06em] text-ink-muted">Motion</dt>
              <dd className="mt-1">{detail?.motion}</dd>
            </div>
            <div>
              <dt className="font-label uppercase tracking-[0.06em] text-ink-muted">Pose</dt>
              <dd className="mt-1">{detail?.pose}</dd>
            </div>
            <div>
              <dt className="font-label uppercase tracking-[0.06em] text-ink-muted">Action</dt>
              <dd className="mt-1">{detail?.action}</dd>
            </div>
          </dl>
          {detail && HOW_TO[detail.name] && (
            <div className="mt-6 border-t border-ink pt-4">
              <p className="font-label uppercase tracking-[0.06em] text-ink-muted">How to</p>
              <ol className="mt-2 list-decimal space-y-1 pl-5 font-body">
                {HOW_TO[detail.name].map((step) => (
                  <li key={step}>{step}</li>
                ))}
              </ol>
            </div>
          )}
        </div>
      </Sheet>
    </>
  );
}
