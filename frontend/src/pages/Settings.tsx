import { SettingsGroup, SettingsRow } from "../components/settings";
import { Button, SegmentedControl, Slider, Switch } from "../components/controls";
import { useSettings } from "../hooks/useSettings";
import { useInputMode } from "../hooks/useInputMode";
import type { Settings } from "../lib/types";

export function SettingsPage() {
  const settings = useSettings();
  const inputMode = useInputMode();

  if (!settings.current || !settings.saved) {
    return <p className="p-6 font-label uppercase tracking-[0.06em] text-ink-muted">Loading…</p>;
  }
  const s = settings.current;

  const num = (path: string[], value: number, min: number, max: number, step: number, format?: (v: number) => string, label?: string) => (
    <Slider
      label={label ?? path.join(".")}
      min={min}
      max={max}
      step={step}
      value={value}
      format={format}
      onChange={(v) => settings.update(path, v)}
    />
  );

  const changedRow = (path: string[], oldSettings: Settings, current: Settings): { changed: boolean; oldDisplay: string | null } => {
    let o: unknown = oldSettings;
    let c: unknown = current;
    for (const key of path) {
      o = (o as Record<string, unknown>)?.[key];
      c = (c as Record<string, unknown>)?.[key];
    }
    const changed = o !== c;
    return { changed, oldDisplay: changed && typeof o === "boolean" ? (o ? "on" : "off") : changed ? String(o) : null };
  };

  const unsaved = settings.dirty ? "1 unsaved" : "0 unsaved";

  return (
    <>
      <div className="border-b border-ink">
        <SettingsGroup name="Cursor">
          <SettingsRow
            label="Sensitivity"
            description="Cursor speed relative to hand movement."
            {...changedRow(["cursor", "sensitivity"], settings.saved, s)}
          >
            {num(["cursor", "sensitivity"], s.cursor.sensitivity, 0.5, 3, 0.1, (v) => v.toFixed(1))}
          </SettingsRow>
          <SettingsRow
            label="Smoothing"
            description="Higher values filter jitter but add lag."
            {...changedRow(["cursor", "smoothing"], settings.saved, s)}
          >
            {num(["cursor", "smoothing"], s.cursor.smoothing, 0, 0.95, 0.05, (v) => v.toFixed(2))}
          </SettingsRow>
          <SettingsRow
            label="Active region margin"
            description="Invisible border of the camera frame the cursor avoids."
            {...changedRow(["cursor", "active_region_margin"], settings.saved, s)}
          >
            {num(["cursor", "active_region_margin"], s.cursor.active_region_margin, 0, 0.4, 0.01, (v) => v.toFixed(2))}
          </SettingsRow>
          <SettingsRow label="Control hand" description="Which hand drives the cursor." {...changedRow(["cursor", "control_hand"], settings.saved, s)}>
            <SegmentedControl
              label="Control hand"
              value={s.cursor.control_hand}
              options={[
                { value: "left", label: "Left" },
                { value: "right", label: "Right" },
              ]}
              onChange={(v) => settings.update(["cursor", "control_hand"], v)}
            />
          </SettingsRow>
        </SettingsGroup>

        <SettingsGroup name="Click">
          <SettingsRow label="Pinch threshold" description="Thumb–index distance that triggers a click." {...changedRow(["click", "pinch_threshold"], settings.saved, s)}>
            {num(["click", "pinch_threshold"], s.click.pinch_threshold, 0.02, 0.15, 0.01, (v) => v.toFixed(2))}
          </SettingsRow>
          <SettingsRow label="Cooldown" description="Minimum seconds between clicks." {...changedRow(["click", "cooldown"], settings.saved, s)}>
            {num(["click", "cooldown"], s.click.cooldown, 0.1, 2, 0.1, (v) => v.toFixed(1))}
          </SettingsRow>
          <SettingsRow label="Double click" description="Send a double click on pinch." {...changedRow(["click", "double_click"], settings.saved, s)}>
            <Switch checked={s.click.double_click} onChange={(v) => settings.update(["click", "double_click"], v)} label="Double click" />
          </SettingsRow>
        </SettingsGroup>

        <SettingsGroup name="Scroll">
          <SettingsRow label="Speed" {...changedRow(["scroll", "speed"], settings.saved, s)}>
            {num(["scroll", "speed"], s.scroll.speed, 0.2, 5, 0.1, (v) => v.toFixed(1))}
          </SettingsRow>
          <SettingsRow label="Dead zone" description="Hand movement below this does not scroll." {...changedRow(["scroll", "dead_zone"], settings.saved, s)}>
            {num(["scroll", "dead_zone"], s.scroll.dead_zone, 0, 0.1, 0.01, (v) => v.toFixed(2))}
          </SettingsRow>
        </SettingsGroup>

        <SettingsGroup name="Volume">
          <SettingsRow label="Sensitivity" {...changedRow(["volume", "sensitivity"], settings.saved, s)}>
            {num(["volume", "sensitivity"], s.volume.sensitivity, 0.1, 3, 0.1, (v) => v.toFixed(1))}
          </SettingsRow>
          <SettingsRow label="Smoothing" {...changedRow(["volume", "smoothing"], settings.saved, s)}>
            {num(["volume", "smoothing"], s.volume.smoothing, 0, 0.95, 0.05, (v) => v.toFixed(2))}
          </SettingsRow>
        </SettingsGroup>

        <SettingsGroup name="Safety">
          <SettingsRow
            label="Input mode"
            description="Preview tracks the hand only. Live dispatches real mouse, click, scroll and volume events."
            invalid={Boolean(inputMode.error)}
            invalidMessage={inputMode.error ?? undefined}
          >
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
          </SettingsRow>
          <SettingsRow label="Emergency hotkey" description="Global shortcut that halts control." {...changedRow(["safety", "emergency_hotkey"], settings.saved, s)}>
            <input
              type="text"
              value={s.safety.emergency_hotkey}
              onChange={(e) => settings.update(["safety", "emergency_hotkey"], e.target.value)}
              className="h-10 w-56 border border-ink bg-transparent px-3 font-mono text-[13px] uppercase"
              aria-label="Emergency hotkey"
            />
          </SettingsRow>
          <SettingsRow label="Auto-disable after no hand" description="Seconds without a hand before control stops. 0 disables." {...changedRow(["safety", "auto_disable_no_hand"], settings.saved, s)}>
            {num(["safety", "auto_disable_no_hand"], s.safety.auto_disable_no_hand, 0, 30, 1, (v) => `${v} s`)}
          </SettingsRow>
          <SettingsRow label="Auto-disable on disconnect" description="Stop control when the frontend link is lost." {...changedRow(["safety", "auto_disable_on_disconnect"], settings.saved, s)}>
            <Switch checked={s.safety.auto_disable_on_disconnect} onChange={(v) => settings.update(["safety", "auto_disable_on_disconnect"], v)} label="Auto-disable on disconnect" />
          </SettingsRow>
        </SettingsGroup>
      </div>

      <div className="flex items-center justify-between px-6 py-4">
        <Button variant="secondary" onClick={() => settings.reset()}>Reset</Button>
        <div className="flex items-center gap-4">
          {settings.error && (
            <span className="border-l-[3px] border-signal-text pl-2 font-label uppercase tracking-[0.06em] text-signal-text">
              {settings.error}
            </span>
          )}
          <span className="font-label uppercase tracking-[0.06em] text-ink-muted">{unsaved}</span>
          <Button onClick={() => settings.save()} disabled={!settings.dirty || settings.saving}>
            Save
          </Button>
        </div>
      </div>
    </>
  );
}
