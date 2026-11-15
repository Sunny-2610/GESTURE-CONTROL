import type {
  GestureInfo,
  Settings,
  SettingsPayload,
  Status,
} from "./types";

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      /* keep statusText */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  status: () => fetch("/api/status").then((r) => json<Status>(r)),

  events: () =>
    fetch("/api/events").then((r) => json<import("./types").EventEntry[]>(r)),

  gestures: () =>
    fetch("/api/gestures")
      .then((r) => json<{ gestures: GestureInfo[] }>(r))
      .then((d) => d.gestures),

  toggleGesture: (name: string, enabled: boolean) =>
    fetch(`/api/gestures/${name}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enabled }),
    }).then((r) => json<GestureInfo>(r)),

  getSettings: () => fetch("/api/settings").then((r) => json<SettingsPayload>(r)),

  putSettings: (settings: Partial<Settings>) =>
    fetch("/api/settings", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ settings }),
    }).then((r) => json<{ settings: Settings; unsaved: number }>(r)),

  resetSettings: () =>
    fetch("/api/settings/reset", { method: "POST" }).then((r) =>
      json<{ settings: Settings }>(r),
    ),

  setInputMode: (live: boolean) =>
    fetch("/api/input-mode", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ live }),
    }).then((r) => json<{ live: boolean }>(r)),

  controller: {
    start: (checks: { hand_visible: boolean; nothing_unsaved: boolean; emergency_shortcut: boolean }) =>
      fetch("/api/controller/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ checks }),
      }).then((r) => json<{ state: string; detail: string }>(r)),
    pause: () =>
      fetch("/api/controller/pause", { method: "POST" }).then((r) =>
        json<{ state: string }>(r),
      ),
    resume: () =>
      fetch("/api/controller/resume", { method: "POST" }).then((r) =>
        json<{ state: string }>(r),
      ),
    stop: () =>
      fetch("/api/controller/stop", { method: "POST" }).then((r) =>
        json<{ state: string }>(r),
      ),
    emergencyStop: () =>
      fetch("/api/controller/emergency-stop", { method: "POST" }).then((r) =>
        json<{ state: string }>(r),
      ),
    rearm: () =>
      fetch("/api/controller/rearm", { method: "POST" }).then((r) =>
        json<{ state: string }>(r),
      ),
  },

  camera: {
    start: () =>
      fetch("/api/camera/start", { method: "POST" }).then((r) =>
        json<{ open: boolean; error: string | null }>(r),
      ),
    stop: () =>
      fetch("/api/camera/stop", { method: "POST" }).then((r) =>
        json<{ open: boolean }>(r),
      ),
  },

  videoUrl: () => `/api/video?${Date.now()}`,
};
