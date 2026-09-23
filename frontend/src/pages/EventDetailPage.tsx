import { FormEvent, useEffect, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { api, ApiError, type EventOut } from '../api/client'
import PageShell from '../components/PageShell'
import { useLang } from '../lang'
import { formatEventDate, formatPrice, pickLocalized } from '../localized'
import { buttonPrimary, colors, heading, input, label } from '../theme'

export default function EventDetailPage() {
  const { slug = '' } = useParams()
  const [params, setParams] = useSearchParams()
  const { lang, t } = useLang()
  const [event, setEvent] = useState<EventOut | null | undefined>(undefined)
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [quantity, setQuantity] = useState(1)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [cancelled, setCancelled] = useState(false)

  const load = () => api.getEvent(slug).then(setEvent).catch(() => setEvent(null))
  useEffect(() => { load() }, [slug]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const reg = params.get('cancelled')
    if (!reg) return
    api.cancelRegistration(reg).catch(() => undefined).finally(() => { setCancelled(true); load(); setParams({}, { replace: true }) })
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  if (event === undefined) return <PageShell><p style={{ color: colors.textMuted }}>…</p></PageShell>
  if (event === null) return <PageShell><p style={{ color: colors.textMuted }}>{t.errGeneric}</p><Link to="/events" style={{ color: colors.mossLight }}>{t.backToEvents}</Link></PageShell>

  const { title, description } = pickLocalized(event, lang)
  const max = Math.min(10, event.seats_left)
  const seatsLabel = event.seats_left === 1 ? t.seatLeftOne : t.seatsLeft.replace('{n}', String(event.seats_left))

  async function submit(e: FormEvent) {
    e.preventDefault()
    setBusy(true); setError(null)
    try {
      const r = await api.checkout(event!.slug, { name, email, quantity, lang })
      if (r.checkout_url) window.location.assign(r.checkout_url)
      else window.location.assign(`/events/thanks?reg=${r.registration_id}`)
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) { setError(t.errSoldOut); load() }
      else if (err instanceof ApiError && err.status === 502) setError(t.errPayment)
      else setError(t.errGeneric)
      setBusy(false)
    }
  }

  return (
    <PageShell>
      <Link to="/events" style={{ color: colors.mossDim, textDecoration: 'none', fontSize: '0.9rem' }}>{t.backToEvents}</Link>
      <p style={{ ...label, marginTop: '2rem' }}>{formatEventDate(event.starts_at, lang)}</p>
      <h2 style={heading}>{title}</h2>
      <p style={{ color: colors.textMuted }}>{event.location}</p>
      <p style={{ color: colors.textSoft, whiteSpace: 'pre-line', fontSize: '1.1rem' }}>{description}</p>
      <p style={{ color: colors.mossLight, letterSpacing: '0.1em' }}>
        {formatPrice(event.price_cents, lang)} {event.price_cents > 0 && t.perSeat} · {event.sold_out ? t.soldOut : seatsLabel}
      </p>
      {cancelled && <p style={{ color: colors.textMuted, fontStyle: 'italic' }}>{t.cancelledNote}</p>}
      {!event.sold_out && (
        <form onSubmit={submit} style={{ marginTop: '2.5rem', display: 'grid', gap: '1rem', maxWidth: '420px' }}>
          <h3 style={{ margin: 0, color: colors.textSoft }}>{t.signUpHeading}</h3>
          <label style={{ color: colors.textMuted }}>{t.nameLabel}<input style={input} value={name} onChange={e => setName(e.target.value)} required maxLength={120} /></label>
          <label style={{ color: colors.textMuted }}>{t.emailLabel}<input style={input} type="email" value={email} onChange={e => setEmail(e.target.value)} required /></label>
          <label style={{ color: colors.textMuted }}>{t.quantityLabel}
            <select style={input} value={quantity} onChange={e => setQuantity(Number(e.target.value))}>
              {Array.from({ length: max }, (_, i) => i + 1).map(n => <option key={n} value={n}>{n}</option>)}
            </select>
          </label>
          {error && <p style={{ color: colors.danger, margin: 0 }}>{error}</p>}
          <button type="submit" style={buttonPrimary} disabled={busy}>
            {busy ? t.submitting : event.price_cents > 0 ? t.payButton : t.registerFreeButton}
          </button>
        </form>
      )}
    </PageShell>
  )
}
