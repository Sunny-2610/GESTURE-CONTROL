import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import type { ReactNode } from "react";
import { api } from "../lib/api";
import { useEventLog, useGestureSocket, useStatus } from "../hooks/useBackend";
import type { ControllerState, Status, WsMessage, WsHand } from "../lib/types";

interface AppData {
  status: Status | null;
  connected: boolean;
  state: ControllerState;
  hands: WsHand[];
  fps: number | null;
  procMs: number | null;
  events: ReturnType<typeof useEventLog>["events"];
  detectedGesture: string | null;
  confidence: number | null;
  cursor: [number, number] | null;
  cameraOpen: boolean;
  refreshStatus: () => void;
}

const Ctx = createContext<AppData | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const { status, error, connected } = useStatus();
  const { events, push, setEvents } = useEventLog();
  const [state, setState] = useState<ControllerState>("OFF");
  const [hands, setHands] = useState<WsHand[]>([]);
  const [fps, setFps] = useState<number | null>(null);
  const [procMs, setProcMs] = useState<number | null>(null);
  const [detected, setDetected] = useState<string | null>(null);
  const [confidence, setConfidence] = useState<number | null>(null);
  const [cursor, setCursor] = useState<[number, number] | null>(null);
  const rafRef = useRef(0);

  // load initial event log
  useEffect(() => {
    api.events().then(setEvents).catch(() => {});
  }, [setEvents]);

  const onMessage = useCallback(
    (m: WsMessage) => {
      if (m.type === "frame") {
        // batch DOM updates to animation frames
        cancelAnimationFrame(rafRef.current);
        rafRef.current = requestAnimationFrame(() => {
          setHands(m.hands ?? []);
          setFps(m.fps ?? null);
          setProcMs(m.proc_ms ?? null);
          const primary = (m.hands ?? []).find((h) => h.role === "primary") ?? (m.hands ?? [])[0];
          setDetected(primary?.gesture ?? null);
          setConfidence(primary?.confidence ?? null);
          setCursor(
            primary?.cursor ? ([primary.cursor[0], primary.cursor[1]] as [number, number]) : null,
          );
        });
      } else if (m.type === "state") {
        setState(m.state);
      } else if (m.type === "event") {
        push(m.entry);
      }
    },
    [push],
  );

  useGestureSocket(onMessage);

  // keep state in sync with polling too
  useEffect(() => {
    if (status?.controller.state) setState(status.controller.state);
  }, [status?.controller.state]);

  const value = useMemo<AppData>(
    () => ({
      status,
      connected: connected && (status !== null),
      state,
      hands,
      fps,
      procMs,
      events,
      detectedGesture: detected,
      confidence,
      cursor,
      cameraOpen: status?.camera.open ?? false,
      refreshStatus: () => api.status().then(() => undefined).catch(() => undefined),
    }),
    [status, connected, state, hands, fps, procMs, events, detected, confidence, cursor],
  );

  void error;
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useAppData(): AppData {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useAppData must be used inside AppProvider");
  return ctx;
}
