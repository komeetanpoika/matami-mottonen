import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, type AdminEventOut, type AdminRegistrationOut } from '../../api/client'
import { useLang } from '../../lang'
import { formatEventDate, formatPrice, pickLocalized } from '../../localized'
import { button, colors } from '../../theme'

export default function AdminAttendeesPage() {
  const id = Number(useParams().id)
  const { lang, t } = useLang()
  const [event, setEvent] = useState<AdminEventOut | null>(null)
  const [rows, setRows] = useState<AdminRegistrationOut[]>([])
  useEffect(() => { api.admin.getEvent(id).then(setEvent); api.admin.registrations(id).then(setRows) }, [id])
  if (!event) return null
  return (
    <>
      <Link to="/admin" style={{ color: colors.mossDim }}>← {t.adminEvents}</Link>
      <h2 style={{ color: colors.textSoft }}>{pickLocalized(event, lang).title}</h2>
      <p style={{ color: colors.textMuted }}>{formatEventDate(event.starts_at, lang)} · {t.adminConfirmed}: {event.confirmed_count} / {event.capacity}</p>
      <a href={api.admin.registrationsCsvUrl(id)} style={{ ...button, textDecoration: 'none', display: 'inline-block' }}>{t.adminDownloadCsv}</a>
      <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '1.5rem', fontSize: '0.95rem' }}>
        <thead><tr style={{ color: colors.mossDim, textAlign: 'left' }}>
          <th>{t.nameLabel}</th><th>{t.emailLabel}</th><th>{t.quantityLabel}</th><th>{t.adminStatus}</th><th>{t.adminAmount}</th><th>{t.adminCreated}</th>
        </tr></thead>
        <tbody>{rows.map(r => (
          <tr key={r.id} style={{ borderTop: `1px solid ${colors.border}`, color: r.status === 'confirmed' ? colors.text : colors.textMuted }}>
            <td style={{ padding: '0.5rem 0' }}>{r.name}</td><td>{r.email}</td><td>{r.quantity}</td><td>{r.status}</td>
            <td>{formatPrice(r.amount_cents, lang)}</td><td>{formatEventDate(r.created_at, lang)}</td>
          </tr>
        ))}</tbody>
      </table>
    </>
  )
}
