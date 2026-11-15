import type { ControllerState } from "../../lib/types";

export function StateBlock({ state }: { state: ControllerState }) {
  const word = state;
  const treatment =
    state === "HALT"
      ? "bg-signal-deep text-paper"
      : state === "ACTIVE" || state === "HOLD"
        ? "bg-ink text-paper"
        : "border-2 border-ink bg-transparent text-ink";
  const plate =
    state === "HOLD" ? (
      <span className="relative inline-block">
        <span aria-hidden className="absolute inset-0 gc-hatch" />
        <span className="relative inline-block bg-paper px-2">{word}</span>
      </span>
    ) : (
      word
    );
  return (
    <div className="p-6">
      <p className="font-label uppercase tracking-[0.06em] text-ink-muted">Control</p>
      <div
        aria-live="polite"
        className={`mt-2 inline-block px-2 py-1 font-mono font-medium ${treatment}`}
        style={{ fontSize: "clamp(40px, 5vw, 64px)", lineHeight: 1.05 }}
        role="status"
      >
        {plate}
      </div>
    </div>
  );
}
