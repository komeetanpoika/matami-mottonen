import csv
import io
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Registration
from tests.factories import login, make_event


def _seed(db: Session):
    ev = make_event(db)
    now = datetime.now(UTC)
    db.add_all(
        [
            Registration(
                event_id=ev.id,
                name="Aino",
                email="a@x.fi",
                quantity=2,
                status="confirmed",
                amount_cents=4000,
                expires_at=now,
                confirmed_at=now,
                created_at=now - timedelta(hours=1),
            ),
            Registration(
                event_id=ev.id,
                name="Bo",
                email="b@x.fi",
                quantity=1,
                status="expired",
                amount_cents=2000,
                expires_at=now,
                created_at=now,
            ),
        ]
    )
    db.commit()
    return ev


def test_requires_login(client: TestClient, db: Session) -> None:
    ev = _seed(db)
    assert client.get(f"/api/admin/events/{ev.id}/registrations").status_code == 401


def test_list_newest_first(client: TestClient, db: Session) -> None:
    ev = _seed(db)
    login(client)
    rows = client.get(f"/api/admin/events/{ev.id}/registrations").json()
    assert [r["name"] for r in rows] == ["Bo", "Aino"]
    assert rows[1] == {
        **rows[1],
        "email": "a@x.fi",
        "quantity": 2,
        "status": "confirmed",
        "amount_cents": 4000,
    }
    assert client.get("/api/admin/events/999/registrations").status_code == 404


def test_csv(client: TestClient, db: Session) -> None:
    ev = _seed(db)
    login(client)
    r = client.get(f"/api/admin/events/{ev.id}/registrations.csv")
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/csv")
    lines = r.text.strip().splitlines()
    assert lines[0] == "name,email,quantity,status,amount_eur,created_at"
    assert lines[1].startswith("Bo,b@x.fi,1,expired,20.00,")
    assert lines[2].startswith("Aino,a@x.fi,2,confirmed,40.00,")


def test_csv_neutralises_formula_injection(client: TestClient, db: Session) -> None:
    ev = make_event(db)
    now = datetime.now(UTC)
    db.add(
        Registration(
            event_id=ev.id,
            name='=HYPERLINK("http://evil")',
            email="e@x.fi",
            quantity=1,
            status="confirmed",
            amount_cents=1000,
            expires_at=now,
            confirmed_at=now,
            created_at=now,
        )
    )
    db.commit()
    login(client)
    r = client.get(f"/api/admin/events/{ev.id}/registrations.csv")
    rows = list(csv.reader(io.StringIO(r.text)))
    assert rows[1][0] == '\'=HYPERLINK("http://evil")'
