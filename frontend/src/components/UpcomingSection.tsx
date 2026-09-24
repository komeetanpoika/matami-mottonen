import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type EventOut } from '../api/client'
import { useLang } from '../lang'
import { buttonPrimary, colors, heading, label } from '../theme'
import EventCard from './EventCard'

export default function UpcomingSection() {
  const { t } = useLang()
  const [events, setEvents] = useState<EventOut[] | null>(null)
  useEffect(() => { api.getEvents().then(list => setEvents(list.slice(0, 3))).catch(() => setEvents([])) }, [])
  return (
    <section id="events" style={{ padding: '5rem 1.5rem', background: colors.bg }}>
      <div style={{ maxWidth: '820px', margin: '0 auto' }}>
        <p style={{ ...label, textAlign: 'center' }}>{t.upcomingLabel}</p>
        <h2 style={{ ...heading, textAlign: 'center' }}>{t.upcomingHeading}</h2>
        {events && events.length === 0 && (
          <p style={{ textAlign: 'center', color: colors.textMuted, fontStyle: 'italic' }}>{t.eventsEmpty}</p>
        )}
        <div style={{ display: 'grid', gap: '1rem' }}>{(events ?? []).map(e => <EventCard key={e.id} event={e} />)}</div>
        <p style={{ textAlign: 'center', marginTop: '2.5rem' }}>
          <Link to="/events" style={{ ...buttonPrimary, display: 'inline-block', textDecoration: 'none', padding: '0.85rem 2.5rem' }}>{t.seeAllEvents}</Link>
        </p>
      </div>
    </section>
  )
}
