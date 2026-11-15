import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../lib/api";
import type { EventEntry, Status, WsMessage } from "../lib/types";

const MAX_EVENTS = 50;

/** Polls /api/status every 2 s while the document is visible. */
export function useStatus() {
  const [status, setStatus] = useState<Status | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    let timer: number;
    const tick = () => {
      api
        .status()
        .then((s) => {
          if (!cancelled) {
            setStatus(s);
            setError(null);
          }
        })
        .catch((e) => {
          if (!cancelled) setError(e instanceof Error ? e.message : "link lost");
        })
        .finally(() => {
          if (!cancelled) timer = window.setTimeout(tick, 2000);
        });
    };
    tick();
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [refreshKey]);

  const refresh = useCallback(() => setRefreshKey((k) => k + 1), []);

  return { status, error, connected: error === null, refresh };
}

export type ControllerState = Status["controller"]["state"];

/** Connects to /ws/gestures, feeds frames and event/state pushes. */
export function useGestureSocket(onMessage: (m: WsMessage) => void) {
  const [connected, setConnected] = useState(false);
  const handlerRef = useRef(onMessage);
  handlerRef.current = onMessage;

  useEffect(() => {
    let ws: WebSocket | null = null;
    let cancelled = false;
    let retry: number | undefined;

    const connect = () => {
      if (cancelled) return;
      const proto = window.location.protocol === "https:" ? "wss" : "ws";
      ws = new WebSocket(`${proto}://${window.location.host}/ws/gestures`);
      ws.onopen = () => setConnected(true);
      ws.onmessage = (ev) => {
        try {
          handlerRef.current(JSON.parse(ev.data) as WsMessage);
        } catch {
          /* ignore malformed */
        }
      };
      ws.onclose = () => {
        setConnected(false);
        if (!cancelled) retry = window.setTimeout(connect, 1000);
      };
      ws.onerror = () => ws?.close();
    };
    connect();
    return () => {
      cancelled = true;
      if (retry) window.clearTimeout(retry);
      ws?.close();
    };
  }, []);

  return connected;
}

/** Latest event log mirrored from WS pushes (newest first). */
export function useEventLog() {
  const [events, setEvents] = useState<EventEntry[]>([]);
  const push = useCallback((entry: EventEntry) => {
    setEvents((prev) => [entry, ...prev].slice(0, MAX_EVENTS));
  }, []);
  return { events, push, setEvents };
}

export function useReducedMotion(): boolean {
  const [reduced, setReduced] = useState(
    () => window.matchMedia("(prefers-reduced-motion: reduce)").matches,
  );
  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    const onChange = () => setReduced(mq.matches);
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);
  return reduced;
}
