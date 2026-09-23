import { Link } from 'react-router-dom'
import type { EventOut } from '../api/client'
import { useLang } from '../lang'
import { formatEventDate, formatPrice, pickLocalized } from '../localized'
import { card, colors } from '../theme'

export default function EventCard({ event }: { event: EventOut }) {
  const { lang, t } = useLang()
  const { title } = pickLocalized(event, lang)
  const remaining = event.seats_left === 1 ? t.seatLeftOne : t.seatsLeft.replace('{n}', String(event.seats_left))
  const seats = event.sold_out ? t.soldOut : remaining
  return (
    <Link to={`/events/${event.slug}`} style={{ ...card, display: 'block', textDecoration: 'none', opacity: event.sold_out ? 0.6 : 1 }}>
      <div style={{ color: colors.mossLight, fontSize: '0.85rem', letterSpacing: '0.15em' }}>{formatEventDate(event.starts_at, lang)}</div>
      <h3 style={{ margin: '0.4rem 0 0.5rem', fontSize: '1.6rem', color: colors.textSoft }}>{title}</h3>
      <div style={{ display: 'flex', justifyContent: 'space-between', color: colors.textMuted, fontSize: '0.95rem' }}>
        <span>{event.location ?? ''}</span>
        <span>{formatPrice(event.price_cents, lang)} · {seats}</span>
      </div>
    </Link>
  )
}
