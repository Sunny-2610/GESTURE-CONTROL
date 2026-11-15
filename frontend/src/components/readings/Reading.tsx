import { useEffect, useRef } from "react";

export function Sparkline({ value, height = 48 }: { value: number | null; height?: number }) {
  const history = useRef<number[]>([]);
  const canvas = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (value != null) {
      history.current.push(value);
      if (history.current.length > 60 * 30) history.current.shift();
    }
    const el = canvas.current;
    if (!el) return;
    const ctx = el.getContext("2d");
    if (!ctx) return;
    const dpr = window.devicePixelRatio || 1;
    const w = el.clientWidth;
    el.width = w * dpr;
    el.height = height * dpr;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, w, height);
    const data = history.current;
    if (data.length < 2) return;
    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;
    ctx.strokeStyle = "#1A1916";
    ctx.lineWidth = 1;
    ctx.beginPath();
    data.forEach((v, i) => {
      const x = (i / (data.length - 1)) * w;
      const y = height - ((v - min) / range) * (height - 8) - 4;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
    const lastX = w;
    const lastV = data[data.length - 1];
    const lastY = height - ((lastV - min) / range) * (height - 8) - 4;
    ctx.fillStyle = "#1A1916";
    ctx.fillRect(lastX - 4, lastY - 2, 4, 4);
  }, [value, height]);

  return <canvas ref={canvas} className="block w-full" style={{ height }} aria-hidden />;
}

export function Reading({
  label,
  value,
  suffix,
  spark,
}: {
  label: string;
  value: number | null;
  suffix?: string;
  spark?: boolean;
}) {
  return (
    <div className="p-6">
      <p className="font-mono font-medium text-ink" style={{ fontSize: "clamp(40px, 4.5vw, 64px)", lineHeight: 1.05 }}>
        {value != null ? value.toFixed(1) : <span className="text-ink-muted">—</span>}
        {value != null && suffix ? <span className="ml-2 font-label text-ink-muted">{suffix}</span> : null}
      </p>
      <p className="mt-1 font-label uppercase tracking-[0.06em] text-ink-muted">{label}</p>
      {spark ? <div className="mt-4"><Sparkline value={value} /></div> : null}
    </div>
  );
}
