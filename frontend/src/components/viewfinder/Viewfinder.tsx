import { useEffect, useRef, useState } from "react";
import type { ControllerState, WsHand } from "../../lib/types";
import { SkeletonCanvas } from "./SkeletonCanvas";
import { ActiveRegion, CornerBrackets, EmptyState, OverlayChip } from "./Parts";

interface ViewfinderProps {
  cameraOpen: boolean;
  hands: WsHand[];
  state: ControllerState;
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
  gesture,
  confidence,
  cursor,
  showActiveRegion = false,
  emptyLabel = "Camera off",
  onEmptyAction,
}: ViewfinderProps) {
  const img = useRef<HTMLImageElement>(null);
  const [loaded, setLoaded] = useState(false);
  const streamRef = useRef<string | null>(null);

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
    ? "Live"
    : state === "HALT"
      ? "Input blocked"
      : "Preview only";

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
          {cursor && (
            <OverlayChip position="bottom-left">
              Cursor {cursor[0]} / {cursor[1]}
            </OverlayChip>
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
