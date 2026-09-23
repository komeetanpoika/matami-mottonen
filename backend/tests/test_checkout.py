import threading
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Registration
from tests.conftest import FakeStripeGateway, RecordingMailer
from tests.factories import make_event

FORM = {"name": "Aino", "email": "aino@example.fi", "quantity": 2, "lang": "fi"}


def test_checkout_creates_pending_hold_and_stripe_session(
    client: TestClient, db: Session, stripe_fake: FakeStripeGateway
) -> None:
    ev = make_event(db, price_cents=2500, capacity=5)
    r = client.post(f"/api/events/{ev.slug}/checkout", json=FORM)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["checkout_url"] == "https://stripe.test/1"
    reg = db.scalar(select(Registration))
    assert reg is not None and str(reg.id) == body["registration_id"]
    assert reg.status == "pending" and reg.quantity == 2 and reg.amount_cents == 5000
    assert reg.stripe_session_id == "cs_test_1"
    assert timedelta(minutes=30) < reg.expires_at - datetime.now(UTC) <= timedelta(minutes=31)
    call = stripe_fake.calls[0]
    assert call["quantity"] == 2 and call["unit_amount"] == 2500 and call["currency"] == "eur"
    assert call["product_name"] == "Äänimaljailta"  # lang=fi picks the Finnish title
    assert call["success_url"] == f"http://test.local/events/thanks?reg={reg.id}"
    assert call["cancel_url"] == f"http://test.local/events/{ev.slug}?cancelled={reg.id}"
    assert call["customer_email"] == "aino@example.fi"
    assert client.get(f"/api/events/{ev.slug}").json()["seats_left"] == 3


def test_sold_out_returns_409_with_seats_left(client: TestClient, db: Session) -> None:
    ev = make_event(db, capacity=3)
    assert (
        client.post(f"/api/events/{ev.slug}/checkout", json={**FORM, "quantity": 2}).status_code
        == 200
    )
    r = client.post(f"/api/events/{ev.slug}/checkout", json={**FORM, "quantity": 2})
    assert r.status_code == 409
    assert r.json()["detail"] == {"code": "sold_out", "seats_left": 1}


def test_validation(client: TestClient, db: Session) -> None:
    ev = make_event(db)
    assert (
        client.post(f"/api/events/{ev.slug}/checkout", json={**FORM, "quantity": 0}).status_code
        == 422
    )
    assert (
        client.post(f"/api/events/{ev.slug}/checkout", json={**FORM, "quantity": 11}).status_code
        == 422
    )
    assert (
        client.post(f"/api/events/{ev.slug}/checkout", json={**FORM, "email": "x"}).status_code
        == 422
    )
    assert (
        client.post(f"/api/events/{ev.slug}/checkout", json={**FORM, "name": ""}).status_code == 422
    )
    assert (
        client.post(f"/api/events/{ev.slug}/checkout", json={**FORM, "name": "   "}).status_code
        == 422
    )
    assert client.post("/api/events/none/checkout", json=FORM).status_code == 404
    draft = make_event(db, is_published=False)
    assert client.post(f"/api/events/{draft.slug}/checkout", json=FORM).status_code == 404


def test_name_is_stored_stripped(client: TestClient, db: Session) -> None:
    ev = make_event(db)
    r = client.post(f"/api/events/{ev.slug}/checkout", json={**FORM, "name": "  Aino  "})
    assert r.status_code == 200, r.text
    assert db.scalar(select(Registration.name)) == "Aino"


def test_checkout_404_for_a_past_event(client: TestClient, db: Session) -> None:
    past = make_event(db, title_en="Past", starts_at=datetime.now(UTC) - timedelta(minutes=1))
    assert client.post(f"/api/events/{past.slug}/checkout", json=FORM).status_code == 404


def test_free_event_confirms_immediately_and_emails(
    client: TestClient, db: Session, stripe_fake: FakeStripeGateway, mailer_fake: RecordingMailer
) -> None:
    ev = make_event(db, price_cents=0)
    r = client.post(f"/api/events/{ev.slug}/checkout", json=FORM)
    assert r.status_code == 200 and r.json()["checkout_url"] is None
    reg = db.scalar(select(Registration))
    assert reg.status == "confirmed" and reg.confirmed_at is not None and reg.amount_cents == 0
    assert stripe_fake.calls == []
    assert len(mailer_fake.sent) == 1 and mailer_fake.sent[0][0] == "aino@example.fi"


def test_stripe_failure_rolls_back_hold(
    client: TestClient, db: Session, stripe_fake: FakeStripeGateway
) -> None:
    ev = make_event(db)
    stripe_fake.fail_next = True
    r = client.post(f"/api/events/{ev.slug}/checkout", json=FORM)
    assert r.status_code == 502
    assert db.scalar(select(Registration)) is None
    assert client.get(f"/api/events/{ev.slug}").json()["seats_left"] == 10


def test_last_seat_race_only_one_wins(client: TestClient, db: Session) -> None:
    ev = make_event(db, capacity=1)
    results: list[int] = []
    # Every thread is parked here until all four are ready, so the requests
    # really do contend for the row lock instead of trickling in one by one.
    barrier = threading.Barrier(4)

    def go() -> None:
        # One TestClient per thread: a single client is not safe to share across threads.
        with TestClient(client.app) as c:
            barrier.wait()
            results.append(
                c.post(f"/api/events/{ev.slug}/checkout", json={**FORM, "quantity": 1}).status_code
            )

    threads = [threading.Thread(target=go) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(results) == [200, 409, 409, 409]
    assert db.scalar(select(Registration.quantity).where(Registration.status == "pending")) == 1
