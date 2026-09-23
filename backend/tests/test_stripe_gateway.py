from datetime import UTC, datetime

import pytest
import stripe

from app.services.stripe_gateway import CheckoutSession, StripeError, StripeGateway


class _StubSessions:
    """Stands in for `client.v1.checkout.sessions`: records params, no network."""

    def __init__(self, response: object = None, error: Exception | None = None) -> None:
        self.calls: list[dict[str, object]] = []
        self._response = response
        self._error = error

    def create(self, params: dict[str, object] | None = None, options: object = None) -> object:
        self.calls.append(params or {})
        if self._error is not None:
            raise self._error
        return self._response


class _StubSession:
    def __init__(self, id: str, url: str) -> None:
        self.id = id
        self.url = url


def _gateway_with_stub(sessions: _StubSessions) -> StripeGateway:
    gateway = StripeGateway("sk_test_x", "whsec_x")
    # Replace the real Stripe SDK client with a namespace shaped like
    # client.v1.checkout.sessions, avoiding any network call.
    gateway._client = type(
        "StubClient",
        (),
        {"v1": type("V1", (), {"checkout": type("Checkout", (), {"sessions": sessions})()})()},
    )()
    return gateway


EXPIRES_AT = datetime(2026, 10, 10, 15, 0, tzinfo=UTC)


def test_create_checkout_session_sends_expected_params_and_returns_session() -> None:
    sessions = _StubSessions(response=_StubSession(id="cs_1", url="https://stripe.test/1"))
    gateway = _gateway_with_stub(sessions)

    result = gateway.create_checkout_session(
        registration_id="reg-1",
        product_name="Sound Bowl Evening",
        unit_amount=2500,
        currency="eur",
        quantity=2,
        customer_email="aino@example.fi",
        expires_at=EXPIRES_AT,
        success_url="http://test.local/events/thanks?reg=reg-1",
        cancel_url="http://test.local/events/sound-bowl?cancelled=reg-1",
    )

    assert result == CheckoutSession(id="cs_1", url="https://stripe.test/1")
    assert len(sessions.calls) == 1
    params = sessions.calls[0]
    assert params["mode"] == "payment"
    assert params["line_items"] == [
        {
            "price_data": {
                "currency": "eur",
                "unit_amount": 2500,
                "product_data": {"name": "Sound Bowl Evening"},
            },
            "quantity": 2,
        }
    ]
    assert params["customer_email"] == "aino@example.fi"
    assert params["client_reference_id"] == "reg-1"
    assert params["metadata"] == {"registration_id": "reg-1"}
    assert params["expires_at"] == int(EXPIRES_AT.timestamp())
    assert params["success_url"] == "http://test.local/events/thanks?reg=reg-1"
    assert params["cancel_url"] == "http://test.local/events/sound-bowl?cancelled=reg-1"


def test_sdk_stripe_error_surfaces_as_stripe_error() -> None:
    sessions = _StubSessions(error=stripe.StripeError("boom"))
    gateway = _gateway_with_stub(sessions)

    with pytest.raises(StripeError):
        gateway.create_checkout_session(
            registration_id="reg-1",
            product_name="Sound Bowl Evening",
            unit_amount=2500,
            currency="eur",
            quantity=2,
            customer_email="aino@example.fi",
            expires_at=EXPIRES_AT,
            success_url="http://test.local/events/thanks?reg=reg-1",
            cancel_url="http://test.local/events/sound-bowl?cancelled=reg-1",
        )
