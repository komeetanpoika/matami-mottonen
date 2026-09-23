import { FormEvent, useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api, ApiError, type EventIn } from '../../api/client'
import { useLang } from '../../lang'
import { button, buttonPrimary, colors, input } from '../../theme'
import { isoToLocalInput, localInputToIso } from './datetime'

interface Form {
  title_fi: string; title_en: string; description_fi: string; description_en: string
  starts_at: string; ends_at: string; location: string; price_eur: string; capacity: string; is_published: boolean
}
const empty: Form = { title_fi: '', title_en: '', description_fi: '', description_en: '', starts_at: '', ends_at: '', location: '', price_eur: '0', capacity: '10', is_published: false }

function toBody(f: Form): EventIn {
  return {
    title_fi: f.title_fi.trim() || null, title_en: f.title_en.trim() || null,
    description_fi: f.description_fi.trim() || null, description_en: f.description_en.trim() || null,
    starts_at: localInputToIso(f.starts_at) ?? '', ends_at: localInputToIso(f.ends_at),
    location: f.location.trim() || null,
    price_cents: Math.round(Number(f.price_eur.replace(',', '.')) * 100), capacity: Number(f.capacity), is_published: f.is_published,
  }
}

export default function AdminEventFormPage() {
  const { id } = useParams()
  const eventId = id ? Number(id) : null
  const { t } = useLang()
  const nav = useNavigate()
  const [f, setF] = useState<Form>(empty)
  const [err, setErr] = useState<string | null>(null)
  const [confirmedCount, setConfirmedCount] = useState(0)

  useEffect(() => {
    if (eventId === null) return
    api.admin.getEvent(eventId).then(e => {
      setConfirmedCount(e.confirmed_count)
      setF({
        title_fi: e.title_fi ?? '', title_en: e.title_en ?? '', description_fi: e.description_fi ?? '', description_en: e.description_en ?? '',
        starts_at: isoToLocalInput(e.starts_at), ends_at: isoToLocalInput(e.ends_at), location: e.location ?? '',
        price_eur: (e.price_cents / 100).toString(), capacity: String(e.capacity), is_published: e.is_published,
      })
    })
  }, [eventId])

  const set = <K extends keyof Form>(k: K) => (e: { target: { value: string } }) => setF({ ...f, [k]: e.target.value })

  async function submit(e: FormEvent) {
    e.preventDefault()
    setErr(null)
    const body = toBody(f)
    if (!body.title_fi && !body.title_en) { setErr(t.adminNeedTitle); return }
    try {
      if (eventId === null) await api.admin.createEvent(body)
      else await api.admin.updateEvent(eventId, body)
      nav('/admin')
    } catch (ex) { setErr(ex instanceof ApiError ? JSON.stringify(ex.detail) : t.errGeneric) }
  }

  async function remove() {
    if (eventId === null || !window.confirm(t.adminDelete + '?')) return
    try { await api.admin.deleteEvent(eventId); nav('/admin') }
    catch (ex) { setErr(ex instanceof ApiError && ex.status === 409 ? t.adminDeleteBlocked : t.errGeneric) }
  }

  const field = (labelText: string, el: JSX.Element) => <label style={{ color: colors.textMuted, display: 'grid', gap: '0.3rem' }}>{labelText}{el}</label>

  return (
    <form onSubmit={submit} style={{ display: 'grid', gap: '1rem', maxWidth: '640px' }}>
      <h2 style={{ color: colors.textSoft, margin: 0 }}>{eventId === null ? t.adminNewEvent : t.adminEdit}</h2>
      {field(t.adminTitleFi, <input style={input} value={f.title_fi} onChange={set('title_fi')} maxLength={200} />)}
      {field(t.adminTitleEn, <input style={input} value={f.title_en} onChange={set('title_en')} maxLength={200} />)}
      {field(t.adminDescFi, <textarea style={{ ...input, minHeight: '6rem' }} value={f.description_fi} onChange={set('description_fi')} />)}
      {field(t.adminDescEn, <textarea style={{ ...input, minHeight: '6rem' }} value={f.description_en} onChange={set('description_en')} />)}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
        {field(t.adminStartsAt, <input style={input} type="datetime-local" value={f.starts_at} onChange={set('starts_at')} required />)}
        {field(t.adminEndsAt, <input style={input} type="datetime-local" value={f.ends_at} onChange={set('ends_at')} />)}
      </div>
      {field(t.adminLocation, <input style={input} value={f.location} onChange={set('location')} maxLength={300} />)}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
        {field(t.adminPriceEur, <input style={input} inputMode="decimal" value={f.price_eur} onChange={set('price_eur')} required />)}
        {field(t.adminCapacity, <input style={input} type="number" min={1} value={f.capacity} onChange={set('capacity')} required />)}
      </div>
      <label style={{ color: colors.textMuted }}>
        <input type="checkbox" checked={f.is_published} onChange={e => setF({ ...f, is_published: e.target.checked })} /> {t.adminPublished}
      </label>
      {err && <p style={{ color: colors.danger, margin: 0 }}>{err}</p>}
      <div style={{ display: 'flex', gap: '1rem' }}>
        <button type="submit" style={buttonPrimary}>{t.adminSave}</button>
        {eventId !== null && <button type="button" style={{ ...button, color: colors.danger, borderColor: colors.danger }} onClick={remove} disabled={confirmedCount > 0} title={confirmedCount > 0 ? t.adminDeleteBlocked : ''}>{t.adminDelete}</button>}
      </div>
    </form>
  )
}
