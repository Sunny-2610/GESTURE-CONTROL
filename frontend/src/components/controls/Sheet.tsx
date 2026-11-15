import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import { useReducedMotion } from "../../hooks/useBackend";

interface SheetProps {
  open: boolean;
  onClose: () => void;
  title: string;
  width?: "sheet" | "drawer";
  children: ReactNode;
}

export function Sheet({ open, onClose, title, width = "drawer", children }: SheetProps) {
  const reduced = useReducedMotion();
  const ref = useRef<HTMLDivElement>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    if (open) setMounted(true);
    else setMounted(false);
  }, [open]);

  useEffect(() => {
    if (!mounted) return;
    const previous = document.activeElement as HTMLElement | null;
    ref.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
      if (e.key === "Tab" && ref.current) {
        const focusables = ref.current.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
        );
        if (focusables.length === 0) return;
        const first = focusables[0];
        const last = focusables[focusables.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("keydown", onKey);
      previous?.focus();
    };
  }, [mounted, onClose]);

  if (!mounted) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div
        className="absolute inset-0 bg-ink/50"
        onClick={onClose}
        aria-hidden
      />
      <div
        ref={ref}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        tabIndex={-1}
        className={`relative h-full overflow-y-auto border-l-4 border-ink bg-paper outline-none ${
          width === "sheet" ? "w-[520px]" : "w-[380px]"
        } ${reduced ? "" : "animate-sheet-in"}`}
        style={
          reduced
            ? undefined
            : { animation: "sheet-in 160ms cubic-bezier(0.2, 0, 0, 1)" }
        }
      >
        {children}
      </div>
      <style>{`@keyframes sheet-in { from { transform: translateX(100%); } to { transform: translateX(0); } }`}</style>
    </div>
  );
}
