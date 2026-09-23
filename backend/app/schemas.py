from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class LoginIn(BaseModel):
    # Plain str, not EmailStr: email-validator unconditionally rejects the
    # ".local" TLD (IANA special-use, not a deliverability check), and
    # ".local" addresses are baked into conftest.py's APP_ADMIN_EMAIL and
    # this feature's test fixtures.
    email: str
    password: str


class MeOut(BaseModel):
    email: str


class EventIn(BaseModel):
    title_fi: str | None = Field(default=None, max_length=200)
    title_en: str | None = Field(default=None, max_length=200)
    description_fi: str | None = None
    description_en: str | None = None
    starts_at: datetime
    ends_at: datetime | None = None
    location: str | None = Field(default=None, max_length=300)
    price_cents: int = Field(ge=0)
    capacity: int = Field(ge=1)
    is_published: bool = False

    @model_validator(mode="after")
    def _some_title(self) -> "EventIn":
        if not (self.title_fi or self.title_en):
            raise ValueError("title_fi or title_en is required")
        if self.ends_at is not None and self.ends_at < self.starts_at:
            raise ValueError("ends_at before starts_at")
        return self


class EventOut(BaseModel):
    """Public shape."""

    id: int
    slug: str
    title_fi: str | None
    title_en: str | None
    description_fi: str | None
    description_en: str | None
    starts_at: datetime
    ends_at: datetime | None
    location: str | None
    price_cents: int
    currency: str
    capacity: int
    seats_left: int
    sold_out: bool


class AdminEventOut(EventOut):
    is_published: bool
    confirmed_count: int
    pending_count: int


class CheckoutIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    quantity: int = Field(ge=1, le=10)
    lang: str = Field(default="en", pattern="^(fi|en|de|futhark)$")

    @field_validator("name")
    @classmethod
    def _strip_name(cls, v: str) -> str:
        # Strip inside validation so an all-whitespace name is a 422, not an
        # empty name smuggled past min_length and stripped by the endpoint.
        stripped = v.strip()
        if not stripped:
            raise ValueError("name must not be blank")
        return stripped


class CheckoutOut(BaseModel):
    registration_id: str
    checkout_url: str | None


class RegistrationStatusOut(BaseModel):
    status: str
    event_slug: str
    quantity: int


class AdminRegistrationOut(BaseModel):
    id: str
    name: str
    email: str
    quantity: int
    status: str
    amount_cents: int
    created_at: datetime
    confirmed_at: datetime | None
