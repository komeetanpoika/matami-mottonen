export type Lang = 'en' | 'fi' | 'de' | 'futhark'

export interface Strings {
  tagline: string
  heroSub: string
  enterBtn: string
  aboutLabel: string
  aboutHeading: string
  aboutBody: string
  offeringsLabel: string
  offeringsHeading: string
  service1Title: string
  service1Desc: string
  service2Title: string
  service2Desc: string
  service3Title: string
  service3Desc: string
  contactLabel: string
  contactHeading: string
  contactBody: string
  footer: string
}

const en: Strings = {
  tagline: 'sound · tarot · art',
  heroSub: 'Witch. Healer. Chaos agent with good intentions and a small collection of singing bowls.',
  enterBtn: 'Enter ↓',
  aboutLabel: '✦ about ✦',
  aboutHeading: 'She lives in the moss',
  aboutBody: 'Matami works with sound, intuition, and whatever the cards decide to say that day. Sessions are held in-person, outdoors when possible, and always with the understanding that healing is messy and non-linear. No spiritual bypassing. No false promises. Just vibration, presence, and the occasional unsolicited truth.',
  offeringsLabel: '✦ offerings ✦',
  offeringsHeading: 'What she does',
  service1Title: 'Sound Bowl Healing',
  service1Desc: 'One-on-one sessions and group ceremonies. The bowls do whatever they want. So do you.',
  service2Title: 'Tarot Readings',
  service2Desc: 'Cards pulled from a deck that has been dropped on the floor many times. They still work.',
  service3Title: 'Art for Sale',
  service3Desc: 'Paintings, prints, and things made at strange hours. Comes with no explanation unless requested.',
  contactLabel: '✦ contact ✦',
  contactHeading: 'Get in touch',
  contactBody: 'For bookings, questions, or to enquire about art — reach out below. Response times are feral but genuine.',
  footer: 'All rites reserved',
}

const fi: Strings = {
  tagline: 'ääni · tarot · taide',
  heroSub: 'Noita. Parantaja. Kaaoksen asiamies hyvällä sydämellä ja pienellä kokoelmalla laulusuppiloita.',
  enterBtn: 'Sisään ↓',
  aboutLabel: '✦ tietoa ✦',
  aboutHeading: 'Hän asuu sammalessa',
  aboutBody: 'Matami työskentelee äänen, intuition ja sen kanssa mitä kortit sinä päivänä päättävät sanoa. Istunnot pidetään kasvotusten, ulkona aina kun mahdollista, ja aina ymmärryksellä että paraneminen on sotkuista eikä etene suoraan. Ei henkistä oikomista. Ei tyhjiä lupauksia. Vain värinää, läsnäoloa ja satunnainen pyytämätön totuus.',
  offeringsLabel: '✦ palvelut ✦',
  offeringsHeading: 'Mitä hän tekee',
  service1Title: 'Äänimaljaparannus',
  service1Desc: 'Henkilökohtaisia istuntoja ja ryhmäseremonioja. Maljat tekevät mitä haluavat. Sinäkin.',
  service2Title: 'Tarotlukemiset',
  service2Desc: 'Kortit nostetaan pakasta joka on pudonnut lattialle monta kertaa. Ne toimivat silti.',
  service3Title: 'Taidetta myytävänä',
  service3Desc: 'Maalauksia, tulosteita ja asioita jotka on tehty oudoilla tunneilla. Ei selityksiä ellei pyydetä.',
  contactLabel: '✦ yhteys ✦',
  contactHeading: 'Ota yhteyttä',
  contactBody: 'Varauksiin, kysymyksiin tai taidekysymyksiin — ota yhteyttä alla. Vastausajat ovat villitä mutta aitoja.',
  footer: 'Kaikki oikeudet pidätetään',
}

const de: Strings = {
  tagline: 'klang · tarot · kunst',
  heroSub: 'Hexe. Heilerin. Chaosagentin mit guten Absichten und einer kleinen Sammlung Klangschalen.',
  enterBtn: 'Eintreten ↓',
  aboutLabel: '✦ über ✦',
  aboutHeading: 'Sie lebt im Moos',
  aboutBody: 'Matami arbeitet mit Klang, Intuition und dem, was die Karten an jedem Tag zu sagen beschließen. Sitzungen finden persönlich statt, wenn möglich draußen, immer mit dem Verständnis, dass Heilung unordentlich und nichtlinear ist. Kein spirituelles Umgehen. Keine falschen Versprechen. Nur Schwingung, Präsenz und die gelegentliche ungebetene Wahrheit.',
  offeringsLabel: '✦ angebote ✦',
  offeringsHeading: 'Was sie tut',
  service1Title: 'Klangschalen-Heilung',
  service1Desc: 'Einzelsitzungen und Gruppenzeremonien. Die Schalen tun, was sie wollen. Du auch.',
  service2Title: 'Tarotlesungen',
  service2Desc: 'Karten aus einem Stapel gezogen, der schon viele Male auf den Boden gefallen ist. Sie funktionieren trotzdem.',
  service3Title: 'Kunst zu verkaufen',
  service3Desc: 'Gemälde, Drucke und Dinge, die zu seltsamen Stunden entstanden. Ohne Erklärung, es sei denn, sie wird erbeten.',
  contactLabel: '✦ kontakt ✦',
  contactHeading: 'Kontakt aufnehmen',
  contactBody: 'Für Buchungen, Fragen oder Kunstanfragen — schreib unten. Antwortzeiten sind wild aber aufrichtig.',
  footer: 'Alle Riten vorbehalten',
}

// Elder Futhark transliteration
const runeMap: Record<string, string> = {
  a: 'ᚨ', b: 'ᛒ', c: 'ᚲ', d: 'ᛞ', e: 'ᛖ', f: 'ᚠ', g: 'ᚷ', h: 'ᚺ',
  i: 'ᛁ', j: 'ᛃ', k: 'ᚲ', l: 'ᛚ', m: 'ᛗ', n: 'ᚾ', o: 'ᛟ', p: 'ᛈ',
  q: 'ᚲ', r: 'ᚱ', s: 'ᛊ', t: 'ᛏ', u: 'ᚢ', v: 'ᚹ', w: 'ᚹ', x: 'ᚲᛊ',
  y: 'ᛃ', z: 'ᛉ', ä: 'ᚨ', ö: 'ᛟ', ü: 'ᚢ', å: 'ᚨ', ß: 'ᛊᛊ',
}

function toRunes(text: string): string {
  return text.toLowerCase().split('').map(ch => runeMap[ch] ?? ch).join('')
}

function runeStrings(base: Strings): Strings {
  return Object.fromEntries(
    Object.entries(base).map(([k, v]) => [k, toRunes(v)])
  ) as unknown as Strings
}

export const translations: Record<Lang, Strings> = {
  en,
  fi,
  de,
  futhark: runeStrings(en),
}

export const langLabels: Record<Lang, string> = {
  en: 'EN',
  fi: 'FI',
  de: 'DE',
  futhark: 'ᚠᚢᚦ',
}
