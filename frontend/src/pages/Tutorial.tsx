import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { useAppData } from "../hooks/AppContext";
import { PoseDrawing } from "../components/gestures";
import { Viewfinder } from "../components/viewfinder";
import { Button } from "../components/controls";

const HOLD_MS = 500;

interface TutorialStep {
  pose: string;
  title: string;
  blurb: string;
  hint: string;
}

const STEPS: TutorialStep[] = [
  {
    pose: "pointer",
    title: "Point",
    blurb: "Index up, other fingers folded. Moves the mouse cursor.",
    hint: "Keep your palm facing the camera and move your hand around.",
  },
  {
    pose: "pinch_click",
    title: "Pinch",
    blurb: "Thumb and index fingertips touch to click.",
    hint: "Bring them together slowly, then open again.",
  },
  {
    pose: "three_finger",
    title: "Volume",
    blurb: "Index, middle and ring up. Move your hand up or down.",
    hint: "The volume bar appears in the viewfinder.",
  },
  {
    pose: "two_finger_scroll",
    title: "Scroll",
    blurb: "Index and middle up. Move like a joystick.",
    hint: "Push your hand up or down to scroll the page.",
  },
  {
    pose: "open_palm",
    title: "Open palm",
    blurb: "All five fingers up. Swipe left or right to go back / forward.",
    hint: "Move your whole hand sideways in one quick motion.",
  },
  {
    pose: "closed_fist",
    title: "Fist",
    blurb: "All fingers folded. Pauses every action instantly.",
    hint: "Make a fist and hold it until the viewfinder says PAUSED.",
  },
];

export function TutorialPage() {
  const { state, hands, detectedGesture, confidence, engine, cameraOpen } = useAppData();
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [, tick] = useState(0);
  const wasLive = useRef<boolean | null>(null);
  const forced = useRef(false);
  const restored = useRef(false);
  const matchStart = useRef<number | null>(null);

  const restore = useCallback(() => {
    if (restored.current) return;
    restored.current = true;
    if (forced.current && wasLive.current !== null) {
      api.setInputMode(wasLive.current).catch(() => {});
    }
  }, []);

  // Force preview (dry-run) for the whole tutorial; restore the previous
  // input mode afterwards, even when the page unmounts early or errors.
  useEffect(() => {
    restored.current = false;
    forced.current = false;
    let cancelled = false;
    (async () => {
      try {
        const s = await api.status();
        if (cancelled) return;
        wasLive.current = s.input_live;
        if (s.input_live) {
          forced.current = true;
          await api.setInputMode(false);
        }
      } catch (e) {
        setError(String(e));
      } finally {
        if (cancelled) restore();
      }
    })();
    return () => {
      cancelled = true;
      restore();
    };
  }, [restore]);

  // timer tick so gesture-hold progress advances even while the pose is steady
  useEffect(() => {
    const id = window.setInterval(() => tick((n) => n + 1), 100);
    return () => window.clearInterval(id);
  }, []);

  // advance when the target gesture is held for HOLD_MS
  useEffect(() => {
    if (done) return;
    const target = STEPS[step]?.pose;
    if (detectedGesture === target) {
      if (matchStart.current === null) {
        matchStart.current = performance.now();
      } else if (performance.now() - matchStart.current >= HOLD_MS) {
        matchStart.current = null;
        if (step + 1 >= STEPS.length) setDone(true);
        else setStep(step + 1);
      }
    } else {
      matchStart.current = null;
    }
  }, [detectedGesture, step, done, cameraOpen]);

  const current = STEPS[Math.min(step, STEPS.length - 1)];
  const idle = state === "OFF";

  if (done) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center gap-6 p-8 text-center">
        <p className="font-heading text-ink">Tutorial complete</p>
        <p className="max-w-[60ch] font-body text-ink-muted">
          You can start control from the dashboard whenever you are ready. Actions are
          sent only after the three arming checks.
        </p>
        <Button variant="primary" onClick={() => navigate("/")}>
          Back to dashboard
        </Button>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-3 divide-x divide-ink border-b border-ink">
      <div className="col-span-2 p-8">
        <Viewfinder
          cameraOpen={cameraOpen}
          hands={hands}
          state={state}
          liveInput={false}
          gesture={detectedGesture}
          confidence={confidence}
          cursor={null}
          engine={engine}
          emptyLabel="Camera off"
          onEmptyAction={
            cameraOpen ? undefined : (
              <Button variant="secondary" onClick={() => api.camera.start().catch(() => {})}>
                Start camera
              </Button>
            )
          }
        />
        {error && (
          <p className="mt-4 font-body text-signal-text" role="alert">
            {error}
          </p>
        )}
        <p className="mt-4 max-w-[70ch] font-body text-ink-muted">
          The tutorial always runs in preview mode &mdash; no mouse, keyboard or volume
          actions are sent. Your previous input mode is restored when you leave.
        </p>
      </div>
      <div className="p-8">
        <div className="flex items-baseline justify-between">
          <span className="font-label uppercase tracking-[0.06em] text-ink-muted">
            Step {step + 1} / {STEPS.length}
          </span>
          <button
            className="font-label uppercase tracking-[0.06em] text-ink-muted underline hover:text-ink"
            onClick={() => setDone(true)}
          >
            Skip
          </button>
        </div>
        <div className="mt-6 flex items-center gap-6">
          <div className="w-24 shrink-0">
            <PoseDrawing pose={current.pose} color="#1A1916" size={96} />
          </div>
          <div>
            <h2 className="font-heading text-ink">{current.title}</h2>
            <p className="mt-2 font-body text-ink">{current.blurb}</p>
          </div>
        </div>
        <p className="mt-6 font-body text-ink-muted">{current.hint}</p>
        {idle && (
          <p className="mt-6 border border-dashed border-ink p-3 font-label uppercase tracking-[0.06em] text-ink-muted">
            Preview only &mdash; start control from the dashboard to send actions
          </p>
        )}
        <div className="mt-8 flex gap-1.5" aria-hidden>
          {STEPS.map((s, i) => (
            <span
              key={s.pose}
              className={`h-1.5 w-8 ${i <= step ? "bg-ink" : "bg-ink-muted"}`}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
