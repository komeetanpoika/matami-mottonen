from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.services.checkout import confirmation_payload, send_with_retry
from app.services.mailer import Mailer, get_mailer
from app.services.stripe_gateway import StripeError, StripeGateway, get_stripe_gateway
from app.services.webhook import handle_event

router = APIRouter(prefix="/stripe", tags=["stripe"])


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    background: BackgroundTasks,
    stripe_signature: str = Header(default=""),
    db: Session = Depends(get_db),
    gateway: StripeGateway = Depends(get_stripe_gateway),
    mailer: Mailer = Depends(get_mailer),
) -> dict[str, bool]:
    payload = await request.body()
    try:
        event = gateway.construct_event(payload, stripe_signature)
    except StripeError as e:
        raise HTTPException(status_code=400, detail="Invalid signature") from e
    confirmed = handle_event(db, event)
    if confirmed is not None:
        to, subject, body = confirmation_payload(confirmed, confirmed.lang)
        background.add_task(send_with_retry, mailer, to, subject, body)
    return {"received": True}
