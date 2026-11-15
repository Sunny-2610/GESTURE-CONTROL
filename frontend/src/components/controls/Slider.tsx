import { useMemo } from "react";

interface SliderProps {
  label: string;
  min: number;
  max: number;
  step: number;
  value: number;
  onChange: (value: number) => void;
  disabled?: boolean;
  format?: (value: number) => string;
}

export function Slider({ label, min, max, step, value, onChange, disabled, format }: SliderProps) {
  const ticks = useMemo(() => {
    const marks: number[] = [];
    for (let i = 0; i <= 10; i++) marks.push(i / 10);
    return marks;
  }, []);
  const shown = format ? format(value) : String(value);
  return (
    <div className="flex items-center gap-4">
      <div className="relative flex-1">
        <div aria-hidden className="pointer-events-none absolute inset-x-0 top-1/2 flex h-1 -translate-y-1/2 items-center justify-between">
          {ticks.map((t) => (
            <span key={t} className="h-1 w-px bg-ink" />
          ))}
        </div>
        <input
          type="range"
          className="gc-slider relative"
          aria-label={label}
          min={min}
          max={max}
          step={step}
          value={value}
          disabled={disabled}
          onChange={(e) => onChange(Number(e.target.value))}
        />
      </div>
      <span className="w-24 text-right font-mono text-[32px] font-medium leading-8 text-ink">
        {shown}
      </span>
    </div>
  );
}
