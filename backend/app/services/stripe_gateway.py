import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import stripe

from app.config import settings


class StripeError(Exception):
    pass


@dataclass(frozen=True)
class CheckoutSession:
    id: str
    url: str


class StripeGateway:
    def __init__(self, secret_key: str, webhook_secret: str) -> None:
        self._client = stripe.StripeClient(secret_key)
        self._webhook_secret = webhook_secret

    def create_checkout_session(
        self,
        *,
        registration_id: str,
        product_name: str,
        unit_amount: int,
        currency: str,
        quantity: int,
        customer_email: str,
        expires_at: datetime,
        success_url: str,
        cancel_url: str,
    ) -> CheckoutSession:
        try:
            s = self._client.v1.checkout.sessions.create(
                params={
                    "mode": "payment",
                    "line_items": [
                        {
                            "price_data": {
                                "currency": currency,
                                "unit_amount": unit_amount,
                                "product_data": {"name": product_name},
                            },
                            "quantity": quantity,
                        }
                    ],
                    "customer_email": customer_email,
                    "client_reference_id": registration_id,
                    "metadata": {"registration_id": registration_id},
                    "expires_at": int(expires_at.timestamp()),
                    "success_url": success_url,
                    "cancel_url": cancel_url,
                }
            )
        except stripe.StripeError as e:  # network, auth, validation
            raise StripeError(str(e)) from e
        if not s.url:
            raise StripeError("Stripe returned no checkout URL")
        return CheckoutSession(id=s.id, url=s.url)

    def expire_session(self, session_id: str) -> None:
        try:
            self._client.v1.checkout.sessions.expire(session_id)
        except stripe.StripeError as e:
            raise StripeError(str(e)) from e

    def construct_event(self, payload: bytes, signature: str) -> dict[str, Any]:
        """Verify the webhook signature and return the event as a plain dict. Raises StripeError."""
        try:
            event = stripe.Webhook.construct_event(payload, signature, self._webhook_secret)
        except (ValueError, stripe.SignatureVerificationError) as e:
            raise StripeError(str(e)) from e
        if hasattr(event, "to_dict_recursive"):
            return event.to_dict_recursive()
        # This SDK version's Event has no to_dict_recursive(); the payload's bytes are
        # already signature-verified, so re-parse them directly for a plain dict.
        return json.loads(payload)


_gateway: StripeGateway | None = None


def get_stripe_gateway() -> StripeGateway:
    global _gateway
    if _gateway is None:
        _gateway = StripeGateway(settings.stripe_secret_key, settings.stripe_webhook_secret)
    return _gateway
