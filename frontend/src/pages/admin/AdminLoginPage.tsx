import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../../api/client'
import { useLang } from '../../lang'
import { buttonPrimary, colors, input } from '../../theme'

export default function AdminLoginPage() {
  const { t } = useLang()
  const nav = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [err, setErr] = useState(false)
  async function submit(e: FormEvent) {
    e.preventDefault()
    try { await api.login(email, password); nav('/admin') } catch { setErr(true) }
  }
  return (
    <div style={{ background: colors.bgDeep, minHeight: '100vh', display: 'grid', placeItems: 'center' }}>
      <form onSubmit={submit} style={{ display: 'grid', gap: '1rem', width: 'min(360px, 90vw)' }}>
        <h2 style={{ color: colors.textSoft, margin: 0 }}>{t.adminLogin}</h2>
        <input style={input} type="email" placeholder={t.emailLabel} value={email} onChange={e => setEmail(e.target.value)} required />
        <input style={input} type="password" placeholder={t.adminPassword} value={password} onChange={e => setPassword(e.target.value)} required />
        {err && <p style={{ color: colors.danger, margin: 0 }}>{t.adminBadLogin}</p>}
        <button style={buttonPrimary} type="submit">{t.adminLogin}</button>
      </form>
    </div>
  )
}
