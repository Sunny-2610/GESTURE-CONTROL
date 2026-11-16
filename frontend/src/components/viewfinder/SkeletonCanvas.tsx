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
const INDEX_TIP = 8;

export function SkeletonCanvas({
  hands,
  mirrored,
  color,
  dwell = 0,
}: {
  hands: WsHand[];
  mirrored: boolean;
  color: string;
  dwell?: number;
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
    // dwell-click progress ring around the index fingertip
    if (dwell > 0 && hands.length > 0) {
      const hand = hands.find((hd) => hd.role === "primary") ?? hands[0];
      const [tip] = hand.landmarks[INDEX_TIP];
      const [, tipY] = hand.landmarks[INDEX_TIP];
      const cx = mirrored ? (1 - tip) * w : tip * w;
      const cy = tipY * h;
      const r = 16;
      ctx.save();
      ctx.lineWidth = 2;
      // faint full ring
      ctx.globalAlpha = 0.3;
      ctx.beginPath();
      ctx.arc(cx, cy, r, 0, Math.PI * 2);
      ctx.stroke();
      // progress arc (starts at the top, clockwise)
      ctx.globalAlpha = 1;
      ctx.beginPath();
      ctx.arc(cx, cy, r, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * Math.min(1, dwell));
      ctx.stroke();
      ctx.restore();
    }
  });

  return <canvas ref={canvas} className="pointer-events-none absolute inset-0 h-full w-full" aria-hidden />;
}
