import { describe, expect, it } from 'vitest'
import { formatEventDate, formatPrice, pickLocalized } from './localized'

const both = { title_fi: 'Äänimaljailta', title_en: 'Sound Bowl Evening', description_fi: 'Tuo huopa.', description_en: 'Bring a blanket.' }
const enOnly = { ...both, title_fi: null, description_fi: null }
const fiOnly = { ...both, title_en: null, description_en: null }

describe('pickLocalized', () => {
  it('fi prefers Finnish, falls back to English', () => {
    expect(pickLocalized(both, 'fi').title).toBe('Äänimaljailta')
    expect(pickLocalized(enOnly, 'fi').title).toBe('Sound Bowl Evening')
  })
  it('en and de prefer English, fall back to Finnish', () => {
    expect(pickLocalized(both, 'de').title).toBe('Sound Bowl Evening')
    expect(pickLocalized(fiOnly, 'en').description).toBe('Tuo huopa.')
  })
  it('futhark transliterates the English text', () => {
    expect(pickLocalized(both, 'futhark').title).toBe('ᛊᛟᚢᚾᛞ ᛒᛟᚹᛚ ᛖᚹᛖᚾᛁᚾᚷ')
  })
  it('empty description becomes empty string', () => {
    expect(pickLocalized({ ...enOnly, description_en: null }, 'en').description).toBe('')
  })
})

describe('formatting', () => {
  it('shows Helsinki local time', () => {
    expect(formatEventDate('2026-10-10T15:00:00Z', 'fi')).toContain('10.10.2026')
    expect(formatEventDate('2026-10-10T15:00:00Z', 'fi')).toMatch(/18[.:]00/) // fi-FI prints 18.00
    expect(formatEventDate('2026-10-10T15:00:00Z', 'en')).toContain('18:00')
  })
  it('formats euros and free', () => {
    expect(formatPrice(2500, 'en')).toBe('25 €')
    expect(formatPrice(2550, 'en')).toBe('25.50 €')
    expect(formatPrice(2550, 'fi')).toBe('25,50 €')
    expect(formatPrice(0, 'en')).toBe('Free')
    expect(formatPrice(0, 'fi')).toBe('Ilmainen')
  })
})
