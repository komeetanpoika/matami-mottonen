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
  navEvents: string
  navHome: string
  upcomingLabel: string
  upcomingHeading: string
  seeAllEvents: string
  eventsHeading: string
  eventsEmpty: string
  seatsLeft: string
  soldOut: string
  free: string
  perSeat: string
  signUpHeading: string
  nameLabel: string
  emailLabel: string
  quantityLabel: string
  payButton: string
  registerFreeButton: string
  submitting: string
  errSoldOut: string
  errPayment: string
  errGeneric: string
  cancelledNote: string
  thanksConfirming: string
  thanksConfirmed: string
  thanksPendingLong: string
  thanksExpired: string
  backToEvents: string
  adminTitle: string
  adminLogin: string
  adminLogout: string
  adminPassword: string
  adminBadLogin: string
  adminEvents: string
  adminNewEvent: string
  adminUpcoming: string
  adminPast: string
  adminPublished: string
  adminDraft: string
  adminConfirmed: string
  adminCapacity: string
  adminPriceEur: string
  adminStartsAt: string
  adminEndsAt: string
  adminLocation: string
  adminTitleFi: string
  adminTitleEn: string
  adminDescFi: string
  adminDescEn: string
  adminSave: string
  adminDelete: string
  adminDeleteBlocked: string
  adminAttendees: string
  adminDownloadCsv: string
  adminStatus: string
  adminAmount: string
  adminCreated: string
  adminEdit: string
  adminNeedTitle: string
  adminBadPrice: string
  adminBadCapacity: string
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
  navEvents: 'Events',
  navHome: 'Home',
  upcomingLabel: '✦ upcoming ✦',
  upcomingHeading: 'Gatherings',
  seeAllEvents: 'All events →',
  eventsHeading: 'Events',
  eventsEmpty: 'Nothing on the calendar right now. The moss is resting.',
  seatsLeft: '{n} seats left',
  soldOut: 'Sold out',
  free: 'Free',
  perSeat: 'per seat',
  signUpHeading: 'Sign up',
  nameLabel: 'Name',
  emailLabel: 'Email',
  quantityLabel: 'Seats',
  payButton: 'Continue to payment',
  registerFreeButton: 'Sign up',
  submitting: 'One moment…',
  errSoldOut: 'Those seats just went.',
  errPayment: 'The payment service is unavailable. Please try again in a moment.',
  errGeneric: 'Something went wrong.',
  cancelledNote: 'Payment cancelled. Your seats were released.',
  thanksConfirming: 'Confirming your payment…',
  thanksConfirmed: "You're in. A confirmation is on its way to your email.",
  thanksPendingLong: 'Payment received. Your confirmation email will follow shortly.',
  thanksExpired: 'This sign-up expired before payment completed. Please sign up again.',
  backToEvents: '← Back to events',
  adminTitle: 'Admin',
  adminLogin: 'Log in',
  adminLogout: 'Log out',
  adminPassword: 'Password',
  adminBadLogin: 'Wrong email or password.',
  adminEvents: 'Events',
  adminNewEvent: 'New event',
  adminUpcoming: 'Upcoming',
  adminPast: 'Past',
  adminPublished: 'Published',
  adminDraft: 'Draft',
  adminConfirmed: 'Confirmed',
  adminCapacity: 'Capacity',
  adminPriceEur: 'Price (€)',
  adminStartsAt: 'Starts',
  adminEndsAt: 'Ends (optional)',
  adminLocation: 'Location',
  adminTitleFi: 'Title (FI)',
  adminTitleEn: 'Title (EN)',
  adminDescFi: 'Description (FI)',
  adminDescEn: 'Description (EN)',
  adminSave: 'Save',
  adminDelete: 'Delete',
  adminDeleteBlocked: 'Cannot delete: confirmed sign-ups exist.',
  adminAttendees: 'Attendees',
  adminDownloadCsv: 'Download CSV',
  adminStatus: 'Status',
  adminAmount: 'Paid',
  adminCreated: 'Created',
  adminEdit: 'Edit',
  adminNeedTitle: 'Give the event a title in at least one language.',
  adminBadPrice: 'Enter a price like 25 or 25,50.',
  adminBadCapacity: 'Capacity must be a whole number of at least 1.',
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
  navEvents: 'Tapahtumat',
  navHome: 'Etusivu',
  upcomingLabel: '✦ tulossa ✦',
  upcomingHeading: 'Kokoontumiset',
  seeAllEvents: 'Kaikki tapahtumat →',
  eventsHeading: 'Tapahtumat',
  eventsEmpty: 'Kalenteri on tyhjä juuri nyt. Sammal lepää.',
  seatsLeft: '{n} paikkaa jäljellä',
  soldOut: 'Loppuunmyyty',
  free: 'Ilmainen',
  perSeat: '/ paikka',
  signUpHeading: 'Ilmoittaudu',
  nameLabel: 'Nimi',
  emailLabel: 'Sähköposti',
  quantityLabel: 'Paikkoja',
  payButton: 'Siirry maksamaan',
  registerFreeButton: 'Ilmoittaudu',
  submitting: 'Hetki…',
  errSoldOut: 'Nuo paikat menivät juuri.',
  errPayment: 'Maksupalvelu ei vastaa. Yritä hetken päästä uudelleen.',
  errGeneric: 'Jokin meni pieleen.',
  cancelledNote: 'Maksu peruttu. Paikkasi vapautettiin.',
  thanksConfirming: 'Vahvistetaan maksuasi…',
  thanksConfirmed: 'Olet mukana. Vahvistus on matkalla sähköpostiisi.',
  thanksPendingLong: 'Maksu vastaanotettu. Vahvistusviesti tulee pian.',
  thanksExpired: 'Ilmoittautuminen vanheni ennen maksun valmistumista. Ilmoittaudu uudelleen.',
  backToEvents: '← Takaisin tapahtumiin',
  adminTitle: 'Hallinta',
  adminLogin: 'Kirjaudu',
  adminLogout: 'Kirjaudu ulos',
  adminPassword: 'Salasana',
  adminBadLogin: 'Väärä sähköposti tai salasana.',
  adminEvents: 'Tapahtumat',
  adminNewEvent: 'Uusi tapahtuma',
  adminUpcoming: 'Tulevat',
  adminPast: 'Menneet',
  adminPublished: 'Julkaistu',
  adminDraft: 'Luonnos',
  adminConfirmed: 'Vahvistetut',
  adminCapacity: 'Paikkoja',
  adminPriceEur: 'Hinta (€)',
  adminStartsAt: 'Alkaa',
  adminEndsAt: 'Päättyy (valinnainen)',
  adminLocation: 'Paikka',
  adminTitleFi: 'Otsikko (FI)',
  adminTitleEn: 'Otsikko (EN)',
  adminDescFi: 'Kuvaus (FI)',
  adminDescEn: 'Kuvaus (EN)',
  adminSave: 'Tallenna',
  adminDelete: 'Poista',
  adminDeleteBlocked: 'Ei voi poistaa: vahvistettuja ilmoittautumisia.',
  adminAttendees: 'Osallistujat',
  adminDownloadCsv: 'Lataa CSV',
  adminStatus: 'Tila',
  adminAmount: 'Maksettu',
  adminCreated: 'Luotu',
  adminEdit: 'Muokkaa',
  adminNeedTitle: 'Anna tapahtumalle otsikko ainakin yhdellä kielellä.',
  adminBadPrice: 'Anna hinta muodossa 25 tai 25,50.',
  adminBadCapacity: 'Paikkamäärän on oltava kokonaisluku, vähintään 1.',
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
  navEvents: 'Veranstaltungen',
  navHome: 'Startseite',
  upcomingLabel: '✦ demnächst ✦',
  upcomingHeading: 'Zusammenkünfte',
  seeAllEvents: 'Alle Veranstaltungen →',
  eventsHeading: 'Veranstaltungen',
  eventsEmpty: 'Gerade ist nichts im Kalender. Das Moos ruht.',
  seatsLeft: '{n} Plätze frei',
  soldOut: 'Ausverkauft',
  free: 'Kostenlos',
  perSeat: 'pro Platz',
  signUpHeading: 'Anmelden',
  nameLabel: 'Name',
  emailLabel: 'E-Mail',
  quantityLabel: 'Plätze',
  payButton: 'Zur Zahlung',
  registerFreeButton: 'Anmelden',
  submitting: 'Einen Moment…',
  errSoldOut: 'Diese Plätze sind gerade weg.',
  errPayment: 'Der Zahlungsdienst ist nicht erreichbar. Bitte gleich noch einmal versuchen.',
  errGeneric: 'Etwas ist schiefgelaufen.',
  cancelledNote: 'Zahlung abgebrochen. Deine Plätze wurden freigegeben.',
  thanksConfirming: 'Zahlung wird bestätigt…',
  thanksConfirmed: 'Du bist dabei. Eine Bestätigung ist unterwegs an deine E-Mail.',
  thanksPendingLong: 'Zahlung eingegangen. Die Bestätigung folgt in Kürze.',
  thanksExpired: 'Diese Anmeldung ist vor Abschluss der Zahlung abgelaufen. Bitte erneut anmelden.',
  backToEvents: '← Zurück zu den Veranstaltungen',
  adminTitle: 'Verwaltung',
  adminLogin: 'Anmelden',
  adminLogout: 'Abmelden',
  adminPassword: 'Passwort',
  adminBadLogin: 'Falsche E-Mail oder Passwort.',
  adminEvents: 'Veranstaltungen',
  adminNewEvent: 'Neue Veranstaltung',
  adminUpcoming: 'Bevorstehend',
  adminPast: 'Vergangen',
  adminPublished: 'Veröffentlicht',
  adminDraft: 'Entwurf',
  adminConfirmed: 'Bestätigt',
  adminCapacity: 'Kapazität',
  adminPriceEur: 'Preis (€)',
  adminStartsAt: 'Beginn',
  adminEndsAt: 'Ende (optional)',
  adminLocation: 'Ort',
  adminTitleFi: 'Titel (FI)',
  adminTitleEn: 'Titel (EN)',
  adminDescFi: 'Beschreibung (FI)',
  adminDescEn: 'Beschreibung (EN)',
  adminSave: 'Speichern',
  adminDelete: 'Löschen',
  adminDeleteBlocked: 'Löschen nicht möglich: bestätigte Anmeldungen vorhanden.',
  adminAttendees: 'Teilnehmende',
  adminDownloadCsv: 'CSV herunterladen',
  adminStatus: 'Status',
  adminAmount: 'Bezahlt',
  adminCreated: 'Erstellt',
  adminEdit: 'Bearbeiten',
  adminNeedTitle: 'Gib der Veranstaltung mindestens in einer Sprache einen Titel.',
  adminBadPrice: 'Gib einen Preis wie 25 oder 25,50 ein.',
  adminBadCapacity: 'Die Kapazität muss eine ganze Zahl von mindestens 1 sein.',
}

// Elder Futhark transliteration
const runeMap: Record<string, string> = {
  a: 'ᚨ', b: 'ᛒ', c: 'ᚲ', d: 'ᛞ', e: 'ᛖ', f: 'ᚠ', g: 'ᚷ', h: 'ᚺ',
  i: 'ᛁ', j: 'ᛃ', k: 'ᚲ', l: 'ᛚ', m: 'ᛗ', n: 'ᚾ', o: 'ᛟ', p: 'ᛈ',
  q: 'ᚲ', r: 'ᚱ', s: 'ᛊ', t: 'ᛏ', u: 'ᚢ', v: 'ᚹ', w: 'ᚹ', x: 'ᚲᛊ',
  y: 'ᛃ', z: 'ᛉ', ä: 'ᚨ', ö: 'ᛟ', ü: 'ᚢ', å: 'ᚨ', ß: 'ᛊᛊ',
}

export function toRunes(text: string): string {
  return text.toLowerCase().split('').map(ch => runeMap[ch] ?? ch).join('')
}

function toRunesKeepingPlaceholders(text: string): string {
  return text
    .split(/(\{[a-z]+\})/)
    .map(part => (/^\{[a-z]+\}$/.test(part) ? part : toRunes(part)))
    .join('')
}

function runeStrings(base: Strings): Strings {
  return Object.fromEntries(
    Object.entries(base).map(([k, v]) => [k, toRunesKeepingPlaceholders(v)])
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
