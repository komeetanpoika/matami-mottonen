import { Lang, langLabels } from '../translations'
import { useLang } from '../lang'

const langs: Lang[] = ['en', 'fi', 'de', 'futhark']

export default function LangSwitcher() {
  const { lang, setLang } = useLang()

  return (
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
  )
}
