import type { ReactNode } from "react";

export function OverlayChip({
  position,
  children,
}: {
  position: "top-left" | "top-right" | "bottom-left" | "bottom-right";
  children: ReactNode;
}) {
  const map: Record<string, string> = {
    "top-left": "left-3 top-3",
    "top-right": "right-3 top-3",
    "bottom-left": "bottom-3 left-3",
    "bottom-right": "bottom-3 right-3",
  };
  return (
    <span
      className={`absolute bg-paper/90 px-2 py-1 font-label uppercase tracking-[0.06em] text-ink ${map[position]}`}
    >
      {children}
    </span>
  );
}

export function CornerBrackets() {
  const corner = "absolute h-6 w-6 border-ink";
  return (
    <>
      <span aria-hidden className={`${corner} left-3 top-3 border-l-2 border-t-2`} />
      <span aria-hidden className={`${corner} right-3 top-3 border-r-2 border-t-2`} />
      <span aria-hidden className={`${corner} bottom-3 left-3 border-b-2 border-l-2`} />
      <span aria-hidden className={`${corner} bottom-3 right-3 border-b-2 border-r-2`} />
    </>
  );
}

export function EmptyState({ label }: { label: string }) {
  return (
    <div className="absolute inset-0 flex flex-col items-center justify-center bg-paper-2">
      <svg width="48" height="48" viewBox="0 0 48 48" aria-hidden className="text-ink">
        <line x1="24" y1="0" x2="24" y2="14" stroke="currentColor" strokeWidth="1" />
        <line x1="24" y1="34" x2="24" y2="48" stroke="currentColor" strokeWidth="1" />
        <line x1="0" y1="24" x2="14" y2="24" stroke="currentColor" strokeWidth="1" />
        <line x1="34" y1="24" x2="48" y2="24" stroke="currentColor" strokeWidth="1" />
        <circle cx="24" cy="24" r="10" stroke="currentColor" strokeWidth="1" fill="none" />
      </svg>
      <p className="mt-4 font-label uppercase tracking-[0.06em] text-ink">{label}</p>
    </div>
  );
}

export function ActiveRegion({ margin = 0.08 }: { margin?: number }) {
  const style = {
    top: `${margin * 100}%`,
    left: `${margin * 100}%`,
    right: `${margin * 100}%`,
    bottom: `${margin * 100}%`,
  };
  return (
    <div className="absolute" style={style} aria-hidden>
      <div className="h-full w-full border border-dashed border-ink" />
      <span className="absolute -top-[16px] left-0 bg-paper/90 px-2 py-0.5 font-label uppercase tracking-[0.06em] text-ink">
        Active region
      </span>
    </div>
  );
}
