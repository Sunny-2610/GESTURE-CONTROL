import { useState } from "react";
import { Viewfinder } from "../components/viewfinder";
import { StateBlock, Reading, EventLog } from "../components/readings";
import { Button, Sheet, SegmentedControl } from "../components/controls";
import { Shortcut } from "../components/controls/Keycap";
import { useAppData } from "../hooks/AppContext";
import { useInputMode } from "../hooks/useInputMode";
import { api } from "../lib/api";

function ArmingSheet({ open, onClose, onArmed }: { open: boolean; onClose: () => void; onArmed: () => void }) {
  const [checks, setChecks] = useState({ hand_visible: false, nothing_unsaved: false, emergency_shortcut: false });
  const [error, setError] = useState<string | null>(null);
  const all = Object.values(checks).every(Boolean);
  const count = Object.values(checks).filter(Boolean).length;

  const arm = async () => {
    try {
      await api.controller.start(checks);
      setError(null);
      onArmed();
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Arming failed");
    }
  };

  const rows = [
    { key: "hand_visible", text: "My hand is visible in the preview.", hint: "Optical tracking confidence > 90% required" },
    { key: "nothing_unsaved", text: "Nothing important is unsaved.", hint: "Active window receives dispatched OS input events" },
    { key: "emergency_shortcut", text: "I know the emergency shortcut.", hint: "" },
  ] as const;

  return (
    <Sheet open={open} onClose={onClose} title="Arm control" width="sheet">
      <div className="flex h-full flex-col justify-between p-8">
        <div>
          <div className="mb-6 flex items-start justify-between border-b border-ink pb-4">
            <div>
              <p className="font-label uppercase tracking-[0.06em] text-ink-muted">Safety pre-arm</p>
              <h1 className="mt-1 text-[28px] font-semibold uppercase leading-8">Arm control</h1>
            </div>
            <button type="button" onClick={onClose} className="border border-ink px-2.5 py-1 font-label uppercase tracking-[0.06em] hover:bg-ink hover:text-paper">
              [ Esc ]
            </button>
          </div>
          <div className="mb-8 border-l-2 border-ink bg-paper-2 py-1 pl-3">
            <p className="font-label uppercase leading-relaxed tracking-[0.06em] text-ink">
              Confirm system readiness before binding HID input pipeline. Three hard interlock checks required.
            </p>
          </div>
          <div className="space-y-6">
            {rows.map((row) => (
              <label key={row.key} className="flex cursor-pointer items-start gap-4">
                <input
                  type="checkbox"
                  checked={checks[row.key]}
                  onChange={(e) => setChecks((c) => ({ ...c, [row.key]: e.target.checked }))}
                  className="mt-1 h-[22px] w-[22px] appearance-none border-2 border-ink bg-paper checked:bg-ink"
                />
                <span>
                  <span className="text-[18px] font-semibold leading-[22px]">{row.text}</span>
                  {row.key === "emergency_shortcut" ? (
                    <span className="mt-3 flex items-center gap-2">
                      <Shortcut keys={["Ctrl", "Alt", "Shift", "Q"]} />
                    </span>
                  ) : (
                    <span className="mt-1 block font-label uppercase tracking-[0.06em] text-ink-muted">{row.hint}</span>
                  )}
                </span>
              </label>
            ))}
          </div>
        </div>
        <div>
          <div className="mb-4 flex items-start gap-2 border border-ink bg-paper-2 p-3">
            <span className="font-mono font-bold text-ink">!</span>
            <p className="font-label uppercase leading-relaxed tracking-[0.06em] text-ink-muted">
              Disengage at any time via hardware interrupt or emergency kill switch.
            </p>
          </div>
          <div className="flex items-center gap-3 border-t border-ink pt-4">
            <button
              type="button"
              onClick={onClose}
              className="h-12 border border-ink px-6 font-label font-semibold uppercase tracking-[0.06em] hover:bg-ink hover:text-paper"
            >
              [ Cancel ]
            </button>
            <button
              type="button"
              disabled={!all}
              onClick={arm}
              className="h-12 flex-1 border border-ink bg-ink font-label font-semibold uppercase tracking-wider text-paper disabled:cursor-not-allowed disabled:opacity-40"
            >
              {all ? "Arm" : "[ Interlock pending ]"}
            </button>
          </div>
          <div className="mt-3 flex items-center justify-between font-label uppercase tracking-[0.06em] text-ink-muted">
            <span>Status: interlock {all ? "complete" : `incomplete (${count}/3)`}</span>
            <span className="font-semibold text-ink">Safety gate 01</span>
          </div>
          {error && <p className="mt-2 border-l-[3px] border-signal-text pl-3 font-label uppercase tracking-[0.06em] text-signal-text">{error}</p>}
        </div>
      </div>
    </Sheet>
  );
}

export function Dashboard() {
  const { status, state, hands, fps, events, detectedGesture, confidence, cursor, cameraOpen } = useAppData();
  const inputMode = useInputMode();
  const [armingOpen, setArmingOpen] = useState(false);

  const primaryAction = () => {
    if (state === "OFF") setArmingOpen(true);
    else if (state === "ACTIVE") api.controller.pause().catch(() => {});
    else if (state === "HOLD") api.controller.resume().catch(() => {});
  };
  const primaryLabel =
    state === "OFF" ? "Start control" : state === "ACTIVE" ? "Pause" : state === "HOLD" ? "Resume" : "Start control";
  const primaryDisabled = state === "HALT" || state === "ARMED";

  return (
    <div className="grid grid-cols-3 divide-x divide-ink border-b border-ink">
      <div className="col-span-2 p-8">
        <Viewfinder
          cameraOpen={cameraOpen}
          hands={hands}
          state={state}
          liveInput={status?.input_live ?? false}
          gesture={detectedGesture}
          confidence={confidence}
          cursor={cursor}
          emptyLabel={status?.camera.busy ? "Camera busy" : "Camera off"}
          onEmptyAction={
            cameraOpen ? undefined : (
              <Button variant="secondary" onClick={() => api.camera.start().catch(() => {})}>
                Start camera
              </Button>
            )
          }
        />
        {state === "OFF" && (
          <p className="mt-4 max-w-[70ch] font-body text-ink-muted">
            No actions are sent until control is started.
          </p>
        )}
      </div>

      <div className="flex flex-col">
        <StateBlock state={state} />
        <div className="border-t border-ink">
          <Reading label="Frames per second" value={fps} spark />
        </div>
        <div className="flex-1 border-t border-ink">
          <EventLog events={events} max={8} />
        </div>
        <div className="border-t border-ink px-6 py-4">
          <div className="flex items-center justify-between gap-3">
            <span className="font-label uppercase tracking-[0.06em] text-ink-muted">Input mode</span>
            <SegmentedControl
              label="Input mode"
              wide
              value={inputMode.mode}
              options={[
                { value: "preview", label: "Preview" },
                { value: "live", label: "Live" },
              ]}
              onChange={inputMode.change}
            />
          </div>
          {inputMode.error && (
            <p className="mt-2 border-l-[3px] border-signal-text pl-3 font-label uppercase tracking-[0.06em] text-signal-text">
              {inputMode.error}
            </p>
          )}
        </div>
        <div className="flex flex-wrap gap-3 border-t border-ink p-6">
          <Button onClick={primaryAction} disabled={primaryDisabled}>
            {primaryLabel}
          </Button>
          {state !== "OFF" && state !== "HALT" && (
            <Button variant="secondary" onClick={() => api.controller.stop().catch(() => {})}>
              Stop control
            </Button>
          )}
          {state === "HALT" && (
            <Button variant="secondary" onClick={() => api.controller.rearm().catch(() => {})}>
              Re-arm
            </Button>
          )}
        </div>
      </div>

      <ArmingSheet open={armingOpen} onClose={() => setArmingOpen(false)} onArmed={() => undefined} />
    </div>
  );
}
