from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Registration
from app.schemas import CheckoutIn, CheckoutOut
from app.services.checkout import (
    CheckoutError,
    confirmation_payload,
    send_with_retry,
    start_checkout,
)
from app.services.mailer import Mailer, get_mailer
from app.services.stripe_gateway import StripeGateway, get_stripe_gateway

router = APIRouter(prefix="/events", tags=["checkout"])


@router.post("/{slug}/checkout", response_model=CheckoutOut)
def checkout(
    slug: str,
    body: CheckoutIn,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    gateway: StripeGateway = Depends(get_stripe_gateway),
    mailer: Mailer = Depends(get_mailer),
) -> CheckoutOut:
    try:
        result = start_checkout(
            db,
            gateway,
            slug=slug,
            name=body.name.strip(),
            email=body.email,
            quantity=body.quantity,
            lang=body.lang,
        )
    except CheckoutError as e:
        if e.code == "not_found":
            raise HTTPException(status_code=404, detail="Event not found") from e
        if e.code == "sold_out":
            raise HTTPException(
                status_code=409, detail={"code": "sold_out", "seats_left": e.seats_left}
            ) from e
        raise HTTPException(status_code=502, detail={"code": "payment_unavailable"}) from e
    if result.confirmed:
        reg = db.get(Registration, result.registration_id)
        assert reg is not None
        to, subject, text = confirmation_payload(reg, body.lang)
        background.add_task(send_with_retry, mailer, to, subject, text)
    return CheckoutOut(
        registration_id=str(result.registration_id), checkout_url=result.checkout_url
    )
