const TZ = 'Europe/Helsinki'

export function isoToLocalInput(iso: string | null): string {
  if (!iso) return ''
  const parts = new Intl.DateTimeFormat('en-GB', {
    timeZone: TZ, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false,
  }).formatToParts(new Date(iso))
  const g = (type: string) => parts.find(p => p.type === type)?.value ?? '00'
  return `${g('year')}-${g('month')}-${g('day')}T${g('hour') === '24' ? '00' : g('hour')}:${g('minute')}`
}

/** Convert a Helsinki wall-clock `YYYY-MM-DDTHH:mm` to UTC ISO by iterating the offset. */
export function localInputToIso(v: string): string | null {
  if (!v) return null
  const [d, tm] = v.split('T')
  const [y, m, day] = d.split('-').map(Number)
  const [h, min] = tm.split(':').map(Number)
  let guess = Date.UTC(y, m - 1, day, h, min)
  for (let i = 0; i < 2; i++) {
    const back = isoToLocalInput(new Date(guess).toISOString())
    if (back === v) break
    const [bd, bt] = back.split('T')
    const [by, bm, bday] = bd.split('-').map(Number)
    const [bh, bmin] = bt.split(':').map(Number)
    const diff = Date.UTC(by, bm - 1, bday, bh, bmin) - guess
    guess -= diff
  }
  return new Date(guess).toISOString()
}
