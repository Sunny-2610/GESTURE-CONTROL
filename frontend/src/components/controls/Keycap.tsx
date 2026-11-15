export function Keycap({ label }: { label: string }) {
  return (
    <kbd className="inline-flex h-7 items-center rounded-sm border border-ink border-b-2 px-3 font-mono text-[13px] uppercase text-ink">
      {label}
    </kbd>
  );
}

export function Shortcut({ keys }: { keys: string[] }) {
  return (
    <span className="inline-flex items-center gap-1">
      {keys.map((k, i) => (
        <span key={i} className="inline-flex items-center gap-1">
          {i > 0 && <span className="font-mono text-[10px] text-ink-muted">+</span>}
          <Keycap label={k} />
        </span>
      ))}
    </span>
  );
}
