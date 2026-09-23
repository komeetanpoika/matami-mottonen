import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type AdminEventOut } from '../../api/client'
import { useLang } from '../../lang'
import { formatEventDate, formatPrice, pickLocalized } from '../../localized'
import { buttonPrimary, colors } from '../../theme'

function Table({ rows }: { rows: AdminEventOut[] }) {
  const { lang, t } = useLang()
  return (
    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.95rem' }}>
      <thead><tr style={{ color: colors.mossDim, textAlign: 'left' }}>
        <th>{t.adminStartsAt}</th><th>{t.eventsHeading}</th><th>{t.adminPriceEur}</th><th>{t.adminConfirmed}</th><th></th><th></th>
      </tr></thead>
      <tbody>{rows.map(e => (
        <tr key={e.id} style={{ borderTop: `1px solid ${colors.border}` }}>
          <td style={{ padding: '0.6rem 0' }}>{formatEventDate(e.starts_at, lang)}</td>
          <td>{pickLocalized(e, lang).title}</td>
          <td>{formatPrice(e.price_cents, lang)}</td>
          <td>{e.confirmed_count} / {e.capacity}{e.pending_count > 0 && <span style={{ color: colors.textMuted }}> (+{e.pending_count})</span>}</td>
          <td style={{ color: e.is_published ? colors.mossLight : colors.textMuted }}>{e.is_published ? t.adminPublished : t.adminDraft}</td>
          <td style={{ textAlign: 'right' }}>
            <Link to={`/admin/events/${e.id}`} style={{ color: colors.mossLight, marginRight: '1rem' }}>{t.adminEdit}</Link>
            <Link to={`/admin/events/${e.id}/attendees`} style={{ color: colors.mossLight }}>{t.adminAttendees}</Link>
          </td>
        </tr>
      ))}</tbody>
    </table>
  )
}

export default function AdminEventsPage() {
  const { t } = useLang()
  const [events, setEvents] = useState<AdminEventOut[]>([])
  useEffect(() => { api.admin.listEvents().then(setEvents) }, [])
  const now = Date.now()
  const upcoming = events.filter(e => new Date(e.starts_at).getTime() >= now).sort((a, b) => a.starts_at.localeCompare(b.starts_at))
  const past = events.filter(e => new Date(e.starts_at).getTime() < now)
  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ color: colors.textSoft }}>{t.adminEvents}</h2>
        <Link to="/admin/events/new" style={{ ...buttonPrimary, textDecoration: 'none' }}>{t.adminNewEvent}</Link>
      </div>
      <h3 style={{ color: colors.mossDim }}>{t.adminUpcoming}</h3>
      <Table rows={upcoming} />
      <h3 style={{ color: colors.mossDim, marginTop: '2.5rem' }}>{t.adminPast}</h3>
      <Table rows={past} />
    </>
  )
}
