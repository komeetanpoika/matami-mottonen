import json
import threading
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Registration
from tests.conftest import RecordingMailer
from tests.factories import make_event
from tests.stripe_sig import sign

SECRET = "whsec_test_secret"


def _reg(db: Session, status: str = "pending", **kw: object) -> Registration:
    ev = make_event(db)
    now = datetime.now(UTC)
    values: dict[str, object] = dict(
        event_id=ev.id,
        name="A",
        email="a@x.fi",
        quantity=2,
        status=status,
        amount_cents=4000,
        expires_at=now + timedelta(minutes=30),
        stripe_session_id="cs_1",
    )
    values.update(kw)
    reg = Registration(**values)
    db.add(reg)
    db.commit()
    db.refresh(reg)
    return reg


def _post(client: TestClient, event: dict, secret: str = SECRET):
    payload = json.dumps(event).encode()
    return client.post(
        "/api/stripe/webhook",
        content=payload,
        headers={"Stripe-Signature": sign(payload, secret), "Content-Type": "application/json"},
    )


def _completed(reg: Registration, **obj: object) -> dict:
    obj.setdefault("payment_status", "paid")
    return _session_event("checkout.session.completed", reg, **obj)


def _session_event(kind: str, reg: Registration, **obj: object) -> dict:
    return {
        "id": "evt_1",
        "type": kind,
        "data": {
            "object": {
                "id": "cs_1",
                "payment_intent": "pi_1",
                "client_reference_id": str(reg.id),
                "metadata": {"registration_id": str(reg.id)},
                **obj,
            }
        },
    }


def test_bad_signature_400(client: TestClient, db: Session) -> None:
    reg = _reg(db)
    assert _post(client, _completed(reg), secret="whsec_wrong").status_code == 400
    db.refresh(reg)
    assert reg.status == "pending"


def test_completed_confirms_and_emails(
    client: TestClient, db: Session, mailer_fake: RecordingMailer
) -> None:
    reg = _reg(db)
    r = _post(client, _completed(reg))
    assert r.status_code == 200 and r.json() == {"received": True}
    db.refresh(reg)
    assert reg.status == "confirmed" and reg.stripe_payment_intent_id == "pi_1" and reg.confirmed_at
    assert len(mailer_fake.sent) == 1 and "Sound Bowl Evening" in mailer_fake.sent[0][1]


def test_completed_is_idempotent(
    client: TestClient, db: Session, mailer_fake: RecordingMailer
) -> None:
    reg = _reg(db)
    _post(client, _completed(reg))
    _post(client, _completed(reg))
    assert len(mailer_fake.sent) == 1


def test_completed_found_via_metadata_when_session_unknown(client: TestClient, db: Session) -> None:
    reg = _reg(db, stripe_session_id=None)
    _post(client, _completed(reg))
    db.refresh(reg)
    assert reg.status == "confirmed"


def test_expired_releases_hold(client: TestClient, db: Session) -> None:
    reg = _reg(db)
    ev = {
        "id": "evt_2",
        "type": "checkout.session.expired",
        "data": {"object": {"id": "cs_1", "metadata": {}}},
    }
    assert _post(client, ev).status_code == 200
    db.refresh(reg)
    assert reg.status == "expired"


def test_expired_does_not_touch_confirmed(client: TestClient, db: Session) -> None:
    reg = _reg(db, status="confirmed")
    _post(
        client,
        {
            "id": "evt_3",
            "type": "checkout.session.expired",
            "data": {"object": {"id": "cs_1", "metadata": {}}},
        },
    )
    db.refresh(reg)
    assert reg.status == "confirmed"


def test_refund_cancels(client: TestClient, db: Session) -> None:
    reg = _reg(db, status="confirmed", stripe_payment_intent_id="pi_1")
    ev = {
        "id": "evt_4",
        "type": "charge.refunded",
        "data": {
            "object": {
                "id": "ch_1",
                "payment_intent": "pi_1",
                "refunded": True,
                "amount": 4000,
                "amount_refunded": 4000,
            }
        },
    }
    assert _post(client, ev).status_code == 200
    db.refresh(reg)
    assert reg.status == "cancelled"


def test_partial_refund_is_ignored(client: TestClient, db: Session) -> None:
    reg = _reg(db, status="confirmed", stripe_payment_intent_id="pi_1")
    ev = {
        "id": "evt_4b",
        "type": "charge.refunded",
        "data": {
            "object": {
                "id": "ch_1",
                "payment_intent": "pi_1",
                "refunded": False,
                "amount": 4000,
                "amount_refunded": 500,
            }
        },
    }
    assert _post(client, ev).status_code == 200
    db.refresh(reg)
    assert reg.status == "confirmed"


def test_unknown_registration_and_unknown_type_are_acknowledged(
    client: TestClient, db: Session
) -> None:
    ev = {
        "id": "evt_5",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_none",
                "payment_intent": "pi_x",
                "payment_status": "paid",
                "client_reference_id": "nope",
                "metadata": {},
            }
        },
    }
    assert _post(client, ev).status_code == 200
    assert (
        _post(
            client, {"id": "evt_6", "type": "payment_intent.created", "data": {"object": {}}}
        ).status_code
        == 200
    )


def test_email_retries_then_succeeds(
    client: TestClient, db: Session, mailer_fake: RecordingMailer, monkeypatch
) -> None:
    import app.services.checkout as co

    monkeypatch.setattr(co.time, "sleep", lambda _s: None)
    mailer_fake.fail_times = 2
    reg = _reg(db)
    _post(client, _completed(reg))
    assert len(mailer_fake.sent) == 1


def test_concurrent_completed_confirms_once(
    client: TestClient, db: Session, mailer_fake: RecordingMailer
) -> None:
    reg = _reg(db)
    payload = json.dumps(_completed(reg)).encode()
    headers = {"Stripe-Signature": sign(payload, SECRET), "Content-Type": "application/json"}
    barrier = threading.Barrier(2)
    results: list[int] = []

    def _worker() -> None:
        barrier.wait()
        with TestClient(client.app) as c:
            r = c.post("/api/stripe/webhook", content=payload, headers=headers)
            results.append(r.status_code)

    threads = [threading.Thread(target=_worker) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert results == [200, 200]
    db.refresh(reg)
    assert reg.status == "confirmed"
    assert len(mailer_fake.sent) == 1


def test_completed_without_paid_payment_status_leaves_hold_pending(
    client: TestClient, db: Session, mailer_fake: RecordingMailer
) -> None:
    reg = _reg(db)
    assert _post(client, _completed(reg, payment_status="unpaid")).status_code == 200
    db.refresh(reg)
    assert reg.status == "pending" and reg.confirmed_at is None
    assert mailer_fake.sent == []


def test_async_payment_succeeded_confirms_and_emails(
    client: TestClient, db: Session, mailer_fake: RecordingMailer
) -> None:
    reg = _reg(db)
    _post(client, _completed(reg, payment_status="unpaid"))
    r = _post(client, _session_event("checkout.session.async_payment_succeeded", reg))
    assert r.status_code == 200
    db.refresh(reg)
    assert reg.status == "confirmed" and reg.confirmed_at is not None
    assert len(mailer_fake.sent) == 1


def test_async_payment_failed_releases_hold(client: TestClient, db: Session) -> None:
    reg = _reg(db)
    assert (
        _post(client, _session_event("checkout.session.async_payment_failed", reg)).status_code
        == 200
    )
    db.refresh(reg)
    assert reg.status == "expired"


def test_completed_for_expired_registration_confirms_anyway(
    client: TestClient, db: Session, mailer_fake: RecordingMailer
) -> None:
    # The sweep released the hold while the customer was still paying.
    reg = _reg(db, status="expired", expires_at=datetime.now(UTC) - timedelta(minutes=1))
    assert _post(client, _completed(reg)).status_code == 200
    db.refresh(reg)
    assert reg.status == "confirmed" and reg.confirmed_at is not None
    assert len(mailer_fake.sent) == 1
