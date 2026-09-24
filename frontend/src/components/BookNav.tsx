import { Link } from 'react-router-dom'
import { useLang } from '../lang'
import { colors } from '../theme'

/** The site's one primary action, pinned top-left on every page. */
export default function BookNav({ left = '1rem' }: { left?: string }) {
  const { t } = useLang()
  return (
    <Link
      to="/events"
      style={{
        position: 'fixed',
        top: '1rem',
        left,
        zIndex: 100,
        background: colors.moss,
        color: colors.text,
        fontFamily: "'Crimson Text', Georgia, serif",
        fontSize: '0.85rem',
        letterSpacing: '0.1em',
        padding: '0.5rem 1rem',
        borderRadius: '2px',
        textDecoration: 'none',
        boxShadow: '0 2px 18px rgba(0,0,0,0.35)',
        transition: 'background 0.15s',
      }}
      onMouseEnter={e => ((e.currentTarget as HTMLElement).style.background = '#4d6e4e')}
      onMouseLeave={e => ((e.currentTarget as HTMLElement).style.background = colors.moss)}
    >
      {t.navEvents}
    </Link>
  )
}
