/**
 * Hand-pose line drawings (Design.md 7.14): 1.5px monoline hands in a 160x160
 * viewBox, no fills except square joint markers. Every pose pairs the hand
 * with a small motion hint: an arrow, an icon, or a ring, so a first-time
 * user can read what to do from the picture alone.
 */
export function PoseDrawing({
  pose,
  color,
  size = 160,
}: {
  pose: string;
  color: string;
  size?: number;
}) {
  const s = { stroke: color, strokeWidth: 1.5, fill: "none", strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  const thin = { stroke: color, strokeWidth: 1, fill: "none", strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  const joint = (x: number, y: number, size = 5) => (
    <rect x={x - size / 2} y={y - size / 2} width={size} height={size} fill={color} />
  );

  // standard palm block, wrist open at the bottom, knuckles at y=100
  const palm = <path d="M56 150 L56 110 Q56 100 66 100 L94 100 Q104 100 104 110 L104 150" {...s} />;

  // vertical double-headed arrow (volume / scroll)
  const vArrow = (x: number, y1: number, y2: number) => (
    <g>
      <line x1={x} y1={y1 + 5} x2={x} y2={y2 - 5} {...thin} />
      <path d={`M${x - 4} ${y1 + 6} L${x} ${y1} L${x + 4} ${y1 + 6}`} {...thin} />
      <path d={`M${x - 4} ${y2 - 6} L${x} ${y2} L${x + 4} ${y2 - 6}`} {...thin} />
    </g>
  );

  let body: JSX.Element;
  let marks: JSX.Element | null = null;

  switch (pose) {
    case "closed_fist": {
      body = (
        <>
          <path d="M62 150 L62 106 Q62 96 72 96 L94 96 Q104 96 104 106 L104 150" {...s} />
          {/* curled finger creases */}
          <path d="M70 104 Q76 99 82 104" {...thin} />
          <path d="M84 104 Q90 99 96 104" {...thin} />
          {/* thumb wrapped across the fingers */}
          <path d="M62 124 Q72 112 86 115 Q100 118 102 110" {...s} />
          {/* pause icon: two vertical bars */}
          <rect x={124} y={46} width={6} height={22} {...s} />
          <rect x={134} y={46} width={6} height={22} {...s} />
        </>
      );
      marks = (
        <>
          {joint(72, 96)}
          {joint(94, 96)}
        </>
      );
      break;
    }
    case "pinch_click": {
      body = (
        <>
          {palm}
          {/* index bent down to the contact point */}
          <path d="M66 100 Q62 84 72 76 Q77 72 82 72" {...s} />
          {/* thumb meeting it */}
          <path d="M58 124 Q55 110 66 100 Q74 92 82 76" {...s} />
          {/* middle, ring, pinky loosely curled */}
          <path d="M80 100 Q86 93 80 89" {...s} />
          <path d="M94 100 Q100 93 94 89" {...s} />
          <path d="M104 102 Q110 96 104 92" {...s} />
          {/* contact circle + click burst */}
          <circle cx={82} cy={72} r={4.5} {...thin} />
          <line x1={90} y1={64} x2={97} y2={58} {...thin} />
          <line x1={92} y1={72} x2={102} y2={72} {...thin} />
          <line x1={90} y1={80} x2={97} y2={86} {...thin} />
        </>
      );
      marks = joint(82, 72, 6);
      break;
    }
    case "three_finger": {
      body = (
        <>
          {palm}
          {/* index, middle, ring raised and spread slightly */}
          <path d="M66 100 Q60 74 58 50" {...s} />
          <path d="M80 100 Q80 72 80 46" {...s} />
          <path d="M94 100 Q98 76 100 54" {...s} />
          {/* pinky and thumb curled in */}
          <path d="M104 102 Q110 94 104 90" {...s} />
          <path d="M58 120 Q50 114 54 106" {...s} />
          {/* speaker with three volume bars */}
          <path d="M20 62 L28 62 L36 54 L36 82 L28 74 L20 74 Z" {...thin} />
          <line x1={42} y1={62} x2={42} y2={70} {...thin} />
          <line x1={48} y1={57} x2={48} y2={75} {...thin} />
          <line x1={54} y1={52} x2={54} y2={80} {...thin} />
          {/* volume arrow */}
          {vArrow(126, 54, 100)}
        </>
      );
      marks = (
        <>
          {joint(58, 50)}
          {joint(80, 46)}
          {joint(100, 54)}
        </>
      );
      break;
    }
    case "two_finger_scroll": {
      body = (
        <>
          {palm}
          {/* index and middle raised in a V */}
          <path d="M66 100 Q58 74 56 52" {...s} />
          <path d="M80 100 Q82 72 84 48" {...s} />
          {/* ring and pinky curled, thumb tucked */}
          <path d="M94 100 Q100 94 94 90" {...s} />
          <path d="M104 102 Q110 96 104 92" {...s} />
          <path d="M58 122 Q50 116 54 108" {...s} />
          {/* scroll arrow */}
          {vArrow(126, 54, 100)}
          {/* mouse with wheel */}
          <rect x={22} y={116} width={20} height={26} rx={6} {...s} />
          <line x1={32} y1={123} x2={32} y2={132} {...thin} />
        </>
      );
      marks = (
        <>
          {joint(56, 52)}
          {joint(84, 48)}
        </>
      );
      break;
    }
    case "pointer": {
      body = (
        <>
          {palm}
          {/* only the index raised */}
          <path d="M66 100 Q64 72 64 46" {...s} />
          <path d="M80 100 Q86 94 80 90" {...s} />
          <path d="M94 100 Q100 94 94 90" {...s} />
          <path d="M104 102 Q110 96 104 92" {...s} />
          <path d="M58 122 Q50 116 54 108" {...s} />
          {/* dwell-click ring around the fingertip */}
          <circle cx={64} cy={42} r={11} {...thin} strokeDasharray="4 3" />
          {/* cursor arrow icon */}
          <path d="M118 36 L118 58 L124 52 L128 62 L132 60 L128 51 L136 51 Z" {...thin} />
        </>
      );
      marks = joint(64, 46);
      break;
    }
    case "open_palm":
    default: {
      body = (
        <>
          {/* palm shifted up so the swipe arrow fits underneath */}
          <path d="M58 134 L58 100 Q58 92 66 92 L94 92 Q102 92 102 100 L102 134" {...s} />
          {/* five fingers spread */}
          <path d="M66 92 Q60 68 56 44" {...s} />
          <path d="M80 92 Q80 66 78 38" {...s} />
          <path d="M94 92 Q97 66 99 40" {...s} />
          <path d="M102 96 Q108 76 112 56" {...s} />
          <path d="M60 116 Q48 108 46 94 Q46 88 52 88" {...s} />
          {/* horizontal swipe arrow with back/forward chevrons */}
          <line x1={32} y1={146} x2={128} y2={146} {...thin} />
          <path d="M37 141 L32 146 L37 151" {...thin} />
          <path d="M123 141 L128 146 L123 151" {...thin} />
          <path d="M26 140 L20 146 L26 152" {...thin} />
          <path d="M134 140 L140 146 L134 152" {...thin} />
        </>
      );
      marks = (
        <>
          {joint(56, 44)}
          {joint(78, 38)}
          {joint(99, 40)}
          {joint(112, 56)}
        </>
      );
      break;
    }
  }

  return (
    <svg viewBox="0 0 160 160" width={size} height={size} aria-hidden>
      {body}
      {marks}
    </svg>
  );
}
