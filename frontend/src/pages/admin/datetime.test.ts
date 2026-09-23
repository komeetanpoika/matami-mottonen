import { expect, it } from 'vitest'
import { isoToLocalInput, localInputToIso } from './datetime'

it('round-trips Helsinki wall time', () => {
  expect(isoToLocalInput('2026-10-10T15:00:00Z')).toBe('2026-10-10T18:00')   // EEST
  expect(isoToLocalInput('2026-12-10T15:00:00Z')).toBe('2026-12-10T17:00')   // EET
  expect(localInputToIso('2026-10-10T18:00')).toBe('2026-10-10T15:00:00.000Z')
  expect(localInputToIso('2026-12-10T17:00')).toBe('2026-12-10T15:00:00.000Z')
  expect(localInputToIso('')).toBeNull()
  expect(isoToLocalInput(null)).toBe('')
})
