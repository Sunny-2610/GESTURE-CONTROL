import { useEffect, useState } from "react";
import { api } from "../lib/api";
import type { ControllerState } from "../lib/types";

/** Controller state machine mirror with transitions from /api/controller. */
export function useControllerState() {
  const [state, setState] = useState<ControllerState>("OFF");
  const [error, setError] = useState<string | null>(null);

  // poll status lightly to stay in sync with other surfaces (hotkey, ws rules)
  useEffect(() => {
    let timer: number;
    let cancelled = false;
    const tick = () => {
      api
        .status()
        .then((s) => !cancelled && setState(s.controller.state))
        .catch(() => {})
        .finally(() => {
          if (!cancelled) timer = window.setTimeout(tick, 2000);
        });
    };
    tick();
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, []);

  const run = async (fn: () => Promise<{ state: string }>) => {
    try {
      const res = await fn();
      setState(res.state as ControllerState);
      setError(null);
      return true;
    } catch (e) {
      setError(e instanceof Error ? e.message : "command failed");
      return false;
    }
  };

  return {
    state,
    error,
    arm: () => run(() => api.controller.start({ hand_visible: true, nothing_unsaved: true, emergency_shortcut: true })),
    pause: () => run(() => api.controller.pause()),
    resume: () => run(() => api.controller.resume()),
    stop: () => run(() => api.controller.stop()),
    emergencyStop: () => run(() => api.controller.emergencyStop()),
    rearm: () => run(() => api.controller.rearm()),
  };
}
