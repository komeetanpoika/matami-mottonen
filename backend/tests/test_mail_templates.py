from datetime import UTC, datetime

from app.services.mail_templates import confirmation

KW = dict(
    event_title="Sound Bowl Evening",
    starts_at=datetime(2026, 10, 10, 15, 0, tzinfo=UTC),
    location="The moss",
    quantity=2,
    amount_cents=4000,
    contact_email="m@x.fi",
)


def test_english_body_has_helsinki_time_and_amount() -> None:
    subject, body = confirmation("en", **KW)
    assert "Sound Bowl Evening" in subject
    assert "10.10.2026 18:00" in body  # UTC+3 in October (EEST)
    assert "2 seats" in body and "40.00 €" in body and "m@x.fi" in body


def test_finnish_and_fallback() -> None:
    subject_fi, body_fi = confirmation("fi", **KW)
    assert "Vahvistus" in subject_fi and "2 paikkaa" in body_fi
    assert confirmation("de", **KW) == confirmation("en", **KW)
    assert confirmation("futhark", **KW) == confirmation("en", **KW)
