import csv
import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db import get_db
from app.models import Event, Registration
from app.schemas import AdminRegistrationOut

router = APIRouter(prefix="/admin/events", tags=["admin"], dependencies=[Depends(require_admin)])

_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _csv_safe(value: str) -> str:
    """Prefix a value with `'` if it could be read as a spreadsheet formula.

    `name`/`email` come from the anonymous public checkout form, so an
    admin opening the export in Excel/Sheets must not have attacker-supplied
    strings like `=HYPERLINK(...)` execute as a formula.
    """
    if value.startswith(_FORMULA_PREFIXES):
        return f"'{value}"
    return value


def _rows(db: Session, event_id: int) -> list[Registration]:
    if db.get(Event, event_id) is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return list(
        db.scalars(
            select(Registration)
            .where(Registration.event_id == event_id)
            .order_by(Registration.created_at.desc())
        )
    )


@router.get("/{event_id}/registrations", response_model=list[AdminRegistrationOut])
def list_registrations(event_id: int, db: Session = Depends(get_db)) -> list[AdminRegistrationOut]:
    return [
        AdminRegistrationOut(
            id=str(r.id),
            name=r.name,
            email=r.email,
            quantity=r.quantity,
            status=r.status,
            amount_cents=r.amount_cents,
            created_at=r.created_at,
            confirmed_at=r.confirmed_at,
        )
        for r in _rows(db, event_id)
    ]


@router.get("/{event_id}/registrations.csv")
def registrations_csv(event_id: int, db: Session = Depends(get_db)) -> Response:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["name", "email", "quantity", "status", "amount_eur", "created_at"])
    for r in _rows(db, event_id):
        w.writerow(
            [
                _csv_safe(r.name),
                _csv_safe(r.email),
                r.quantity,
                r.status,
                f"{r.amount_cents / 100:.2f}",
                r.created_at.isoformat(),
            ]
        )
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="event-{event_id}-registrations.csv"'
        },
    )
