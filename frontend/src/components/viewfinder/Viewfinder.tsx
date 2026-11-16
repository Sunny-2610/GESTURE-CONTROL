import { useEffect, useMemo, useRef, useState } from "react";
import type { ControllerState, EngineStatus, WsHand } from "../../lib/types";
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
  engine?: EngineStatus;
  showActiveRegion?: boolean;
  emptyLabel?: string;
  onEmptyAction?: React.ReactNode;
}

/** Toast that fades about 1 s after a new (text, ts) pair arrives. */
function ActionToast({ toast }: { toast: EngineStatus["toast"] }) {
  const [visible, setVisible] = useState(false);
  const lastTs = useRef(0);
  const reduced = useMemo(
    () =>
      typeof window !== "undefined" &&
      window.matchMedia?.("(prefers-reduced-motion: reduce)").matches === true,
    [],
  );

  useEffect(() => {
    if (!toast || toast.ts === lastTs.current) return;
    lastTs.current = toast.ts;
    setVisible(true);
    const t = window.setTimeout(() => setVisible(false), 1000);
    return () => window.clearTimeout(t);
  }, [toast]);

  if (!toast || !visible) return null;
  return (
    <div
      role="status"
      className={`absolute bottom-16 left-1/2 -translate-x-1/2 bg-ink px-3 py-1.5 font-mono text-[14px] uppercase tracking-widest text-paper ${
        reduced ? "" : "transition-opacity duration-300"
      }`}
    >
      {toast.text}
    </div>
  );
}

export function Viewfinder({
  cameraOpen,
  hands,
  state,
  liveInput,
  gesture,
  confidence,
  cursor,
  engine,
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

  // large mode chip text
  const modeText = controlling && engine
    ? engine.mode === "cursor"
      ? "CURSOR"
      : engine.mode === "click"
        ? "CLICK"
        : engine.mode === "scroll"
          ? "SCROLL"
          : engine.mode === "volume"
            ? engine.volume != null
              ? `VOLUME ${Math.round(engine.volume)}%`
              : "VOLUME"
            : engine.mode === "swipe"
              ? "SWIPE"
              : engine.mode === "paused"
                ? "PAUSED"
                : null
    : null;

  const scrollSpeed = Math.min(1, Math.abs(engine?.scroll_velocity ?? 0) / 12);
  const scrollArrow = controlling && engine?.mode === "scroll" && scrollSpeed > 0.04;

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
      {cameraOpen && (
        <SkeletonCanvas
          hands={hands}
          mirrored
          color={skeletonColor}
          dwell={controlling ? engine?.dwell_progress ?? 0 : 0}
        />
      )}
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

          {modeText && (
            <div
              className="absolute left-1/2 top-3 -translate-x-1/2 bg-ink px-4 py-1.5 font-mono text-[15px] uppercase tracking-[0.2em] text-paper"
              aria-live="polite"
            >
              {modeText}
            </div>
          )}

          {/* vertical volume bar, only in volume mode */}
          {controlling && engine?.mode === "volume" && (
            <div className="absolute right-10 top-1/2 flex h-1/2 -translate-y-1/2 items-stretch gap-2">
              <div className="relative w-4 border border-ink bg-paper/85">
                <div
                  className="absolute bottom-0 left-0 right-0 bg-ink"
                  style={{ height: `${Math.max(0, Math.min(100, engine.volume ?? 0))}%` }}
                />
                {engine.volume_anchor != null && (
                  <div
                    className="absolute left-[-6px] right-[-6px] h-[2px] bg-signal-text"
                    style={{ top: `${Math.max(0, Math.min(100, engine.volume_anchor * 100))}%` }}
                    aria-hidden
                  />
                )}
              </div>
              <span className="self-center font-mono text-[13px] font-semibold text-ink">
                {engine.volume != null ? `${Math.round(engine.volume)}%` : "—"}
              </span>
            </div>
          )}

          {/* scroll arrow, size follows velocity */}
          {scrollArrow && (
            <div className="absolute right-10 top-1/2 -translate-y-1/2">
              <svg
                width={24}
                height={16 + 48 * scrollSpeed}
                viewBox="0 0 24 64"
                aria-hidden
                className="text-ink"
              >
                <g
                  stroke="currentColor"
                  strokeWidth={2.5}
                  fill="none"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  transform={
                    (engine?.scroll_velocity ?? 0) < 0 ? undefined : "rotate(180 12 32)"
                  }
                >
                  <line x1="12" y1="10" x2="12" y2={54 * (0.4 + 0.6 * scrollSpeed) + 6} />
                  <path d={`M5 ${8 + 44 * scrollSpeed} L12 ${2 + 50 * scrollSpeed} L19 ${8 + 44 * scrollSpeed}`} />
                </g>
              </svg>
            </div>
          )}

          <ActionToast toast={engine?.toast ?? null} />

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
