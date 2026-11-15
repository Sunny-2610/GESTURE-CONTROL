import { useEffect, useState } from "react";
import { useAppData } from "./AppContext";
import { api } from "../lib/api";

export type InputMode = "preview" | "live";

export function useInputMode() {
  const { status, refreshStatus } = useAppData();
  const [mode, setMode] = useState<InputMode>("preview");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (status) setMode(status.input_live ? "live" : "preview");
  }, [status?.input_live]);

  const change = async (next: InputMode): Promise<boolean> => {
    if (next === mode || busy) return next === mode;
    setBusy(true);
    setError(null);
    try {
      const res = await api.setInputMode(next === "live");
      setMode(res.live ? "live" : "preview");
      refreshStatus();
      return res.live === (next === "live");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Mode switch failed");
      return false;
    } finally {
      setBusy(false);
    }
  };

  return { mode, error, busy, change };
}
