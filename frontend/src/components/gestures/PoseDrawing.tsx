/**
 * Hand-pose line drawings (Design.md 7.14): 1.5px monoline hands in a 140px-high
 * viewBox. `highlight` marks the landmarks that matter for the pose, and thin
 * dimension lines show where a distance matters (pinch gap).
 */
export function PoseDrawing({ pose, color }: { pose: string; color: string }) {
  const stroke = { stroke: color, strokeWidth: 1.5, fill: "none", strokeLinecap: "round" as const };
  const W = 120;
  const H = 140;
  const joint = (x: number, y: number, size = 5) => (
    <rect x={x - size / 2} y={y - size / 2} width={size} height={size} fill={color} />
  );

  // palm block anchored at wrist (60, 120)
  const palm = (
    <path d="M40 120 L38 88 Q38 78 48 78 L72 78 Q82 78 82 88 L80 120 Z" {...stroke} />
  );

  const fingerUp = (x: number, tipY: number) => (
    <>
      <line x1={x} y1={80} x2={x} y2={tipY} {...stroke} />
    </>
  );

  let fingers: JSX.Element;
  let marks: JSX.Element | null = null;
  let dims: JSX.Element | null = null;

  switch (pose) {
    case "closed_fist":
      fingers = (
        <>
          <path d="M44 80 Q44 70 52 70 L76 70 Q84 70 84 78 L84 86" {...stroke} />
          <path d="M44 78 Q36 74 38 66" {...stroke} />
        </>
      );
      marks = joint(60, 78);
      break;
    case "volume_mode":
      fingers = (
        <>
          <path d="M44 80 Q44 70 52 70 L74 70 Q82 70 82 78 L82 86" {...stroke} />
          <path d="M42 82 Q30 74 26 58 Q25 52 31 52 L34 54" {...stroke} />
        </>
      );
      marks = (
        <>
          {joint(31, 53)}
          {joint(60, 78)}
        </>
      );
      dims = (
        <line x1="34" y1="52" x2="34" y2="16" {...stroke} strokeDasharray="3 3" />
      );
      break;
    case "two_finger_scroll":
      fingers = (
        <>
          {fingerUp(50, 34)}
          {fingerUp(62, 32)}
          <path d="M72 80 Q72 72 78 74" {...stroke} />
          <path d="M80 82 Q84 76 88 78" {...stroke} />
        </>
      );
      marks = (
        <>
          {joint(50, 34)}
          {joint(62, 32)}
        </>
      );
      break;
    case "pinch_click":
      fingers = (
        <>
          <path d="M50 80 Q48 62 54 52 Q58 46 64 48" {...stroke} />
          <path d="M42 84 Q32 72 40 62 Q44 58 50 60 Q56 62 60 58 Q64 52 70 54" {...stroke} />
          <path d="M74 80 Q76 74 82 76" {...stroke} />
          <path d="M80 82 Q86 78 88 82" {...stroke} />
        </>
      );
      marks = (
        <>
          {joint(64, 48)}
          {joint(66, 55)}
        </>
      );
      dims = (
        <>
          <line x1="66" y1="48" x2="66" y2="55" stroke={color} strokeWidth="1" />
          <line x1="80" y1="48" x2="80" y2="55" stroke={color} strokeWidth="1" strokeDasharray="2 2" />
        </>
      );
      break;
    case "pointer":
      fingers = (
        <>
          {fingerUp(52, 30)}
          <path d="M64 80 Q64 72 70 74" {...stroke} />
          <path d="M74 82 Q78 76 84 78" {...stroke} />
          <path d="M84 84 Q88 80 92 84" {...stroke} />
        </>
      );
      marks = joint(52, 30);
      break;
    case "open_palm":
    default:
      fingers = (
        <>
          {fingerUp(42, 44)}
          {fingerUp(54, 32)}
          {fingerUp(66, 30)}
          {fingerUp(78, 36)}
          <path d="M40 92 Q32 86 34 78 L40 78" {...stroke} />
        </>
      );
      marks = null;
      break;
  }

  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="140" height="140" aria-hidden>
      {palm}
      {fingers}
      {marks}
      {dims}
    </svg>
  );
}
