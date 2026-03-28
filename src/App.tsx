import { useState } from 'react'
import './index.css'
import { Lang, langLabels, translations } from './translations'
import CornerFrames from './CornerFrames'

const services = (t: ReturnType<typeof translations[Lang extends string ? Lang : never]>) => [
  { icon: '🪬', title: t.service1Title, desc: t.service1Desc },
  { icon: '🃏', title: t.service2Title, desc: t.service2Desc },
  { icon: '🖼',  title: t.service3Title, desc: t.service3Desc },
]

// Pre-placed organic scatter
const scatter: { glyph: string; x: number; y: number; rot: number; size: number; op: number }[] = [
  { glyph: '🌿', x: 3,  y: 4,  rot: -30, size: 3.8, op: 0.10 },
  { glyph: '🍃', x: 9,  y: 11, rot: 15,  size: 2.2, op: 0.07 },
  { glyph: '🌿', x: 1,  y: 22, rot: 42,  size: 4.5, op: 0.08 },
  { glyph: '🍃', x: 14, y: 6,  rot: -55, size: 1.8, op: 0.06 },
  { glyph: '❧',  x: 7,  y: 35, rot: 10,  size: 3.0, op: 0.09 },
  { glyph: '🌿', x: 0,  y: 50, rot: -20, size: 5.0, op: 0.07 },
  { glyph: '🍃', x: 5,  y: 62, rot: 60,  size: 2.5, op: 0.06 },
  { glyph: '❦',  x: 2,  y: 75, rot: -8,  size: 2.8, op: 0.08 },
  { glyph: '🌿', x: 8,  y: 85, rot: 35,  size: 3.5, op: 0.07 },
  { glyph: '🍃', x: 1,  y: 93, rot: -40, size: 2.0, op: 0.06 },
  { glyph: '🌿', x: 88, y: 2,  rot: 20,  size: 4.2, op: 0.09 },
  { glyph: '🍃', x: 94, y: 10, rot: -15, size: 2.4, op: 0.07 },
  { glyph: '❧',  x: 91, y: 20, rot: 50,  size: 2.6, op: 0.08 },
  { glyph: '🌿', x: 97, y: 32, rot: -35, size: 3.8, op: 0.07 },
  { glyph: '🍃', x: 85, y: 43, rot: 25,  size: 2.0, op: 0.06 },
  { glyph: '🌿', x: 93, y: 55, rot: -60, size: 4.8, op: 0.08 },
  { glyph: '❦',  x: 88, y: 67, rot: 12,  size: 3.2, op: 0.07 },
  { glyph: '🍃', x: 96, y: 78, rot: -22, size: 2.2, op: 0.06 },
  { glyph: '🌿', x: 90, y: 90, rot: 45,  size: 3.6, op: 0.08 },
  { glyph: '🍄', x: 20, y: 15, rot: 8,   size: 2.2, op: 0.07 },
  { glyph: '🌱', x: 35, y: 8,  rot: -12, size: 1.8, op: 0.06 },
  { glyph: '🍁', x: 48, y: 5,  rot: 33,  size: 2.5, op: 0.07 },
  { glyph: '🌾', x: 62, y: 12, rot: -20, size: 3.2, op: 0.06 },
  { glyph: '🍄', x: 75, y: 7,  rot: 15,  size: 1.9, op: 0.07 },
  { glyph: '🌰', x: 28, y: 72, rot: -5,  size: 2.0, op: 0.06 },
  { glyph: '🍂', x: 42, y: 80, rot: 28,  size: 2.4, op: 0.07 },
  { glyph: '🌱', x: 56, y: 76, rot: -18, size: 1.6, op: 0.05 },
  { glyph: '🍄', x: 68, y: 83, rot: 40,  size: 2.1, op: 0.07 },
  { glyph: '🌰', x: 80, y: 72, rot: -10, size: 2.3, op: 0.06 },
  { glyph: '☽',  x: 30, y: 38, rot: -5,  size: 2.8, op: 0.06 },
  { glyph: '✦',  x: 50, y: 30, rot: 0,   size: 1.5, op: 0.07 },
  { glyph: '⋆',  x: 44, y: 55, rot: 20,  size: 1.2, op: 0.06 },
  { glyph: '✦',  x: 65, y: 40, rot: 0,   size: 1.8, op: 0.05 },
  { glyph: '🌙', x: 72, y: 25, rot: 8,   size: 2.2, op: 0.07 },
  { glyph: '⋆',  x: 22, y: 55, rot: -10, size: 1.4, op: 0.06 },
  { glyph: '🌲', x: 15, y: 88, rot: 3,   size: 4.5, op: 0.06 },
  { glyph: '🪨', x: 38, y: 92, rot: -8,  size: 2.8, op: 0.05 },
  { glyph: '🌾', x: 55, y: 90, rot: 12,  size: 3.4, op: 0.06 },
  { glyph: '🌲', x: 73, y: 87, rot: -4,  size: 4.0, op: 0.06 },
  { glyph: '🪨', x: 82, y: 94, rot: 5,   size: 2.2, op: 0.05 },
]

const langs: Lang[] = ['en', 'fi', 'de', 'futhark']

export default function App() {
  const [lang, setLang] = useState<Lang>('en')
  const t = translations[lang]
  const svcs = services(t)

  return (
    <div style={{ background: '#1e2318', minHeight: '100vh' }}>
      <CornerFrames />

      {/* Language switcher — fixed top-right */}
      <div style={{
        position: 'fixed',
        top: '1rem',
        right: '1rem',
        zIndex: 100,
        display: 'flex',
        gap: '0.25rem',
        background: 'rgba(20,24,16,0.75)',
        backdropFilter: 'blur(6px)',
        border: '1px solid #2a3d2b',
        padding: '0.3rem 0.4rem',
        borderRadius: '2px',
      }}>
        {langs.map(l => (
          <button
            key={l}
            onClick={() => setLang(l)}
            style={{
              background: lang === l ? '#3d5a3e' : 'transparent',
              color: lang === l ? '#e8e0d0' : '#5c7a50',
              border: 'none',
              cursor: 'pointer',
              fontFamily: "'Crimson Text', Georgia, serif",
              fontSize: '0.8rem',
              letterSpacing: '0.08em',
              padding: '0.2rem 0.5rem',
              transition: 'all 0.15s',
              borderRadius: '1px',
            }}
            onMouseEnter={e => { if (lang !== l) (e.target as HTMLElement).style.color = '#a0c090' }}
            onMouseLeave={e => { if (lang !== l) (e.target as HTMLElement).style.color = '#5c7a50' }}
          >
            {langLabels[l]}
          </button>
        ))}
      </div>

      {/* Hero */}
      <section
        style={{
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          textAlign: 'center',
          padding: '4rem 1.5rem',
          background: 'radial-gradient(ellipse at 30% 70%, #3a1e38 0%, #271428 30%, #1e2318 60%), radial-gradient(ellipse at 70% 30%, #253022 0%, #1e2318 60%)',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {/* organic scatter */}
        <div aria-hidden style={{ position: 'absolute', inset: 0, pointerEvents: 'none', userSelect: 'none' }}>
          {scatter.map((s, i) => (
            <span key={i} style={{
              position: 'absolute',
              left: `${s.x}%`,
              top: `${s.y}%`,
              fontSize: `${s.size}rem`,
              opacity: s.op,
              transform: `rotate(${s.rot}deg)`,
              display: 'block',
              lineHeight: 1,
            }}>
              {s.glyph}
            </span>
          ))}
        </div>

        <p style={{ position: 'relative', color: '#7a9e6a', letterSpacing: '0.25em', fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '1rem' }}>
          {t.tagline}
        </p>
        <h1 style={{
          position: 'relative',
          fontFamily: lang === 'futhark' ? 'serif' : "'Pinyon Script', cursive",
          fontWeight: 400,
          fontSize: lang === 'futhark' ? 'clamp(2.5rem, 7vw, 5rem)' : 'clamp(4.5rem, 13vw, 9rem)',
          lineHeight: 1.2,
          margin: '0 0 1.5rem',
          color: '#e8e0d0',
          textShadow: '0 2px 40px rgba(160, 80, 150, 0.35)',
          letterSpacing: lang === 'futhark' ? '0.15em' : 'normal',
        }}>
          Matami<br />Möttönen
        </h1>
        <p style={{ position: 'relative', maxWidth: '28rem', fontSize: '1.2rem', color: '#b8b090', fontStyle: 'italic', marginBottom: '2.5rem' }}>
          {t.heroSub}
        </p>
        <a
          href="#services"
          style={{
            position: 'relative',
            display: 'inline-block',
            border: '1px solid #3d5a3e',
            color: '#7a9e6a',
            padding: '0.65rem 2rem',
            letterSpacing: '0.12em',
            fontSize: '0.9rem',
            textDecoration: 'none',
            textTransform: lang === 'futhark' ? 'none' : 'uppercase',
            transition: 'all 0.2s',
          }}
          onMouseEnter={e => {
            (e.target as HTMLElement).style.background = '#3d5a3e'
            ;(e.target as HTMLElement).style.color = '#e8e0d0'
          }}
          onMouseLeave={e => {
            (e.target as HTMLElement).style.background = 'transparent'
            ;(e.target as HTMLElement).style.color = '#7a9e6a'
          }}
        >
          {t.enterBtn}
        </a>
      </section>

      {/* About */}
      <section id="about" style={{ maxWidth: '640px', margin: '0 auto', padding: '6rem 1.5rem', textAlign: 'center' }}>
        <p style={{ fontSize: '0.8rem', letterSpacing: '0.3em', textTransform: 'uppercase', color: '#5c7a50', marginBottom: '1.5rem' }}>
          {t.aboutLabel}
        </p>
        <h2 style={{ fontSize: 'clamp(2rem, 5vw, 3rem)', marginBottom: '1.5rem', color: '#c8c0a8' }}>
          {t.aboutHeading}
        </h2>
        <p style={{ color: '#a09880', fontSize: '1.15rem' }}>
          {t.aboutBody}
        </p>
        <div style={{ marginTop: '2.5rem', color: '#3d5a3e', fontSize: '1.5rem', letterSpacing: '0.5rem' }}>
          ⋆ ꩜ ⋆ ꩜ ⋆
        </div>
      </section>

      {/* Services */}
      <section id="services" style={{ padding: '5rem 1.5rem', background: '#181d14' }}>
        <div style={{ maxWidth: '900px', margin: '0 auto' }}>
          <p style={{ textAlign: 'center', fontSize: '0.8rem', letterSpacing: '0.3em', textTransform: 'uppercase', color: '#5c7a50', marginBottom: '0.75rem' }}>
            {t.offeringsLabel}
          </p>
          <h2 style={{ textAlign: 'center', fontSize: 'clamp(2rem, 5vw, 3rem)', marginBottom: '3rem', color: '#c8c0a8' }}>
            {t.offeringsHeading}
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.5rem' }}>
            {svcs.map(s => (
              <div key={s.title} style={{ border: '1px solid #2a3d2b', padding: '2rem 1.5rem', background: '#1e2318', position: 'relative' }}>
                <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>{s.icon}</div>
                <h3 style={{ fontSize: '1.6rem', marginBottom: '0.75rem', color: '#d8d0b8' }}>{s.title}</h3>
                <p style={{ color: '#8a8070', margin: 0, fontSize: '1rem' }}>{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Contact */}
      <section id="contact" style={{ padding: '6rem 1.5rem', textAlign: 'center', background: 'radial-gradient(ellipse at 50% 100%, #3a1e38 0%, #271428 40%, #1e2318 70%)' }}>
        <p style={{ fontSize: '0.8rem', letterSpacing: '0.3em', textTransform: 'uppercase', color: '#5c7a50', marginBottom: '0.75rem' }}>
          {t.contactLabel}
        </p>
        <h2 style={{ fontSize: 'clamp(2rem, 5vw, 3rem)', marginBottom: '1rem', color: '#c8c0a8' }}>
          {t.contactHeading}
        </h2>
        <p style={{ color: '#8a8070', maxWidth: '30rem', margin: '0 auto 2.5rem', fontSize: '1.1rem' }}>
          {t.contactBody}
        </p>
        <a
          href="mailto:matami@example.com"
          style={{ display: 'inline-block', background: '#3d5a3e', color: '#e8e0d0', padding: '0.75rem 2.5rem', textDecoration: 'none', fontSize: '1rem', letterSpacing: '0.08em', transition: 'background 0.2s' }}
          onMouseEnter={e => ((e.target as HTMLElement).style.background = '#2a3d2b')}
          onMouseLeave={e => ((e.target as HTMLElement).style.background = '#3d5a3e')}
        >
          matami@example.com
        </a>
      </section>

      {/* Footer */}
      <footer style={{ borderTop: '1px solid #1e2a1e', padding: '2rem 1.5rem', textAlign: 'center', color: '#3d5040', fontSize: '0.85rem', letterSpacing: '0.05em' }}>
        © {new Date().getFullYear()} Matami Möttönen &nbsp;·&nbsp; {t.footer}
      </footer>

    </div>
  )
}
