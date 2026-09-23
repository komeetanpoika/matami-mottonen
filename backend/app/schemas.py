from pydantic import BaseModel


class LoginIn(BaseModel):
    # Plain str, not EmailStr: email-validator unconditionally rejects the
    # ".local" TLD (IANA special-use, not a deliverability check), and
    # ".local" addresses are baked into conftest.py's APP_ADMIN_EMAIL and
    # this feature's test fixtures.
    email: str
    password: str


class MeOut(BaseModel):
    email: str
