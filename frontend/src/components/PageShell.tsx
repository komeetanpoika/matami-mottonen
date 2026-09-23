import { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import CornerFrames from '../CornerFrames'
import { useLang } from '../lang'
import { colors } from '../theme'
import LangSwitcher from './LangSwitcher'

export default function PageShell({ children }: { children: ReactNode }) {
  const { t } = useLang()
  return (
    <div style={{ background: colors.bg, minHeight: '100vh' }}>
      <CornerFrames />
      <LangSwitcher />
      <Link to="/" style={{ position: 'fixed', top: '1.3rem', left: '1.5rem', zIndex: 100, color: colors.mossDim, textDecoration: 'none', letterSpacing: '0.12em', fontSize: '0.85rem' }}>
        {t.navHome}
      </Link>
      <main style={{ maxWidth: '820px', margin: '0 auto', padding: '6rem 1.5rem 5rem' }}>{children}</main>
    </div>
  )
}
