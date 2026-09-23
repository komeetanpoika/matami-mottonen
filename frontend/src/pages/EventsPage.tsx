import { useEffect, useState } from 'react'
import { api, type EventOut } from '../api/client'
import EventCard from '../components/EventCard'
import PageShell from '../components/PageShell'
import { useLang } from '../lang'
import { colors, heading, label } from '../theme'

function monthKey(iso: string, locale: string): string {
  return new Intl.DateTimeFormat(locale, { timeZone: 'Europe/Helsinki', month: 'long', year: 'numeric' }).format(new Date(iso))
}

export default function EventsPage() {
  const { lang, t } = useLang()
  const [events, setEvents] = useState<EventOut[] | null>(null)
  useEffect(() => { api.getEvents().then(setEvents).catch(() => setEvents([])) }, [])
  const locale = { en: 'en-GB', fi: 'fi-FI', de: 'de-DE', futhark: 'en-GB' }[lang]
  const groups = new Map<string, EventOut[]>()
  for (const e of events ?? []) {
    const k = monthKey(e.starts_at, locale)
    groups.set(k, [...(groups.get(k) ?? []), e])
  }
  return (
    <PageShell>
      <p style={{ ...label, textAlign: 'center' }}>{t.upcomingLabel}</p>
      <h2 style={{ ...heading, textAlign: 'center' }}>{t.eventsHeading}</h2>
      {events && events.length === 0 && <p style={{ textAlign: 'center', color: colors.textMuted, fontStyle: 'italic' }}>{t.eventsEmpty}</p>}
      {[...groups].map(([month, list]) => (
        <section key={month} style={{ marginBottom: '2.5rem' }}>
          <h3 style={{ color: colors.mossDim, fontSize: '1rem', letterSpacing: '0.2em', textTransform: 'uppercase', fontStyle: 'normal' }}>{month}</h3>
          <div style={{ display: 'grid', gap: '1rem' }}>{list.map(e => <EventCard key={e.id} event={e} />)}</div>
        </section>
      ))}
    </PageShell>
  )
}
