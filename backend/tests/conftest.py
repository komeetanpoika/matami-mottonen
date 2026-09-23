import os

# Must run before any app import.
os.environ["APP_ENV"] = "test"
os.environ["APP_DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://fish:fish@localhost:5433/matami_test"
)
os.environ["APP_ADMIN_EMAIL"] = "owner@test.local"
os.environ["APP_ADMIN_PASSWORD"] = "owner-pass"
os.environ["APP_STRIPE_WEBHOOK_SECRET"] = "whsec_test_secret"
os.environ["APP_PUBLIC_BASE_URL"] = "http://test.local"
os.environ["APP_SWEEP_INTERVAL_SECONDS"] = "0"

import threading  # noqa: E402
from collections.abc import Iterator  # noqa: E402
from dataclasses import dataclass, field  # noqa: E402

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.config import settings  # noqa: E402
from app.services.mailer import Mailer, get_mailer  # noqa: E402
from app.services.stripe_gateway import (  # noqa: E402
    CheckoutSession,
    StripeError,
    StripeGateway,
    get_stripe_gateway,
)

TABLES = "registrations, events, admin_users"


class FakeStripeGateway(StripeGateway):
    def __init__(self) -> None:
        super().__init__(secret_key="sk_test_fake", webhook_secret=settings.stripe_webhook_secret)
        self.calls: list[dict[str, object]] = []
        self.expired: list[str] = []
        self.fail_next = False
        self.fail_expire = False
        self._lock = threading.Lock()

    def create_checkout_session(self, **kw: object) -> CheckoutSession:
        with self._lock:
            if self.fail_next:
                self.fail_next = False
                raise StripeError("simulated outage")
            self.calls.append(kw)
            n = len(self.calls)
            return CheckoutSession(id=f"cs_test_{n}", url=f"https://stripe.test/{n}")

    def expire_session(self, session_id: str) -> None:
        if self.fail_expire:
            raise StripeError("simulated expire failure")
        self.expired.append(session_id)


@dataclass
class RecordingMailer(Mailer):
    sent: list[tuple[str, str, str]] = field(default_factory=list)
    fail_times: int = 0

    def send(self, to: str, subject: str, body: str) -> None:
        if self.fail_times > 0:
            self.fail_times -= 1
            raise OSError("smtp down")
        self.sent.append((to, subject, body))


@pytest.fixture()
def stripe_fake() -> FakeStripeGateway:
    return FakeStripeGateway()


@pytest.fixture()
def mailer_fake() -> RecordingMailer:
    return RecordingMailer()


@pytest.fixture(scope="session")
def migrated_db() -> None:
    base_url, test_db_name = settings.database_url.rsplit("/", 1)
    admin = create_engine(base_url + "/postgres", isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{test_db_name}" WITH (FORCE)'))
        conn.execute(text(f'CREATE DATABASE "{test_db_name}"'))
    admin.dispose()
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture()
def db(migrated_db: None) -> Iterator[Session]:
    """A committing session on a freshly truncated database.

    Endpoints open their own sessions (real `get_db`), so tests seed with
    `db.commit()` and re-read with `db.expire_all()` / fresh queries.
    """
    from app.db import SessionLocal, engine

    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {TABLES} RESTART IDENTITY CASCADE"))
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture()
def client(
    db: Session, stripe_fake: FakeStripeGateway, mailer_fake: RecordingMailer
) -> Iterator[TestClient]:
    from app.main import app

    app.dependency_overrides[get_stripe_gateway] = lambda: stripe_fake
    app.dependency_overrides[get_mailer] = lambda: mailer_fake
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
