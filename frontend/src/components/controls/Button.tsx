import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "secondary" | "text";

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
}

export function Button({ variant = "primary", className = "", children, ...rest }: Props) {
  const base =
    "h-10 px-4 font-label uppercase tracking-[0.06em] rounded-sm active:translate-y-px disabled:translate-y-0 disabled:cursor-not-allowed disabled:bg-paper-2 disabled:text-ink-muted";
  const styles: Record<Variant, string> = {
    primary: "bg-ink text-paper border border-ink hover:bg-paper hover:text-ink",
    secondary: "border border-ink bg-transparent text-ink hover:bg-ink hover:text-paper",
    text: "h-auto px-0 py-0 font-label uppercase tracking-[0.06em] text-ink underline underline-offset-2",
  };
  return (
    <button
      type="button"
      className={`${base} ${variant === "text" ? styles.text : styles[variant]} ${className}`}
      {...rest}
    >
      {children}
    </button>
  );
}
