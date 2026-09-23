import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Registration
from app.repositories import registrations as repo
from app.schemas import RegistrationStatusOut
from app.services.stripe_gateway import StripeGateway, get_stripe_gateway
from app.services.webhook import cancel_pending

router = APIRouter(prefix="/registrations", tags=["registrations"])


def _load(db: Session, reg_id: str) -> Registration:
    try:
        parsed = uuid.UUID(reg_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Registration not found") from None
    reg = repo.get(db, parsed)
    if reg is None:
        raise HTTPException(status_code=404, detail="Registration not found")
    return reg


@router.get("/{reg_id}/status", response_model=RegistrationStatusOut)
def status(reg_id: str, db: Session = Depends(get_db)) -> RegistrationStatusOut:
    reg = _load(db, reg_id)
    return RegistrationStatusOut(
        status=reg.status, event_slug=reg.event.slug, quantity=reg.quantity
    )


@router.post("/{reg_id}/cancel", status_code=204)
def cancel(
    reg_id: str,
    db: Session = Depends(get_db),
    gateway: StripeGateway = Depends(get_stripe_gateway),
) -> None:
    reg = _load(db, reg_id)
    if not cancel_pending(db, gateway, reg):
        raise HTTPException(status_code=409, detail="Registration is not pending")
