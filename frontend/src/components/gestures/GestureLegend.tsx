import type { GestureInfo } from "../../lib/types";
import { PoseDrawing } from "./PoseDrawing";

const CHEAT_SHEET: { name: string; label: string }[] = [
  { name: "closed_fist", label: "Pause" },
  { name: "pinch_click", label: "Click" },
  { name: "three_finger", label: "Volume" },
  { name: "two_finger_scroll", label: "Scroll" },
  { name: "pointer", label: "Cursor" },
  { name: "open_palm", label: "Swipe" },
];

/** Small six-up cheat sheet of every pose with its label. */
export function GestureLegend({ color = "#1A1916" }: { color?: string }) {
  return (
    <div className="grid grid-cols-3 gap-x-6 gap-y-4 max-[599px]:grid-cols-2">
      {CHEAT_SHEET.map((g) => (
        <div key={g.name} className="flex flex-col items-center">
          <PoseDrawing pose={g.name} color={color} size={72} />
          <span className="mt-1 font-label text-[11px] uppercase tracking-[0.06em]">
            {g.label}
          </span>
        </div>
      ))}
    </div>
  );
}

export type { GestureInfo };
