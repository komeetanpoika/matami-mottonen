from datetime import datetime
from zoneinfo import ZoneInfo

HELSINKI = ZoneInfo("Europe/Helsinki")


def _fmt_dt(dt: datetime) -> str:
    return dt.astimezone(HELSINKI).strftime("%d.%m.%Y %H:%M")


def _fmt_eur(cents: int) -> str:
    return f"{cents / 100:.2f} €"


def _fmt_seats(quantity: int, lang: str) -> str:
    if lang == "fi":
        return f"{quantity} paikka" if quantity == 1 else f"{quantity} paikkaa"
    return f"{quantity} seat" if quantity == 1 else f"{quantity} seats"


def confirmation(
    lang: str,
    *,
    event_title: str,
    starts_at: datetime,
    location: str | None,
    quantity: int,
    amount_cents: int,
    contact_email: str,
) -> tuple[str, str]:
    when = _fmt_dt(starts_at)
    where = location or "-"
    seats = _fmt_seats(quantity, lang)
    if lang == "fi":
        subject = f"Vahvistus: {event_title}"
        body = (
            f"Kiitos ilmoittautumisestasi!\n\n"
            f"Tapahtuma: {event_title}\n"
            f"Aika: {when}\n"
            f"Paikka: {where}\n"
            f"Paikkoja: {seats}\n"
            f"Maksettu: {_fmt_eur(amount_cents)}\n\n"
            f"Kysymyksiä? Vastaa tähän viestiin tai kirjoita osoitteeseen {contact_email}.\n\n"
            f"Nähdään sammalessa,\nMatami Möttönen"
        )
    else:
        subject = f"Confirmation: {event_title}"
        body = (
            f"Thank you for signing up!\n\n"
            f"Event: {event_title}\n"
            f"When: {when}\n"
            f"Where: {where}\n"
            f"Seats: {seats}\n"
            f"Paid: {_fmt_eur(amount_cents)}\n\n"
            f"Questions? Reply to this message or write to {contact_email}.\n\n"
            f"See you in the moss,\nMatami Möttönen"
        )
    return subject, body
