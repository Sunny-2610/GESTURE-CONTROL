import { useEffect, useRef, useState } from "react";
import type { ControllerState, WsHand } from "../../lib/types";
import { SkeletonCanvas } from "./SkeletonCanvas";
import { ActiveRegion, CornerBrackets, EmptyState, OverlayChip } from "./Parts";
interface ViewfinderProps {
  cameraOpen: boolean;
  hands: WsHand[];
  state: ControllerState;
  liveInput: boolean;
  gesture: string | null;
  confidence: number | null;
  cursor: [number, number] | null;
  showActiveRegion?: boolean;
  emptyLabel?: string;
  onEmptyAction?: React.ReactNode;
}

export function Viewfinder({
  cameraOpen,
  hands,
  state,
  liveInput,
  gesture,
  confidence,
  cursor,
  showActiveRegion = false,
  emptyLabel = "Camera off",
  onEmptyAction,
}: ViewfinderProps) {
  const img = useRef<HTMLImageElement>(null);
  const [loaded, setLoaded] = useState(false);
  const [handLost, setHandLost] = useState(false);
  const streamRef = useRef<string | null>(null);

  useEffect(() => {
    if (hands.length > 0) {
      setHandLost(false);
      return;
    }
    const timer = window.setTimeout(() => setHandLost(true), 1500);
    return () => window.clearTimeout(timer);
  }, [hands.length]);

  useEffect(() => {
    if (!cameraOpen) {
      setLoaded(false);
      if (img.current) img.current.src = "";
      streamRef.current = null;
      return;
    }
    if (streamRef.current) return;
    streamRef.current = `/api/video`;
    if (img.current) img.current.src = streamRef.current;
  }, [cameraOpen]);

  const controlling = state === "ACTIVE" || state === "HOLD";
  const skeletonColor = controlling ? "#FF4A1C" : "#1A1916";
  const modeChip = controlling
    ? state === "HOLD"
      ? "Held"
      : "Live"
    : state === "HALT"
      ? "Input blocked"
      : "Preview only";
  const handMissing = cameraOpen && handLost && (state === "ACTIVE" || state === "HOLD");

  return (
    <div
      className="relative w-full overflow-hidden border border-ink bg-paper-2"
      style={{ aspectRatio: "4 / 3" }}
      role="img"
      aria-label="Live camera view with hand tracking"
    >
      {cameraOpen && (
        <img
          ref={img}
          alt=""
          className={`absolute inset-0 h-full w-full object-cover ${
            loaded ? "" : "opacity-0"
          }`}
          style={{ transform: "scaleX(-1)" }}
          onLoad={() => setLoaded(true)}
        />
      )}
      {cameraOpen && <SkeletonCanvas hands={hands} mirrored color={skeletonColor} />}
      {showActiveRegion && cameraOpen && <ActiveRegion />}

      {cameraOpen && (
        <>
          <CornerBrackets />
          <OverlayChip position="top-left">
            {gesture ? `${gesture.replace(/_/g, " ")} ${confidence?.toFixed(2) ?? ""}` : "NO HAND"}
          </OverlayChip>
          <OverlayChip position="top-right">{modeChip}</OverlayChip>
          <OverlayChip position="bottom-right">
            {liveInput ? "Input live" : "Input dry run"}
          </OverlayChip>
          {cursor && (
            <OverlayChip position="bottom-left">
              Cursor {cursor[0]} / {cursor[1]}
            </OverlayChip>
          )}
          {handMissing && (
            <div className="pointer-events-none absolute inset-x-0 top-1/2 -translate-y-1/2 text-center">
              <span className="inline-block bg-ink px-3 py-1 text-xs uppercase tracking-widest text-paper">
                No hand in frame &mdash; raise it
              </span>
            </div>
          )}
        </>
      )}

      {!cameraOpen && (
        <>
          <CornerBrackets />
          <EmptyState label={emptyLabel} />
          {onEmptyAction && (
            <div className="absolute inset-x-0 bottom-10 flex justify-center">
              {onEmptyAction}
            </div>
          )}
        </>
      )}
    </div>
  );
}
