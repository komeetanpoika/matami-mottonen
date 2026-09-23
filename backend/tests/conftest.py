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

from collections.abc import Iterator  # noqa: E402

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.config import settings  # noqa: E402

TABLES = "registrations, events, admin_users"


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
def client(db: Session) -> Iterator[TestClient]:
    from app.main import app

    with TestClient(app) as c:
        yield c
