export function Switch({
  checked,
  onChange,
  label,
  disabled,
}: {
  checked: boolean;
  onChange: (value: boolean) => void;
  label: string;
  disabled?: boolean;
}) {
  const cell = (value: boolean, text: string) => (
    <span
      aria-hidden
      className={`flex h-6 w-7 items-center justify-center font-mono text-[10px] uppercase ${
        checked === value ? "bg-ink text-paper" : "text-ink-muted"
      }`}
    >
      {text}
    </span>
  );
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={`flex h-6 w-14 items-stretch border border-ink disabled:cursor-not-allowed disabled:border-ink-muted ${
        disabled ? "opacity-60" : ""
      }`}
    >
      {cell(false, "OFF")}
      {cell(true, "ON")}
    </button>
  );
}

export function SegmentedControl<T extends string>({
  value,
  options,
  onChange,
  label,
}: {
  value: T;
  options: { value: T; label: string }[];
  onChange: (value: T) => void;
  label: string;
}) {
  return (
    <div role="radiogroup" aria-label={label} className="flex h-6 w-14 items-stretch border border-ink">
      {options.map((opt) => {
        const selected = opt.value === value;
        return (
          <button
            key={opt.value}
            type="button"
            role="radio"
            aria-checked={selected}
            onClick={() => onChange(opt.value)}
            className={`flex-1 font-mono text-[10px] uppercase ${
              selected ? "bg-ink text-paper" : "text-ink-muted hover:text-ink"
            }`}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
