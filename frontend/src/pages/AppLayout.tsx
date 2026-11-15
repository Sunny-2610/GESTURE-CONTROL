import { useEffect, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { TopBar } from "../components/shell/TopBar";
import { StatusLine } from "../components/shell/StatusLine";
import { AlertStrip, alertVariantFor } from "../components/shell/AlertStrip";
import { useAppData } from "../hooks/AppContext";
import { useGestureSocket } from "../hooks/useBackend";
import type { WsMessage } from "../lib/types";

/** assertive announcements for emergency/disconnect */
function useAriaAnnouncements() {
  const [latest, setLatest] = useState<string>("");
  const onMessage = (m: WsMessage) => {
    if (m.type === "event" && m.entry) {
      if (m.entry.event.startsWith("EMERGENCY") || m.entry.event.startsWith("CONTROL DISABLED")) {
        setLatest(`${m.entry.event} ${m.entry.detail}`);
      }
    } else if (m.type === "state" && m.state === "HALT") {
      setLatest("Emergency stop engaged");
    }
  };
  useGestureSocket(onMessage);
  return latest;
}

export function AppLayout() {
  const { status, connected, state, fps, procMs, events } = useAppData();
  const location = useLocation();
  const announcement = useAriaAnnouncements();

  useEffect(() => {
    document.title = `Gesture Control — ${location.pathname === "/" ? "Dashboard" : location.pathname.slice(1)}`;
  }, [location]);

  const alert = alertVariantFor(state, events, connected);

  return (
    <div className="min-h-screen">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-2 focus:z-50 focus:bg-paper focus:px-2 focus:py-1 focus:font-label focus:uppercase"
      >
        Skip to content
      </a>
      <TopBar />
      <div className="pt-topbar" aria-hidden />
      {alert && (
        <AlertStrip
          variant={alert.variant}
          stamp={alert.stamp}
          detail={alert.detail}
          connected={connected}
        />
      )}
      <main id="main" className="min-h-[calc(100vh-140px)]">
        <Outlet />
      </main>
      <StatusLine
        status={status}
        connected={connected}
        fps={fps}
        latency={procMs != null ? procMs + 4 : null}
      />
      <div aria-live="assertive" className="sr-only">
        {announcement}
      </div>
    </div>
  );
}
