import type { GestureInfo } from "../../lib/types";
import { PoseDrawing } from "./PoseDrawing";
import { Switch } from "../controls/Switch";

export function GestureCell({
  gesture,
  detected,
  onToggle,
  onOpen,
}: {
  gesture: GestureInfo;
  detected: boolean;
  onToggle: (enabled: boolean) => void;
  onOpen: () => void;
}) {
  const inverted = detected && gesture.enabled;
  return (
    <article
      className={`flex h-full flex-col p-6 ${
        inverted ? "bg-ink text-paper" : "bg-paper text-ink"
      }`}
    >
      <div className="flex items-start justify-between">
        <span className="font-mono text-[48px] font-medium leading-none">
          {String(gesture.priority).padStart(2, "0")}
        </span>
        <Switch
          checked={gesture.enabled}
          onChange={onToggle}
          label={`Enable ${gesture.title}`}
        />
      </div>
      <button
        type="button"
        onClick={onOpen}
        className="mt-2 block w-full text-left"
        aria-label={`Open detail for ${gesture.title}`}
      >
        <div className="flex h-[140px] items-center justify-center">
          <PoseDrawing pose={gesture.name} color={inverted ? "#ECE9E2" : "#1A1916"} />
        </div>
        <h2
          className={`mt-2 font-heading text-[20px] font-semibold leading-7 ${
            gesture.enabled ? "" : "text-ink-muted"
          }`}
        >
          {gesture.title}
        </h2>
        <p className={`mt-1 font-body ${inverted ? "text-paper" : gesture.enabled ? "text-ink" : "text-ink-muted"}`}>
          {gesture.pose}
        </p>
        <p className={`mt-1 font-body ${inverted ? "text-paper/80" : "text-ink-muted"}`}>
          {gesture.action}
        </p>
      </button>
    </article>
  );
}
