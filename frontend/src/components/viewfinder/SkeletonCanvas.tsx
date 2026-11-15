import { useEffect, useRef } from "react";
import type { WsHand } from "../../lib/types";

const CONNECTIONS: [number, number][] = [
  [0, 1], [1, 2], [2, 3], [3, 4],
  [0, 5], [5, 6], [6, 7], [7, 8],
  [5, 9], [9, 10], [10, 11], [11, 12],
  [9, 13], [13, 14], [14, 15], [15, 16],
  [13, 17], [17, 18], [18, 19], [19, 20],
  [0, 17],
];
const FINGERTIPS = [4, 8, 12, 16, 20];

export function SkeletonCanvas({
  hands,
  mirrored,
  color,
}: {
  hands: WsHand[];
  mirrored: boolean;
  color: string;
}) {
  const canvas = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const el = canvas.current;
    if (!el) return;
    const ctx = el.getContext("2d");
    if (!ctx) return;
    const dpr = window.devicePixelRatio || 1;
    const w = el.clientWidth;
    const h = el.clientHeight;
    if (el.width !== w * dpr || el.height !== h * dpr) {
      el.width = w * dpr;
      el.height = h * dpr;
    }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);
    ctx.strokeStyle = color;
    ctx.fillStyle = color;
    for (const hand of hands) {
      const pts = hand.landmarks.map(([x, y]) => {
        const px = mirrored ? (1 - x) * w : x * w;
        const py = y * h;
        return [px, py] as const;
      });
      ctx.lineWidth = 1.5;
      for (const [a, b] of CONNECTIONS) {
        const [x1, y1] = pts[a];
        const [x2, y2] = pts[b];
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.stroke();
      }
      for (let i = 0; i < pts.length; i++) {
        const [x, y] = pts[i];
        const size = FINGERTIPS.includes(i) ? 6 : 5;
        ctx.fillRect(x - size / 2, y - size / 2, size, size);
      }
    }
  });

  return <canvas ref={canvas} className="pointer-events-none absolute inset-0 h-full w-full" aria-hidden />;
}
