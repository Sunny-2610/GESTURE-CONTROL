import { useCallback, useEffect, useState } from "react";
import { api } from "../lib/api";
import type { Settings } from "../lib/types";

interface UseSettings {
  current: Settings | null;
  saved: Settings | null;
  dirty: boolean;
  error: string | null;
  saving: boolean;
  update: (path: string[], value: unknown) => void;
  save: () => Promise<void>;
  reset: () => Promise<void>;
}

export function useSettings(): UseSettings {
  const [current, setCurrent] = useState<Settings | null>(null);
  const [saved, setSaved] = useState<Settings | null>(null);
  const [dirty, setDirty] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api
      .getSettings()
      .then(({ settings }) => {
        setCurrent(settings);
        setSaved(settings);
      })
      .catch(() => {});
  }, []);

  const update = useCallback((path: string[], value: unknown) => {
    setCurrent((prev) => {
      if (!prev) return prev;
      const next = structuredClone(prev) as unknown as Record<string, unknown>;
      let node: Record<string, unknown> = next;
      for (const key of path.slice(0, -1)) node = node[key] as Record<string, unknown>;
      node[path[path.length - 1]] = value;
      return next as unknown as Settings;
    });
    setDirty(true);
    setError(null);
  }, []);

  const save = useCallback(async () => {
    if (!current || !dirty) return;
    setSaving(true);
    setError(null);
    try {
      const patch: Record<string, unknown> = {};
      for (const group of Object.keys(current) as (keyof Settings)[]) {
        if (JSON.stringify(current[group]) !== JSON.stringify(saved?.[group])) {
          patch[group] = current[group];
        }
      }
      const { settings } = await api.putSettings(patch);
      setCurrent(settings);
      setSaved(settings);
      setDirty(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }, [current, saved, dirty]);

  const reset = useCallback(async () => {
    const { settings } = await api.resetSettings();
    setCurrent(settings);
    setSaved(settings);
    setDirty(false);
    setError(null);
  }, []);

  return { current, saved, dirty, error, saving, update, save, reset };
}
