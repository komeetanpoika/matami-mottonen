// Fixed Art Nouveau golden corner overlay — pointer-events: none throughout

const gold = '#c9a058'
const goldLight = '#e8c878'
const goldDim = '#a07838'

const petalAngles = [0, 45, 90, 135, 180, 225, 270, 315]

// All paths drawn for top-left; other corners are CSS mirror transforms
function CornerPaths() {
  return (
    <g opacity="0.52">
      {/* Outer L-border */}
      <path d="M 220,18 L 38,18 Q 18,18 18,38 L 18,220"
        stroke={gold} strokeWidth="0.8"/>
      {/* Inner parallel L — dashed */}
      <path d="M 220,26 L 44,26 Q 26,26 26,44 L 26,220"
        stroke={goldDim} strokeWidth="0.5" strokeDasharray="4 3"/>

      {/* Corner rosette */}
      <circle cx="38" cy="38" r="7" stroke={goldLight} strokeWidth="0.9"/>
      <circle cx="38" cy="38" r="3.5" fill={gold} opacity="0.7"/>
      {petalAngles.map((deg, i) => {
        const r = (deg * Math.PI) / 180
        return (
          <circle key={i}
            cx={38 + Math.cos(r) * 10}
            cy={38 + Math.sin(r) * 10}
            r="1.8" fill={goldLight} opacity="0.55"
          />
        )
      })}

      {/* Flowing tendril along top edge */}
      <path d="M 52,18 Q 58,10 66,16 Q 72,22 80,14 Q 86,8 94,16 Q 100,22 110,15 Q 118,9 126,17"
        stroke={gold} strokeWidth="0.9"/>
      <path d="M 66,16 Q 64,8 70,7 Q 74,8 70,13" fill={gold} opacity="0.45"/>
      <path d="M 94,16 Q 92,8 98,7 Q 102,8 98,13" fill={gold} opacity="0.45"/>
      <circle cx="80" cy="11" r="2" fill={goldLight} opacity="0.4"/>
      <circle cx="110" cy="12" r="1.5" fill={goldLight} opacity="0.35"/>

      {/* Second wave along top */}
      <path d="M 134,18 Q 140,12 148,17 Q 154,22 162,15 Q 168,10 176,16"
        stroke={goldDim} strokeWidth="0.6"/>
      <path d="M 148,17 Q 146,10 152,9 Q 156,10 152,15" fill={goldDim} opacity="0.4"/>

      {/* Flowing tendril along left edge */}
      <path d="M 18,52 Q 10,58 16,66 Q 22,72 14,80 Q 8,86 16,94 Q 22,100 15,110 Q 9,118 17,126"
        stroke={gold} strokeWidth="0.9"/>
      <path d="M 16,66 Q 8,64 7,70 Q 8,74 13,70" fill={gold} opacity="0.45"/>
      <path d="M 16,94 Q 8,92 7,98 Q 8,102 13,98" fill={gold} opacity="0.45"/>
      <circle cx="11" cy="80" r="2" fill={goldLight} opacity="0.4"/>
      <circle cx="12" cy="110" r="1.5" fill={goldLight} opacity="0.35"/>

      {/* Second wave down left */}
      <path d="M 18,134 Q 12,140 17,148 Q 22,154 15,162 Q 10,168 16,176"
        stroke={goldDim} strokeWidth="0.6"/>
      <path d="M 17,148 Q 10,146 9,152 Q 10,156 15,152" fill={goldDim} opacity="0.4"/>

      {/* Inner diagonal filigree from corner */}
      <path d="M 26,26 Q 34,32 40,28 Q 46,24 50,32 Q 54,40 48,44"
        stroke={goldLight} strokeWidth="0.7" opacity="0.5"/>
      <circle cx="50" cy="33" r="1.4" fill={goldLight} opacity="0.45"/>

      {/* Tiny extra leaf sprigs near corner */}
      <path d="M 36,52 Q 30,56 32,62 Q 36,65 38,60" fill={goldDim} opacity="0.35"/>
      <path d="M 52,36 Q 56,30 62,32 Q 65,36 60,38" fill={goldDim} opacity="0.35"/>
    </g>
  )
}

type Corner = 'tl' | 'tr' | 'bl' | 'br'

const transforms: Record<Corner, string> = {
  tl: 'none',
  tr: 'scaleX(-1)',
  bl: 'scaleY(-1)',
  br: 'scale(-1,-1)',
}

const positions: Record<Corner, React.CSSProperties> = {
  tl: { top: 0, left: 0 },
  tr: { top: 0, right: 0 },
  bl: { bottom: 0, left: 0 },
  br: { bottom: 0, right: 0 },
}

function Corner({ id }: { id: Corner }) {
  return (
    <svg
      width="220" height="220"
      viewBox="0 0 220 220"
      fill="none"
      style={{
        position: 'fixed',
        pointerEvents: 'none',
        zIndex: 200,
        transform: transforms[id],
        ...positions[id],
      }}
    >
      <CornerPaths />
    </svg>
  )
}

export default function CornerFrames() {
  return (
    <>
      <Corner id="tl" />
      <Corner id="tr" />
      <Corner id="bl" />
      <Corner id="br" />
    </>
  )
}
