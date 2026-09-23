import { useEffect, useState } from 'react'
import { Link, Outlet, useNavigate } from 'react-router-dom'
import { api } from '../../api/client'
import LangSwitcher from '../../components/LangSwitcher'
import { useLang } from '../../lang'
import { button, colors } from '../../theme'

export default function AdminLayout() {
  const { t } = useLang()
  const nav = useNavigate()
  const [ready, setReady] = useState(false)
  useEffect(() => { api.me().then(() => setReady(true)).catch(() => nav('/admin/login', { replace: true })) }, [nav])
  if (!ready) return null
  return (
    <div style={{ background: colors.bgDeep, minHeight: '100vh', color: colors.text }}>
      <LangSwitcher />
      <header style={{ display: 'flex', gap: '1.5rem', alignItems: 'center', padding: '1rem 1.5rem', borderBottom: `1px solid ${colors.border}` }}>
        <strong style={{ letterSpacing: '0.15em' }}>{t.adminTitle}</strong>
        <Link to="/admin" style={{ color: colors.mossLight }}>{t.adminEvents}</Link>
        <Link to="/" style={{ color: colors.mossDim }}>{t.navHome}</Link>
        <button style={{ ...button, marginLeft: 'auto', marginRight: '9rem' }} onClick={() => api.logout().then(() => nav('/admin/login'))}>{t.adminLogout}</button>
      </header>
      <main style={{ maxWidth: '960px', margin: '0 auto', padding: '2rem 1.5rem' }}><Outlet /></main>
    </div>
  )
}
