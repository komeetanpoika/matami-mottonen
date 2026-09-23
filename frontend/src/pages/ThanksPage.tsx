import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api, type RegistrationStatus } from '../api/client'
import PageShell from '../components/PageShell'
import { useLang } from '../lang'
import { colors, heading } from '../theme'

const POLL_MS = 2000
const MAX_POLLS = 30

export default function ThanksPage() {
  const [params] = useSearchParams()
  const { t } = useLang()
  const reg = params.get('reg')
  const [status, setStatus] = useState<RegistrationStatus | 'unknown' | 'timeout'>('pending')

  useEffect(() => {
    if (!reg) { setStatus('unknown'); return }
    let polls = 0
    let timer: number | undefined
    let cancelled = false
    const tick = async () => {
      try {
        const r = await api.registrationStatus(reg)
        if (cancelled) return
        if (r.status !== 'pending') { setStatus(r.status); return }
      } catch {
        if (cancelled) return
        setStatus('unknown')
        return
      }
      if (cancelled) return
      if (++polls >= MAX_POLLS) { setStatus('timeout'); return }
      timer = window.setTimeout(tick, POLL_MS)
    }
    tick()
    return () => { cancelled = true; window.clearTimeout(timer) }
  }, [reg])

  const text = {
    pending: t.thanksConfirming, confirmed: t.thanksConfirmed, timeout: t.thanksPendingLong,
    expired: t.thanksExpired, cancelled: t.thanksExpired, unknown: t.errGeneric,
  }[status]

  return (
    <PageShell>
      <h2 style={{ ...heading, textAlign: 'center' }}>{status === 'confirmed' ? '✦' : '☽'}</h2>
      <p data-testid="thanks-status" style={{ textAlign: 'center', color: colors.textSoft, fontSize: '1.2rem' }}>{text}</p>
      <p style={{ textAlign: 'center' }}><Link to="/events" style={{ color: colors.mossLight }}>{t.backToEvents}</Link></p>
    </PageShell>
  )
}
