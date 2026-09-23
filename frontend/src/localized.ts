import { Lang, toRunes, translations } from './translations'

export interface Localizable {
  title_fi: string | null
  title_en: string | null
  description_fi: string | null
  description_en: string | null
}

export function pickLocalized(item: Localizable, lang: Lang): { title: string; description: string } {
  const fiFirst = lang === 'fi'
  const title = (fiFirst ? item.title_fi ?? item.title_en : item.title_en ?? item.title_fi) ?? ''
  const description =
    (fiFirst ? item.description_fi ?? item.description_en : item.description_en ?? item.description_fi) ?? ''
  if (lang === 'futhark') return { title: toRunes(title), description: toRunes(description) }
  return { title, description }
}

const LOCALE: Record<Lang, string> = { en: 'en-GB', fi: 'fi-FI', de: 'de-DE', futhark: 'en-GB' }

export function formatEventDate(iso: string, lang: Lang): string {
  return new Intl.DateTimeFormat(LOCALE[lang], {
    timeZone: 'Europe/Helsinki',
    weekday: 'short', day: 'numeric', month: lang === 'en' || lang === 'futhark' ? 'short' : 'numeric',
    year: 'numeric', hour: '2-digit', minute: '2-digit',
  }).format(new Date(iso))
}

export function formatPrice(cents: number, lang: Lang): string {
  if (cents === 0) return translations[lang].free
  const whole = cents % 100 === 0
  const n = new Intl.NumberFormat(LOCALE[lang], {
    minimumFractionDigits: whole ? 0 : 2, maximumFractionDigits: 2,
  }).format(cents / 100)
  return `${n} €`
}
