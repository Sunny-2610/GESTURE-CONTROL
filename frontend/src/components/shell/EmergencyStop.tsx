import { api } from "../../lib/api";

export function EmergencyStop() {
  const fire = () => {
    api.controller.emergencyStop().catch(() => {
      /* the request is attempted even when the backend is gone */
    });
  };
  return (
    <button
      type="button"
      onClick={fire}
      aria-label="Emergency stop: halt all control immediately"
      className="h-12 min-w-[176px] bg-signal-deep px-4 py-1 text-left"
    >
      <span className="block font-mono text-[13px] font-semibold uppercase leading-4 tracking-[0.06em] text-ink">
        Emergency Stop
      </span>
      <span className="mt-0.5 block font-mono text-[11px] uppercase leading-3 tracking-widest text-ink">
        Ctrl+Alt+Shift+Q
      </span>
    </button>
  );
}
