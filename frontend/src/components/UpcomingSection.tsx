import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type EventOut } from '../api/client'
import { useLang } from '../lang'
import { colors, heading, label } from '../theme'
import EventCard from './EventCard'

export default function UpcomingSection() {
  const { t } = useLang()
  const [events, setEvents] = useState<EventOut[]>([])
  useEffect(() => { api.getEvents().then(list => setEvents(list.slice(0, 3))).catch(() => setEvents([])) }, [])
  if (events.length === 0) return null
  return (
    <section id="events" style={{ padding: '5rem 1.5rem', background: colors.bg }}>
      <div style={{ maxWidth: '820px', margin: '0 auto' }}>
        <p style={{ ...label, textAlign: 'center' }}>{t.upcomingLabel}</p>
        <h2 style={{ ...heading, textAlign: 'center' }}>{t.upcomingHeading}</h2>
        <div style={{ display: 'grid', gap: '1rem' }}>{events.map(e => <EventCard key={e.id} event={e} />)}</div>
        <p style={{ textAlign: 'center', marginTop: '2rem' }}>
          <Link to="/events" style={{ color: colors.mossLight, letterSpacing: '0.12em', textDecoration: 'none' }}>{t.seeAllEvents}</Link>
        </p>
      </div>
    </section>
  )
}
