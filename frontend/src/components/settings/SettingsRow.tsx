import type { ReactNode } from "react";

export function SettingsGroup({ name, children }: { name: string; children: ReactNode }) {
  return (
    <section className="relative border-b border-ink py-6 pl-12 pr-6" aria-label={name}>
      <span
        aria-hidden
        className="absolute left-0 top-6 origin-top-left -rotate-90 font-label uppercase tracking-[0.06em] text-ink-muted"
        style={{ transform: "rotate(90deg)", transformOrigin: "16px 0" }}
      >
        {name}
      </span>
      <div className="divide-y divide-ink border-t border-ink">
        {children}
      </div>
    </section>
  );
}

export function SettingsRow({
  label,
  description,
  invalid,
  invalidMessage,
  changed,
  oldDisplay,
  children,
}: {
  label: string;
  description?: string;
  invalid?: boolean;
  invalidMessage?: string;
  changed?: boolean;
  oldDisplay?: string | null;
  children: ReactNode;
}) {
  return (
    <div
      className={`relative flex items-center justify-between gap-8 py-4 ${
        invalid ? "border-l-[3px] border-signal-text pl-3" : changed ? "border-l-[3px] border-ink pl-3" : ""
      }`}
    >
      <div className="w-2/5">
        <p className="font-label uppercase tracking-[0.06em] text-ink">{label}</p>
        {description ? <p className="mt-1 font-body text-ink-muted">{description}</p> : null}
      </div>
      <div className="flex flex-1 items-center justify-end gap-3">
        {changed && oldDisplay ? (
          <span className="font-mono text-[13px] text-ink-muted line-through">{oldDisplay}</span>
        ) : null}
        {children}
      </div>
      {invalid && invalidMessage ? (
        <p className="absolute -bottom-1 right-0 font-label uppercase tracking-[0.06em] text-signal-text">
          {invalidMessage}
        </p>
      ) : null}
    </div>
  );
}
