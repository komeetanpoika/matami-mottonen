# Event Calendar + Ticketing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a public event calendar with paid (Stripe Checkout) sign-ups and an owner admin UI to the Matami Möttönen site, packaged for self-hosting with docker-compose.

**Architecture:** The existing Vite/React landing page moves to `frontend/` and gains React Router pages (`/events`, `/events/:slug`, `/events/thanks`, `/admin/*`). A new FastAPI + Postgres backend in `backend/` owns events, registrations (reserve-then-pay holds), Stripe Checkout sessions and the webhook, admin auth (Argon2 + signed cookie), and SMTP confirmation emails. `docker-compose.yml` runs `db`, `api`, `web` (nginx serving the built SPA and proxying `/api`).

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2, psycopg 3, Alembic, pydantic-settings, pwdlib[argon2], itsdangerous, stripe (Python SDK), pytest + httpx; React 18, TypeScript, Vite 5, react-router-dom 6, vitest, Playwright; Postgres 16; nginx.

**Spec:** `docs/superpowers/specs/2026-09-23-event-calendar-ticketing-design.md`

## Global Constraints

- Python `>=3.12`; backend venv at `backend/.venv`; run backend commands from `backend/` with the venv active.
- Local Postgres is at `localhost:5433`, role `fish`/`fish` (can create databases). Dev DB `matami`, test DB `matami_test` (created/dropped by the test suite).
- All settings are `APP_`-prefixed env vars via pydantic-settings (`app/config.py`); never read `os.environ` elsewhere.
- `app/domain/` must not import SQLAlchemy, FastAPI, or stripe.
- Every model change ships an Alembic migration; tests run `alembic upgrade head`.
- Times are stored and returned as UTC ISO 8601; display timezone is `Europe/Helsinki` (frontend and email).
- Registration status values: `pending`, `confirmed`, `cancelled`, `expired`. Quantity `1..10`. Hold length `APP_HOLD_MINUTES` default `31` (Stripe requires a session `expires_at` ≥ 30 min after creation; the extra minute absorbs clock skew).
- Currency is `EUR`; `price_cents = 0` means a free event that skips Stripe.
- Event copy fields: `title_fi`, `title_en`, `description_fi`, `description_en`; at least one title required. Frontend `pickLocalized`: `fi → fi ?? en`; `en`/`de → en ?? fi`; `futhark → toRunes(en ?? fi)`.
- New UI copy goes into `frontend/src/translations.ts` `Strings` for `en`, `fi`, `de` (Futhark is derived from `en`).
- Commit after every task with a conventional message ending in `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.
- Backend lint: `ruff check . && ruff format --check .`; frontend: `npm run lint && npx tsc -b`.

---

## File map

**Root**
- `docker-compose.yml`, `.env.example`, `DEPLOY.md`, `.gitignore` (update), `README.md` (rewrite)

**frontend/** (moved from root; new files marked ★)
- `src/main.tsx` — router setup
- ★ `src/lang.tsx` — `LangProvider`, `useLang()`; ★ `src/components/LangSwitcher.tsx`
- `src/translations.ts` — extended `Strings`
- ★ `src/localized.ts` — `pickLocalized`, `formatEventDate`; ★ `src/localized.test.ts`
- ★ `src/api/client.ts` — typed fetch helpers + `ApiError`
- ★ `src/theme.ts` — shared colours/style objects
- `src/pages/LandingPage.tsx` (from `App.tsx`) + ★ `src/components/UpcomingSection.tsx`
- ★ `src/pages/EventsPage.tsx`, ★ `src/pages/EventDetailPage.tsx`, ★ `src/pages/ThanksPage.tsx`
- ★ `src/pages/admin/AdminLayout.tsx`, `AdminLoginPage.tsx`, `AdminEventsPage.tsx`, `AdminEventFormPage.tsx`, `AdminAttendeesPage.tsx`
- ★ `e2e/signup.spec.ts`, ★ `playwright.config.ts`, ★ `Dockerfile`, ★ `nginx.conf`

**backend/**
- `pyproject.toml`, `alembic.ini`, `alembic/env.py`, `alembic/versions/0001_initial.py`, `Dockerfile`, `README.md`
- `app/main.py`, `app/config.py`, `app/db.py`, `app/security.py`
- `app/models/{__init__,base,admin_user,event,registration}.py`
- `app/domain/{capacity,registration_state,slug}.py`
- `app/repositories/{events,registrations}.py`
- `app/services/{stripe_gateway,checkout,webhook,mailer,mail_templates,sweep,auth}.py`
- `app/api/{deps,rate_limit,auth,events,checkout,registrations,stripe_webhook,admin_events,admin_registrations}.py`
- `app/schemas.py`
- `tests/conftest.py`, `tests/factories.py`, `tests/test_*.py`

---

### Task 1: Move the frontend into `frontend/` and set up the monorepo root

**Files:**
- Move: everything except `.git`, `docs/`, `README.md` → `frontend/`
- Create: `.gitignore` (root), `README.md` (root, rewrite)
- Modify: `frontend/index.html` (title), `frontend/vite.config.ts` (proxy)

**Interfaces:**
- Produces: `frontend/` as the Vite app root; `npm run dev` in `frontend/` proxies `/api` to `http://localhost:8000`.

- [ ] **Step 1: Move files**

```bash
cd /home/lappemikb/projects/matami-mottonen
mkdir frontend
git mv index.html package.json package-lock.json eslint.config.js postcss.config.js tailwind.config.js tsconfig.app.json tsconfig.json tsconfig.node.json vite.config.ts public src frontend/
git mv .gitignore frontend/.gitignore
mv node_modules frontend/node_modules
```

- [ ] **Step 2: Root `.gitignore` and README**

Root `.gitignore`:
```
node_modules
dist
.env
*.local
.venv
__pycache__
*.pyc
.pytest_cache
.ruff_cache
.DS_Store
```

Root `README.md`:
```markdown
# Matami Möttönen

Landing page + event calendar with paid sign-ups.

- `frontend/` — React + Vite site (`npm run dev` → http://localhost:5173)
- `backend/` — FastAPI + Postgres API (`uvicorn app.main:app --reload` → http://localhost:8000)
- `docker-compose.yml` — production stack; see `DEPLOY.md`
- Design: `docs/superpowers/specs/2026-09-23-event-calendar-ticketing-design.md`
```

- [ ] **Step 3: Vite proxy and page title**

`frontend/vite.config.ts`:
```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': { target: process.env.BACKEND_URL ?? 'http://localhost:8000', changeOrigin: true },
    },
  },
})
```

In `frontend/index.html` change `<title>Vite + React + TS</title>` to `<title>Matami Möttönen</title>`.

- [ ] **Step 4: Verify build and lint**

Run: `cd frontend && npm run lint && npm run build`
Expected: no lint errors; `dist/` produced.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "chore: move Vite app into frontend/ and add monorepo root

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 2: Backend scaffold — settings, DB, models, initial migration, test harness

**Files:**
- Create: `backend/pyproject.toml`, `backend/alembic.ini`, `backend/alembic/env.py`, `backend/alembic/script.py.mako`, `backend/alembic/versions/0001_initial.py`
- Create: `backend/app/__init__.py`, `backend/app/config.py`, `backend/app/db.py`, `backend/app/main.py`
- Create: `backend/app/models/__init__.py`, `base.py`, `admin_user.py`, `event.py`, `registration.py`
- Create: `backend/tests/__init__.py`, `backend/tests/conftest.py`, `backend/tests/test_health.py`, `backend/tests/test_schema.py`

**Interfaces:**
- Produces: `settings` (`app.config`), `engine`/`SessionLocal`/`get_db` (`app.db`), models `AdminUser`, `Event`, `Registration` and `Base`; test fixtures `db: Session` (fresh truncated DB per test, committing) and `client: TestClient`; `create_app()` in `app.main` and module-level `app`.

- [ ] **Step 1: pyproject**

`backend/pyproject.toml`:
```toml
[project]
name = "matami-backend"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",
    "sqlalchemy>=2.0",
    "psycopg[binary]>=3.2",
    "alembic>=1.13",
    "pydantic-settings>=2.4",
    "pydantic[email]>=2.8",
    "pwdlib[argon2]>=0.2",
    "itsdangerous>=2.2",
    "stripe>=10",
]

[project.optional-dependencies]
dev = ["pytest>=8", "httpx>=0.27", "ruff>=0.6"]

[tool.setuptools.packages.find]
include = ["app*"]

[tool.ruff]
line-length = 100
target-version = "py312"
extend-exclude = ["alembic"]

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]

[tool.ruff.lint.per-file-ignores]
"tests/conftest.py" = ["I001", "E402"]
"app/api/*.py" = ["B008"]
"app/main.py" = ["B008"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Create venv and install**

```bash
cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"
psql -h localhost -p 5433 -U fish -d postgres -c 'CREATE DATABASE matami' || true   # PGPASSWORD=fish
```

- [ ] **Step 3: config and db**

`backend/app/config.py`:
```python
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

_DEV_SECRET = "dev-secret-change-me"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env")

    env: Literal["dev", "test", "production"] = "dev"
    database_url: str = "postgresql+psycopg://fish:fish@localhost:5433/matami"
    secret_key: str = _DEV_SECRET
    session_ttl_hours: int = 336  # 14 days
    login_rate_limit: int = 5  # attempts / 5 min per IP
    public_base_url: str = "http://localhost:5173"
    admin_email: str = "admin@example.com"
    admin_password: str = "admin"
    stripe_secret_key: str = "sk_test_placeholder"
    stripe_webhook_secret: str = "whsec_placeholder"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str = "matami@example.com"
    contact_email: str = "matami@example.com"
    hold_minutes: int = 31
    sweep_interval_seconds: int = 300

    def model_post_init(self, _context: object) -> None:
        if self.env == "production" and self.secret_key == _DEV_SECRET:
            raise RuntimeError("APP_SECRET_KEY must be set in production")


settings = Settings()
```

`backend/app/db.py`:
```python
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 4: Models**

`backend/app/models/base.py`:
```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

`backend/app/models/admin_user.py`:
```python
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AdminUser(Base):
    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
```

`backend/app/models/event.py`:
```python
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint("price_cents >= 0", name="ck_events_price_nonneg"),
        CheckConstraint("capacity >= 1", name="ck_events_capacity_pos"),
        CheckConstraint(
            "title_fi IS NOT NULL OR title_en IS NOT NULL", name="ck_events_some_title"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True)
    title_fi: Mapped[str | None] = mapped_column(String(200))
    title_en: Mapped[str | None] = mapped_column(String(200))
    description_fi: Mapped[str | None] = mapped_column(Text)
    description_en: Mapped[str | None] = mapped_column(Text)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    location: Mapped[str | None] = mapped_column(String(300))
    price_cents: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    capacity: Mapped[int] = mapped_column(Integer)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
```

`backend/app/models/registration.py`:
```python
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.event import Event

STATUSES = ("pending", "confirmed", "cancelled", "expired")


class Registration(Base):
    __tablename__ = "registrations"
    __table_args__ = (
        CheckConstraint("quantity BETWEEN 1 AND 10", name="ck_registrations_quantity"),
        CheckConstraint(
            "status IN ('pending','confirmed','cancelled','expired')",
            name="ck_registrations_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="RESTRICT"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(320))
    quantity: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    amount_cents: Mapped[int] = mapped_column(Integer)
    lang: Mapped[str] = mapped_column(String(8), default="en")  # email language
    stripe_session_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(String(255), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    event: Mapped[Event] = relationship()
```

`backend/app/models/__init__.py`:
```python
from app.models.admin_user import AdminUser
from app.models.base import Base
from app.models.event import Event
from app.models.registration import STATUSES, Registration

__all__ = ["AdminUser", "Base", "Event", "Registration", "STATUSES"]
```

- [ ] **Step 5: Alembic**

`backend/alembic.ini`:
```ini
[alembic]
script_location = %(here)s/alembic
prepend_sys_path = .
path_separator = os
sqlalchemy.url =

[loggers]
keys = root,sqlalchemy,alembic
[handlers]
keys = console
[formatters]
keys = generic
[logger_root]
level = WARNING
handlers = console
qualname =
[logger_sqlalchemy]
level = WARNING
handlers =
qualname = sqlalchemy.engine
[logger_alembic]
level = INFO
handlers =
qualname = alembic
[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic
[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

`backend/alembic/env.py`:
```python
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import settings
from app.models import Base

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)
target_metadata = Base.metadata

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

`backend/alembic/script.py.mako`:
```mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

`backend/alembic/versions/0001_initial.py`:
```python
"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-09-23
"""
import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "admin_users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
    )
    op.create_table(
        "events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("slug", sa.String(120), nullable=False, unique=True),
        sa.Column("title_fi", sa.String(200)),
        sa.Column("title_en", sa.String(200)),
        sa.Column("description_fi", sa.Text),
        sa.Column("description_en", sa.Text),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True)),
        sa.Column("location", sa.String(300)),
        sa.Column("price_cents", sa.Integer, nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="EUR"),
        sa.Column("capacity", sa.Integer, nullable=False),
        sa.Column("is_published", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("price_cents >= 0", name="ck_events_price_nonneg"),
        sa.CheckConstraint("capacity >= 1", name="ck_events_capacity_pos"),
        sa.CheckConstraint("title_fi IS NOT NULL OR title_en IS NOT NULL", name="ck_events_some_title"),
    )
    op.create_index("ix_events_starts_at", "events", ["starts_at"])
    op.create_table(
        "registrations",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("event_id", sa.Integer, sa.ForeignKey("events.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("quantity", sa.Integer, nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("amount_cents", sa.Integer, nullable=False),
        sa.Column("lang", sa.String(8), nullable=False, server_default="en"),
        sa.Column("stripe_session_id", sa.String(255), unique=True),
        sa.Column("stripe_payment_intent_id", sa.String(255)),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("confirmed_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("quantity BETWEEN 1 AND 10", name="ck_registrations_quantity"),
        sa.CheckConstraint(
            "status IN ('pending','confirmed','cancelled','expired')", name="ck_registrations_status"
        ),
    )
    op.create_index("ix_registrations_event_id", "registrations", ["event_id"])
    op.create_index("ix_registrations_status", "registrations", ["status"])
    op.create_index(
        "ix_registrations_stripe_payment_intent_id", "registrations", ["stripe_payment_intent_id"]
    )


def downgrade() -> None:
    op.drop_table("registrations")
    op.drop_table("events")
    op.drop_table("admin_users")
```

- [ ] **Step 6: Minimal app with health endpoint**

`backend/app/main.py`:
```python
from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="Matami Möttönen API")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
```

- [ ] **Step 7: Test harness**

`backend/tests/conftest.py`:
```python
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
```

`backend/tests/test_health.py`:
```python
from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
```

`backend/tests/test_schema.py`:
```python
from sqlalchemy import inspect
from sqlalchemy.orm import Session


def test_migration_creates_tables(db: Session) -> None:
    names = set(inspect(db.get_bind()).get_table_names())
    assert {"admin_users", "events", "registrations"} <= names
```

- [ ] **Step 8: Run**

Run: `cd backend && source .venv/bin/activate && alembic upgrade head && python -m pytest -q && ruff check . && ruff format .`
Expected: 2 passed; ruff clean (run `ruff format .` to fix formatting once).

- [ ] **Step 9: Commit**

```bash
git add backend && git commit -m "feat(backend): scaffold FastAPI app, models, initial migration, test harness

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 3: Domain logic — capacity, registration state machine, slugs

**Files:**
- Create: `backend/app/domain/__init__.py`, `capacity.py`, `registration_state.py`, `slug.py`
- Test: `backend/tests/test_domain.py`

**Interfaces:**
- Produces:
  - `capacity.Hold(quantity: int, status: str, expires_at: datetime)` (frozen dataclass)
  - `capacity.seats_taken(holds: Iterable[Hold], now: datetime) -> int`
  - `capacity.seats_left(capacity: int, holds, now) -> int`
  - `registration_state.transition(current: str, trigger: str) -> str | None` with triggers `"paid" | "expired" | "cancelled" | "refunded"`
  - `slug.slugify(text: str) -> str`, `slug.make_slug(title: str, suffix: str | None = None) -> str` (4-char lowercase base32 suffix by default)

- [ ] **Step 1: Failing tests**

`backend/tests/test_domain.py`:
```python
from datetime import UTC, datetime, timedelta

from app.domain.capacity import Hold, seats_left, seats_taken
from app.domain.registration_state import transition
from app.domain.slug import make_slug, slugify

NOW = datetime(2026, 9, 23, 12, 0, tzinfo=UTC)
LATER = NOW + timedelta(minutes=10)
EARLIER = NOW - timedelta(minutes=1)


def test_confirmed_always_counts_even_if_expires_at_passed() -> None:
    assert seats_taken([Hold(2, "confirmed", EARLIER)], NOW) == 2


def test_pending_counts_only_until_expiry() -> None:
    assert seats_taken([Hold(1, "pending", LATER)], NOW) == 1
    assert seats_taken([Hold(1, "pending", EARLIER)], NOW) == 0
    assert seats_taken([Hold(1, "pending", NOW)], NOW) == 0


def test_cancelled_and_expired_never_count() -> None:
    assert seats_taken([Hold(3, "cancelled", LATER), Hold(3, "expired", LATER)], NOW) == 0


def test_seats_left_never_negative() -> None:
    assert seats_left(2, [Hold(5, "confirmed", LATER)], NOW) == 0
    assert seats_left(10, [Hold(3, "confirmed", LATER), Hold(2, "pending", LATER)], NOW) == 5


def test_transitions() -> None:
    assert transition("pending", "paid") == "confirmed"
    assert transition("pending", "expired") == "expired"
    assert transition("pending", "cancelled") == "expired"
    assert transition("confirmed", "refunded") == "cancelled"
    assert transition("confirmed", "paid") is None
    assert transition("expired", "paid") is None
    assert transition("cancelled", "refunded") is None
    assert transition("pending", "refunded") is None


def test_slugify_handles_finnish() -> None:
    assert slugify("Äänimalja-ilta: Syksy!") == "aanimalja-ilta-syksy"
    assert slugify("   ") == "event"


def test_make_slug_appends_suffix() -> None:
    assert make_slug("Sound Bowl", "ab3k") == "sound-bowl-ab3k"
    s = make_slug("Sound Bowl")
    assert s.startswith("sound-bowl-") and len(s) == len("sound-bowl-") + 4
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_domain.py -q`
Expected: ImportError (module not found).

- [ ] **Step 3: Implement**

`backend/app/domain/__init__.py`: empty.

`backend/app/domain/capacity.py`:
```python
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Hold:
    quantity: int
    status: str
    expires_at: datetime


def seats_taken(holds: Iterable[Hold], now: datetime) -> int:
    total = 0
    for h in holds:
        if h.status == "confirmed":
            total += h.quantity
        elif h.status == "pending" and h.expires_at > now:
            total += h.quantity
    return total


def seats_left(capacity: int, holds: Iterable[Hold], now: datetime) -> int:
    return max(0, capacity - seats_taken(holds, now))
```

`backend/app/domain/registration_state.py`:
```python
PENDING = "pending"
CONFIRMED = "confirmed"
CANCELLED = "cancelled"
EXPIRED = "expired"

_TRANSITIONS: dict[tuple[str, str], str] = {
    (PENDING, "paid"): CONFIRMED,
    (PENDING, "expired"): EXPIRED,
    (PENDING, "cancelled"): EXPIRED,
    (CONFIRMED, "refunded"): CANCELLED,
}


def transition(current: str, trigger: str) -> str | None:
    """Next status for `trigger`, or None when the trigger does not apply (idempotent no-op)."""
    return _TRANSITIONS.get((current, trigger))
```

`backend/app/domain/slug.py`:
```python
import re
import secrets
import unicodedata

_ALPHABET = "abcdefghijklmnopqrstuvwxyz234567"


def slugify(text: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    return s[:100] or "event"


def make_slug(title: str, suffix: str | None = None) -> str:
    if suffix is None:
        suffix = "".join(secrets.choice(_ALPHABET) for _ in range(4))
    return f"{slugify(title)}-{suffix}"
```

- [ ] **Step 4: Run**

Run: `python -m pytest tests/test_domain.py -q && ruff check . && ruff format .`
Expected: 7 passed.

- [ ] **Step 5: Commit**

```bash
git add backend && git commit -m "feat(backend): capacity, registration state machine and slug domain logic

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 4: Admin auth — password hashing, signed session cookie, login/logout/me, rate limit, owner seeding

**Files:**
- Create: `backend/app/security.py`, `backend/app/services/__init__.py`, `backend/app/services/auth.py`, `backend/app/api/__init__.py`, `backend/app/api/deps.py`, `backend/app/api/rate_limit.py`, `backend/app/api/auth.py`, `backend/app/schemas.py`
- Modify: `backend/app/main.py` (lifespan seeds owner, mounts router)
- Test: `backend/tests/test_auth.py`

**Interfaces:**
- Produces:
  - `security.hash_password(p) -> str`, `security.verify_password(p, h) -> bool`, `security.sign_session(user_id: int) -> str`, `security.read_session(token: str) -> int | None`
  - `services.auth.ensure_owner(db) -> None` (creates admin from settings when table empty)
  - `services.auth.authenticate(db, email, password) -> AdminUser | None`
  - `api.deps.require_admin(request, db) -> AdminUser` FastAPI dependency (401 otherwise); `SESSION_COOKIE = "mm_session"`
  - `api.rate_limit.SlidingWindowLimiter(limit, window_seconds).hit(key) -> bool`
  - Routes: `POST /api/auth/login {email,password}` → 204 + cookie / 401 / 429; `POST /api/auth/logout` → 204; `GET /api/auth/me` → `{email}`.
  - All routers are mounted under `/api`.

- [ ] **Step 1: Failing tests**

`backend/tests/test_auth.py`:
```python
import pytest
from fastapi.testclient import TestClient

from app.api import auth as auth_module
from app.api.rate_limit import SlidingWindowLimiter

LOGIN = {"email": "owner@test.local", "password": "owner-pass"}


@pytest.fixture(autouse=True)
def _fresh_limiter() -> None:
    # The limiter is module-level and TestClient's IP is the same for every test.
    auth_module._limiter = SlidingWindowLimiter(5, 300)


def test_me_requires_login(client: TestClient) -> None:
    assert client.get("/api/auth/me").status_code == 401


def test_login_sets_cookie_and_me_works(client: TestClient) -> None:
    r = client.post("/api/auth/login", json=LOGIN)
    assert r.status_code == 204
    assert "mm_session" in r.cookies
    assert client.get("/api/auth/me").json() == {"email": "owner@test.local"}


def test_wrong_password_401(client: TestClient) -> None:
    r = client.post("/api/auth/login", json={**LOGIN, "password": "nope"})
    assert r.status_code == 401


def test_logout_clears_session(client: TestClient) -> None:
    client.post("/api/auth/login", json=LOGIN)
    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/auth/me").status_code == 401


def test_login_rate_limited(client: TestClient) -> None:
    for _ in range(5):
        client.post("/api/auth/login", json={**LOGIN, "password": "nope"})
    assert client.post("/api/auth/login", json=LOGIN).status_code == 429


def test_tampered_cookie_rejected(client: TestClient) -> None:
    client.cookies.set("mm_session", "garbage.value")
    assert client.get("/api/auth/me").status_code == 401
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_auth.py -q`
Expected: 404s (routes missing) → failures.

- [ ] **Step 3: Implement**

`backend/app/security.py`:
```python
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from pwdlib import PasswordHash

from app.config import settings

_hasher = PasswordHash.recommended()  # Argon2id
_DUMMY_HASH = _hasher.hash("dummy-for-constant-time")
_serializer = URLSafeTimedSerializer(settings.secret_key, salt="mm-session")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    ok = _hasher.verify(password, password_hash or _DUMMY_HASH)
    return ok and password_hash is not None


def sign_session(user_id: int) -> str:
    return _serializer.dumps({"uid": user_id})


def read_session(token: str) -> int | None:
    try:
        data = _serializer.loads(token, max_age=settings.session_ttl_hours * 3600)
    except (BadSignature, SignatureExpired):
        return None
    uid = data.get("uid") if isinstance(data, dict) else None
    return uid if isinstance(uid, int) else None
```

`backend/app/services/__init__.py`: empty.

`backend/app/services/auth.py`:
```python
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import AdminUser
from app.security import hash_password, verify_password


def ensure_owner(db: Session) -> None:
    if db.scalar(select(AdminUser.id).limit(1)) is None:
        db.add(
            AdminUser(
                email=settings.admin_email.strip().lower(),
                password_hash=hash_password(settings.admin_password),
            )
        )
        db.commit()


def authenticate(db: Session, email: str, password: str) -> AdminUser | None:
    user = db.scalar(select(AdminUser).where(AdminUser.email == email.strip().lower()))
    if verify_password(password, user.password_hash if user else None):
        return user
    return None
```

`backend/app/api/__init__.py`: empty.

`backend/app/api/rate_limit.py`:
```python
import threading
import time
from collections import defaultdict, deque


class SlidingWindowLimiter:
    def __init__(self, limit: int, window_seconds: int) -> None:
        self.limit = limit
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, key: str) -> bool:
        """Record a hit; return True if still within the limit."""
        now = time.monotonic()
        with self._lock:
            q = self._hits[key]
            while q and q[0] <= now - self.window:
                q.popleft()
            if len(q) >= self.limit:
                return False
            q.append(now)
            return True
```

`backend/app/api/deps.py`:
```python
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import AdminUser
from app.security import read_session

SESSION_COOKIE = "mm_session"


def require_admin(request: Request, db: Session = Depends(get_db)) -> AdminUser:
    token = request.cookies.get(SESSION_COOKIE)
    uid = read_session(token) if token else None
    user = db.get(AdminUser, uid) if uid is not None else None
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user
```

`backend/app/schemas.py` (auth part; later tasks append):
```python
from pydantic import BaseModel, EmailStr


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class MeOut(BaseModel):
    email: str
```

`backend/app/api/auth.py`:
```python
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.api.deps import SESSION_COOKIE, require_admin
from app.api.rate_limit import SlidingWindowLimiter
from app.config import settings
from app.db import get_db
from app.models import AdminUser
from app.schemas import LoginIn, MeOut
from app.security import sign_session
from app.services.auth import authenticate

router = APIRouter(prefix="/auth", tags=["auth"])
_limiter = SlidingWindowLimiter(settings.login_rate_limit, 300)


@router.post("/login", status_code=204)
def login(body: LoginIn, request: Request, response: Response, db: Session = Depends(get_db)) -> None:
    ip = request.client.host if request.client else "unknown"
    if not _limiter.hit(ip):
        raise HTTPException(status_code=429, detail="Too many attempts")
    user = authenticate(db, body.email, body.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    response.set_cookie(
        SESSION_COOKIE,
        sign_session(user.id),
        max_age=settings.session_ttl_hours * 3600,
        httponly=True,
        samesite="lax",
        secure=settings.env == "production",
        path="/",
    )


@router.post("/logout", status_code=204)
def logout(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/")


@router.get("/me", response_model=MeOut)
def me(user: AdminUser = Depends(require_admin)) -> MeOut:
    return MeOut(email=user.email)
```

`backend/app/main.py`:
```python
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from app.api import auth
from app.db import SessionLocal
from app.services.auth import ensure_owner


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    with SessionLocal() as db:
        ensure_owner(db)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Matami Möttönen API", lifespan=lifespan)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    api = APIRouter(prefix="/api")
    api.include_router(auth.router)
    app.include_router(api)
    return app


app = create_app()
```

- [ ] **Step 4: Run**

Run: `python -m pytest -q && ruff check . && ruff format .`
Expected: all pass (health, schema, domain, 6 auth).


- [ ] **Step 5: Commit**

```bash
git add backend && git commit -m "feat(backend): admin auth with Argon2 + signed session cookie and login rate limit

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 5: Admin events CRUD

**Files:**
- Create: `backend/app/repositories/__init__.py`, `backend/app/repositories/events.py`, `backend/app/api/admin_events.py`, `backend/tests/factories.py`
- Modify: `backend/app/schemas.py` (append), `backend/app/main.py` (mount router)
- Test: `backend/tests/test_admin_events.py`

**Interfaces:**
- Consumes: `require_admin`, `make_slug`, `Hold`, `seats_taken`.
- Produces:
  - `repositories.events.holds_for(db, event_id) -> list[Hold]` (pending + confirmed rows, any expiry)
  - `repositories.events.holds_by_event(db, event_ids: list[int]) -> dict[int, list[Hold]]`
  - `repositories.events.get_published_by_slug(db, slug) -> Event | None`
  - `repositories.events.lock_published_by_slug(db, slug) -> Event | None` (`SELECT … FOR UPDATE`)
  - `repositories.events.list_published_upcoming(db, now) -> list[Event]`
  - Schemas: `EventIn`, `AdminEventOut`, `EventOut` (public shape incl. `seats_left`, `sold_out`)
  - Routes: `GET/POST /api/admin/events`, `GET/PUT/DELETE /api/admin/events/{id}`
  - Test factory: `tests.factories.make_event(db, **overrides) -> Event` (committed; default published, tomorrow, 20 €, capacity 10) and `login(client)`.

- [ ] **Step 1: Failing tests**

`backend/tests/factories.py`:
```python
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.slug import make_slug
from app.models import Event

OWNER = {"email": "owner@test.local", "password": "owner-pass"}


def login(client: TestClient) -> None:
    assert client.post("/api/auth/login", json=OWNER).status_code == 204


def make_event(db: Session, **overrides: object) -> Event:
    title = str(overrides.pop("title_en", "Sound Bowl Evening"))
    values: dict[str, object] = dict(
        slug=make_slug(title),
        title_en=title,
        title_fi="Äänimaljailta",
        description_en="Bring a blanket.",
        starts_at=datetime.now(UTC) + timedelta(days=1),
        location="The moss",
        price_cents=2000,
        capacity=10,
        is_published=True,
    )
    values.update(overrides)
    ev = Event(**values)
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev
```

`backend/tests/test_admin_events.py`:
```python
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Event, Registration
from tests.factories import login, make_event

BODY = {
    "title_fi": "Tarot-ilta",
    "title_en": "Tarot Night",
    "description_fi": None,
    "description_en": "Cards.",
    "starts_at": "2026-10-10T16:00:00Z",
    "ends_at": None,
    "location": "Forest",
    "price_cents": 1500,
    "capacity": 8,
    "is_published": False,
}


def test_admin_routes_require_login(client: TestClient) -> None:
    assert client.get("/api/admin/events").status_code == 401
    assert client.post("/api/admin/events", json=BODY).status_code == 401


def test_create_list_update_delete(client: TestClient, db: Session) -> None:
    login(client)
    r = client.post("/api/admin/events", json=BODY)
    assert r.status_code == 201, r.text
    created = r.json()
    assert created["slug"].startswith("tarot-night-")
    assert created["confirmed_count"] == 0 and created["pending_count"] == 0

    r = client.get("/api/admin/events")
    assert [e["id"] for e in r.json()] == [created["id"]]

    r = client.put(f"/api/admin/events/{created['id']}", json={**BODY, "capacity": 12, "is_published": True})
    assert r.status_code == 200 and r.json()["capacity"] == 12 and r.json()["is_published"] is True
    assert r.json()["slug"] == created["slug"]  # slug is immutable

    assert client.delete(f"/api/admin/events/{created['id']}").status_code == 204
    assert client.get("/api/admin/events").json() == []


def test_create_requires_a_title(client: TestClient) -> None:
    login(client)
    r = client.post("/api/admin/events", json={**BODY, "title_fi": None, "title_en": None})
    assert r.status_code == 422


def test_counts_and_delete_guard(client: TestClient, db: Session) -> None:
    login(client)
    ev = make_event(db)
    now = datetime.now(UTC)
    db.add_all([
        Registration(event_id=ev.id, name="A", email="a@x.fi", quantity=2, status="confirmed",
                     amount_cents=4000, expires_at=now, confirmed_at=now),
        Registration(event_id=ev.id, name="B", email="b@x.fi", quantity=1, status="pending",
                     amount_cents=2000, expires_at=now + timedelta(minutes=30)),
        Registration(event_id=ev.id, name="C", email="c@x.fi", quantity=1, status="pending",
                     amount_cents=2000, expires_at=now - timedelta(minutes=1)),
    ])
    db.commit()
    row = client.get("/api/admin/events").json()[0]
    assert row["confirmed_count"] == 2 and row["pending_count"] == 1
    assert client.delete(f"/api/admin/events/{ev.id}").status_code == 409
    assert db.get(Event, ev.id) is not None
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_admin_events.py -q`
Expected: failures (404).

- [ ] **Step 3: Implement**

`backend/app/repositories/__init__.py`: empty.

`backend/app/repositories/events.py`:
```python
from collections import defaultdict
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.capacity import Hold
from app.models import Event, Registration

_COUNTED = ("pending", "confirmed")


def holds_by_event(db: Session, event_ids: list[int]) -> dict[int, list[Hold]]:
    out: dict[int, list[Hold]] = defaultdict(list)
    if not event_ids:
        return out
    rows = db.execute(
        select(
            Registration.event_id, Registration.quantity, Registration.status, Registration.expires_at
        ).where(Registration.event_id.in_(event_ids), Registration.status.in_(_COUNTED))
    )
    for event_id, quantity, status, expires_at in rows:
        out[event_id].append(Hold(quantity, status, expires_at))
    return out


def holds_for(db: Session, event_id: int) -> list[Hold]:
    return holds_by_event(db, [event_id]).get(event_id, [])


def get_published_by_slug(db: Session, slug: str) -> Event | None:
    return db.scalar(select(Event).where(Event.slug == slug, Event.is_published.is_(True)))


def lock_published_by_slug(db: Session, slug: str) -> Event | None:
    return db.scalar(
        select(Event).where(Event.slug == slug, Event.is_published.is_(True)).with_for_update()
    )


def list_published_upcoming(db: Session, now: datetime) -> list[Event]:
    return list(
        db.scalars(
            select(Event)
            .where(Event.is_published.is_(True), Event.starts_at >= now)
            .order_by(Event.starts_at)
        )
    )
```

Append to `backend/app/schemas.py`:
```python
from datetime import datetime  # noqa: E402  (place imports at top when editing)

from pydantic import Field, model_validator  # noqa: E402


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
```

(Merge the imports into the single import block at the top of `schemas.py`: `from datetime import datetime` and `from pydantic import BaseModel, EmailStr, Field, model_validator`.)

`backend/app/api/admin_events.py`:
```python
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db import get_db
from app.domain.capacity import Hold, seats_left, seats_taken
from app.domain.slug import make_slug
from app.models import Event, Registration
from app.repositories.events import holds_by_event
from app.schemas import AdminEventOut, EventIn

router = APIRouter(prefix="/admin/events", tags=["admin"], dependencies=[Depends(require_admin)])


def admin_out(ev: Event, holds: list[Hold], now: datetime) -> AdminEventOut:
    confirmed = sum(h.quantity for h in holds if h.status == "confirmed")
    pending = seats_taken(holds, now) - confirmed
    left = seats_left(ev.capacity, holds, now)
    return AdminEventOut(
        id=ev.id, slug=ev.slug, title_fi=ev.title_fi, title_en=ev.title_en,
        description_fi=ev.description_fi, description_en=ev.description_en,
        starts_at=ev.starts_at, ends_at=ev.ends_at, location=ev.location,
        price_cents=ev.price_cents, currency=ev.currency, capacity=ev.capacity,
        seats_left=left, sold_out=left == 0, is_published=ev.is_published,
        confirmed_count=confirmed, pending_count=pending,
    )


def _apply(ev: Event, body: EventIn) -> None:
    for field, value in body.model_dump().items():
        setattr(ev, field, value)


@router.get("", response_model=list[AdminEventOut])
def list_events(db: Session = Depends(get_db)) -> list[AdminEventOut]:
    now = datetime.now(UTC)
    events = list(db.scalars(select(Event).order_by(Event.starts_at.desc())))
    holds = holds_by_event(db, [e.id for e in events])
    return [admin_out(e, holds.get(e.id, []), now) for e in events]


@router.post("", response_model=AdminEventOut, status_code=201)
def create_event(body: EventIn, db: Session = Depends(get_db)) -> AdminEventOut:
    ev = Event(slug=make_slug(body.title_en or body.title_fi or "event"), currency="EUR")
    _apply(ev, body)
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return admin_out(ev, [], datetime.now(UTC))


def _get(db: Session, event_id: int) -> Event:
    ev = db.get(Event, event_id)
    if ev is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return ev


@router.get("/{event_id}", response_model=AdminEventOut)
def get_event(event_id: int, db: Session = Depends(get_db)) -> AdminEventOut:
    ev = _get(db, event_id)
    return admin_out(ev, holds_by_event(db, [ev.id]).get(ev.id, []), datetime.now(UTC))


@router.put("/{event_id}", response_model=AdminEventOut)
def update_event(event_id: int, body: EventIn, db: Session = Depends(get_db)) -> AdminEventOut:
    ev = _get(db, event_id)
    _apply(ev, body)
    db.commit()
    db.refresh(ev)
    return admin_out(ev, holds_by_event(db, [ev.id]).get(ev.id, []), datetime.now(UTC))


@router.delete("/{event_id}", status_code=204)
def delete_event(event_id: int, db: Session = Depends(get_db)) -> None:
    ev = _get(db, event_id)
    holds = holds_by_event(db, [ev.id]).get(ev.id, [])
    if any(h.status == "confirmed" for h in holds):
        raise HTTPException(status_code=409, detail="Event has confirmed registrations")
    # Non-confirmed registrations go first because of ondelete=RESTRICT.
    for reg in db.scalars(select(Registration).where(Registration.event_id == ev.id)):
        db.delete(reg)
    db.delete(ev)
    db.commit()
```

In `backend/app/main.py` add `from app.api import admin_events, auth` and `api.include_router(admin_events.router)`.

- [ ] **Step 4: Run**

Run: `python -m pytest -q && ruff check . && ruff format .`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add backend && git commit -m "feat(backend): admin events CRUD with seat counts and delete guard

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 6: Public events endpoints

**Files:**
- Create: `backend/app/api/events.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_public_events.py`

**Interfaces:**
- Consumes: `list_published_upcoming`, `get_published_by_slug`, `holds_by_event`, `holds_for`, `EventOut`.
- Produces: `GET /api/events` → `list[EventOut]`; `GET /api/events/{slug}` → `EventOut` / 404; helper `api.events.public_out(ev, holds, now) -> EventOut`.

- [ ] **Step 1: Failing tests**

`backend/tests/test_public_events.py`:
```python
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Registration
from tests.factories import make_event


def test_list_only_published_upcoming_sorted(client: TestClient, db: Session) -> None:
    now = datetime.now(UTC)
    later = make_event(db, title_en="Later", starts_at=now + timedelta(days=5))
    soon = make_event(db, title_en="Soon", starts_at=now + timedelta(days=1))
    make_event(db, title_en="Past", starts_at=now - timedelta(days=1))
    make_event(db, title_en="Draft", is_published=False)
    slugs = [e["slug"] for e in client.get("/api/events").json()]
    assert slugs == [soon.slug, later.slug]


def test_detail_has_seats_left_and_hides_drafts(client: TestClient, db: Session) -> None:
    ev = make_event(db, capacity=5)
    draft = make_event(db, is_published=False)
    now = datetime.now(UTC)
    db.add(Registration(event_id=ev.id, name="A", email="a@x.fi", quantity=2, status="confirmed",
                        amount_cents=4000, expires_at=now, confirmed_at=now))
    db.add(Registration(event_id=ev.id, name="B", email="b@x.fi", quantity=3, status="expired",
                        amount_cents=6000, expires_at=now))
    db.commit()
    body = client.get(f"/api/events/{ev.slug}").json()
    assert body["seats_left"] == 3 and body["sold_out"] is False
    assert "is_published" not in body
    assert client.get(f"/api/events/{draft.slug}").status_code == 404
    assert client.get("/api/events/nope").status_code == 404


def test_sold_out_flag(client: TestClient, db: Session) -> None:
    ev = make_event(db, capacity=1)
    now = datetime.now(UTC)
    db.add(Registration(event_id=ev.id, name="A", email="a@x.fi", quantity=1, status="pending",
                        amount_cents=2000, expires_at=now + timedelta(minutes=20)))
    db.commit()
    body = client.get(f"/api/events/{ev.slug}").json()
    assert body["seats_left"] == 0 and body["sold_out"] is True
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_public_events.py -q` → 404 failures.

- [ ] **Step 3: Implement**

`backend/app/api/events.py`:
```python
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.domain.capacity import Hold, seats_left
from app.models import Event
from app.repositories.events import get_published_by_slug, holds_by_event, list_published_upcoming
from app.schemas import EventOut

router = APIRouter(prefix="/events", tags=["events"])


def public_out(ev: Event, holds: list[Hold], now: datetime) -> EventOut:
    left = seats_left(ev.capacity, holds, now)
    return EventOut(
        id=ev.id, slug=ev.slug, title_fi=ev.title_fi, title_en=ev.title_en,
        description_fi=ev.description_fi, description_en=ev.description_en,
        starts_at=ev.starts_at, ends_at=ev.ends_at, location=ev.location,
        price_cents=ev.price_cents, currency=ev.currency, capacity=ev.capacity,
        seats_left=left, sold_out=left == 0,
    )


@router.get("", response_model=list[EventOut])
def list_events(db: Session = Depends(get_db)) -> list[EventOut]:
    now = datetime.now(UTC)
    events = list_published_upcoming(db, now)
    holds = holds_by_event(db, [e.id for e in events])
    return [public_out(e, holds.get(e.id, []), now) for e in events]


@router.get("/{slug}", response_model=EventOut)
def get_event(slug: str, db: Session = Depends(get_db)) -> EventOut:
    ev = get_published_by_slug(db, slug)
    if ev is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return public_out(ev, holds_by_event(db, [ev.id]).get(ev.id, []), datetime.now(UTC))
```

Mount in `main.py`: `api.include_router(events.router)`.

- [ ] **Step 4: Run** — `python -m pytest -q && ruff check . && ruff format .` → all pass.

- [ ] **Step 5: Commit**

```bash
git add backend && git commit -m "feat(backend): public event list and detail with seats left

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 7: Stripe gateway, mailer interfaces, and the checkout endpoint

**Files:**
- Create: `backend/app/services/stripe_gateway.py`, `backend/app/services/mailer.py`, `backend/app/services/mail_templates.py`, `backend/app/services/checkout.py`, `backend/app/api/checkout.py`
- Modify: `backend/app/schemas.py`, `backend/app/main.py`, `backend/tests/conftest.py`
- Test: `backend/tests/test_checkout.py`, `backend/tests/test_mail_templates.py`

**Interfaces:**
- Consumes: `lock_published_by_slug`, `holds_for`, `seats_left`, `settings`.
- Produces:
  - `stripe_gateway.CheckoutSession(id: str, url: str)` dataclass
  - `stripe_gateway.StripeGateway.create_checkout_session(*, registration_id: str, product_name: str, unit_amount: int, currency: str, quantity: int, customer_email: str, expires_at: datetime, success_url: str, cancel_url: str) -> CheckoutSession`; `.expire_session(session_id) -> None`; `.construct_event(payload: bytes, signature: str) -> dict`
  - `stripe_gateway.StripeError` (wraps SDK errors), `get_stripe_gateway()` dependency
  - `mailer.Mailer` protocol `send(to: str, subject: str, body: str) -> None`; `SmtpMailer`; `NullMailer` (logs only, used when `smtp_host` unset); `get_mailer()` dependency
  - `mail_templates.confirmation(lang: str, *, event_title: str, starts_at: datetime, location: str | None, quantity: int, amount_cents: int, contact_email: str) -> tuple[str, str]` (subject, body); `lang in {"fi","en"}`, anything else → en
  - `checkout.CheckoutError(code: str, seats_left: int | None = None)`; `checkout.start_checkout(db, gateway, *, slug, name, email, quantity, lang, now) -> CheckoutResult(registration_id: UUID, checkout_url: str | None, confirmed: bool)`
  - `checkout.confirmation_payload(reg: Registration, lang: str) -> tuple[str, str, str]` (to, subject, body)
  - Route: `POST /api/events/{slug}/checkout` body `{name, email, quantity, lang}` → 200 `{registration_id, checkout_url}` / 404 / 409 `{detail: {code:"sold_out", seats_left}}` / 422 / 502
  - Test doubles in `conftest.py`: `FakeStripeGateway` (records calls, returns `CheckoutSession("cs_test_<n>", "https://stripe.test/<n>")`, `fail_next: bool`), `RecordingMailer` (`sent: list[tuple[str,str,str]]`, `fail_times: int`); fixtures `stripe_fake`, `mailer_fake`; `client` overrides both dependencies.

- [ ] **Step 1: Failing tests**

`backend/tests/test_mail_templates.py`:
```python
from datetime import UTC, datetime

from app.services.mail_templates import confirmation

KW = dict(event_title="Sound Bowl Evening", starts_at=datetime(2026, 10, 10, 15, 0, tzinfo=UTC),
          location="The moss", quantity=2, amount_cents=4000, contact_email="m@x.fi")


def test_english_body_has_helsinki_time_and_amount() -> None:
    subject, body = confirmation("en", **KW)
    assert "Sound Bowl Evening" in subject
    assert "10.10.2026 18:00" in body  # UTC+3 in October (EEST)
    assert "2 seats" in body and "40.00 €" in body and "m@x.fi" in body


def test_finnish_and_fallback() -> None:
    subject_fi, body_fi = confirmation("fi", **KW)
    assert "Vahvistus" in subject_fi and "2 paikkaa" in body_fi
    assert confirmation("de", **KW) == confirmation("en", **KW)
    assert confirmation("futhark", **KW) == confirmation("en", **KW)
```

`backend/tests/test_checkout.py`:
```python
import threading
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Registration
from tests.conftest import FakeStripeGateway, RecordingMailer
from tests.factories import make_event

FORM = {"name": "Aino", "email": "aino@example.fi", "quantity": 2, "lang": "fi"}


def test_checkout_creates_pending_hold_and_stripe_session(
    client: TestClient, db: Session, stripe_fake: FakeStripeGateway
) -> None:
    ev = make_event(db, price_cents=2500, capacity=5)
    r = client.post(f"/api/events/{ev.slug}/checkout", json=FORM)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["checkout_url"] == "https://stripe.test/1"
    reg = db.scalar(select(Registration))
    assert reg is not None and str(reg.id) == body["registration_id"]
    assert reg.status == "pending" and reg.quantity == 2 and reg.amount_cents == 5000
    assert reg.stripe_session_id == "cs_test_1"
    assert timedelta(minutes=30) < reg.expires_at - datetime.now(UTC) <= timedelta(minutes=31)
    call = stripe_fake.calls[0]
    assert call["quantity"] == 2 and call["unit_amount"] == 2500 and call["currency"] == "eur"
    assert call["product_name"] == "Äänimaljailta"  # lang=fi picks the Finnish title
    assert call["success_url"] == f"http://test.local/events/thanks?reg={reg.id}"
    assert call["cancel_url"] == f"http://test.local/events/{ev.slug}?cancelled={reg.id}"
    assert call["customer_email"] == "aino@example.fi"
    assert client.get(f"/api/events/{ev.slug}").json()["seats_left"] == 3


def test_sold_out_returns_409_with_seats_left(client: TestClient, db: Session) -> None:
    ev = make_event(db, capacity=3)
    assert client.post(f"/api/events/{ev.slug}/checkout", json={**FORM, "quantity": 2}).status_code == 200
    r = client.post(f"/api/events/{ev.slug}/checkout", json={**FORM, "quantity": 2})
    assert r.status_code == 409
    assert r.json()["detail"] == {"code": "sold_out", "seats_left": 1}


def test_validation(client: TestClient, db: Session) -> None:
    ev = make_event(db)
    assert client.post(f"/api/events/{ev.slug}/checkout", json={**FORM, "quantity": 0}).status_code == 422
    assert client.post(f"/api/events/{ev.slug}/checkout", json={**FORM, "quantity": 11}).status_code == 422
    assert client.post(f"/api/events/{ev.slug}/checkout", json={**FORM, "email": "x"}).status_code == 422
    assert client.post(f"/api/events/{ev.slug}/checkout", json={**FORM, "name": ""}).status_code == 422
    assert client.post("/api/events/none/checkout", json=FORM).status_code == 404
    draft = make_event(db, is_published=False)
    assert client.post(f"/api/events/{draft.slug}/checkout", json=FORM).status_code == 404


def test_free_event_confirms_immediately_and_emails(
    client: TestClient, db: Session, stripe_fake: FakeStripeGateway, mailer_fake: RecordingMailer
) -> None:
    ev = make_event(db, price_cents=0)
    r = client.post(f"/api/events/{ev.slug}/checkout", json=FORM)
    assert r.status_code == 200 and r.json()["checkout_url"] is None
    reg = db.scalar(select(Registration))
    assert reg.status == "confirmed" and reg.confirmed_at is not None and reg.amount_cents == 0
    assert stripe_fake.calls == []
    assert len(mailer_fake.sent) == 1 and mailer_fake.sent[0][0] == "aino@example.fi"


def test_stripe_failure_rolls_back_hold(
    client: TestClient, db: Session, stripe_fake: FakeStripeGateway
) -> None:
    ev = make_event(db)
    stripe_fake.fail_next = True
    r = client.post(f"/api/events/{ev.slug}/checkout", json=FORM)
    assert r.status_code == 502
    assert db.scalar(select(Registration)) is None
    assert client.get(f"/api/events/{ev.slug}").json()["seats_left"] == 10


def test_last_seat_race_only_one_wins(client: TestClient, db: Session) -> None:
    ev = make_event(db, capacity=1)
    results: list[int] = []

    def go() -> None:
        # One TestClient per thread: a single client is not safe to share across threads.
        with TestClient(client.app) as c:
            results.append(c.post(f"/api/events/{ev.slug}/checkout", json={**FORM, "quantity": 1}).status_code)

    threads = [threading.Thread(target=go) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(results) == [200, 409, 409, 409]
    assert db.scalar(select(Registration.quantity).where(Registration.status == "pending")) == 1
```

- [ ] **Step 2: Test doubles in conftest**

Append to `backend/tests/conftest.py` (imports at top of the module, below the `os.environ` block):
```python
import threading
from dataclasses import dataclass, field
from datetime import datetime

from app.services.mailer import Mailer, get_mailer
from app.services.stripe_gateway import CheckoutSession, StripeError, StripeGateway, get_stripe_gateway


class FakeStripeGateway(StripeGateway):
    def __init__(self) -> None:
        super().__init__(secret_key="sk_test_fake", webhook_secret=settings.stripe_webhook_secret)
        self.calls: list[dict[str, object]] = []
        self.expired: list[str] = []
        self.fail_next = False
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
```

And replace the `client` fixture:
```python
@pytest.fixture()
def client(db: Session, stripe_fake: FakeStripeGateway, mailer_fake: RecordingMailer) -> Iterator[TestClient]:
    from app.main import app

    app.dependency_overrides[get_stripe_gateway] = lambda: stripe_fake
    app.dependency_overrides[get_mailer] = lambda: mailer_fake
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

- [ ] **Step 3: Run to verify failure** — `python -m pytest tests/test_checkout.py tests/test_mail_templates.py -q` → ImportErrors.

- [ ] **Step 4: Implement services**

`backend/app/services/stripe_gateway.py`:
```python
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
            s = self._client.checkout.sessions.create(
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
            self._client.checkout.sessions.expire(session_id)
        except stripe.StripeError as e:
            raise StripeError(str(e)) from e

    def construct_event(self, payload: bytes, signature: str) -> dict[str, Any]:
        """Verify the webhook signature and return the event as a plain dict. Raises StripeError."""
        try:
            event = stripe.Webhook.construct_event(payload, signature, self._webhook_secret)
        except (ValueError, stripe.SignatureVerificationError) as e:
            raise StripeError(str(e)) from e
        return event.to_dict_recursive()


_gateway: StripeGateway | None = None


def get_stripe_gateway() -> StripeGateway:
    global _gateway
    if _gateway is None:
        _gateway = StripeGateway(settings.stripe_secret_key, settings.stripe_webhook_secret)
    return _gateway
```

Check the installed `stripe` version supports `StripeClient` (v8+). If `to_dict_recursive` is unavailable, use `dict(event)` after `json.loads(payload)`; the handler only needs `type`, `data.object.id`, `data.object.payment_intent`, `data.object.client_reference_id`, `data.object.metadata`.

`backend/app/services/mailer.py`:
```python
import logging
import smtplib
from email.message import EmailMessage
from typing import Protocol

from app.config import settings

log = logging.getLogger(__name__)


class Mailer(Protocol):
    def send(self, to: str, subject: str, body: str) -> None: ...


class SmtpMailer:
    def __init__(self, host: str, port: int, user: str | None, password: str | None, sender: str) -> None:
        self.host, self.port, self.user, self.password, self.sender = host, port, user, password, sender

    def send(self, to: str, subject: str, body: str) -> None:
        msg = EmailMessage()
        msg["From"], msg["To"], msg["Subject"] = self.sender, to, subject
        msg.set_content(body)
        with smtplib.SMTP(self.host, self.port, timeout=20) as smtp:
            smtp.ehlo()
            if self.port != 25:
                smtp.starttls()
            if self.user and self.password:
                smtp.login(self.user, self.password)
            smtp.send_message(msg)


class NullMailer:
    def send(self, to: str, subject: str, body: str) -> None:
        log.warning("SMTP not configured; would send to %s: %s", to, subject)


_mailer: Mailer | None = None


def get_mailer() -> Mailer:
    global _mailer
    if _mailer is None:
        if settings.smtp_host:
            _mailer = SmtpMailer(
                settings.smtp_host, settings.smtp_port, settings.smtp_user,
                settings.smtp_password, settings.smtp_from,
            )
        else:
            _mailer = NullMailer()
    return _mailer
```

`backend/app/services/mail_templates.py`:
```python
from datetime import datetime
from zoneinfo import ZoneInfo

HELSINKI = ZoneInfo("Europe/Helsinki")


def _fmt_dt(dt: datetime) -> str:
    return dt.astimezone(HELSINKI).strftime("%d.%m.%Y %H:%M")


def _fmt_eur(cents: int) -> str:
    return f"{cents / 100:.2f} €"


def confirmation(
    lang: str,
    *,
    event_title: str,
    starts_at: datetime,
    location: str | None,
    quantity: int,
    amount_cents: int,
    contact_email: str,
) -> tuple[str, str]:
    when = _fmt_dt(starts_at)
    where = location or "-"
    if lang == "fi":
        subject = f"Vahvistus: {event_title}"
        body = (
            f"Kiitos ilmoittautumisestasi!\n\n"
            f"Tapahtuma: {event_title}\n"
            f"Aika: {when}\n"
            f"Paikka: {where}\n"
            f"Paikkoja: {quantity} paikkaa\n"
            f"Maksettu: {_fmt_eur(amount_cents)}\n\n"
            f"Kysymyksiä? Vastaa tähän viestiin tai kirjoita osoitteeseen {contact_email}.\n\n"
            f"Nähdään sammalessa,\nMatami Möttönen"
        )
    else:
        subject = f"Confirmation: {event_title}"
        body = (
            f"Thank you for signing up!\n\n"
            f"Event: {event_title}\n"
            f"When: {when}\n"
            f"Where: {where}\n"
            f"Seats: {quantity} seats\n"
            f"Paid: {_fmt_eur(amount_cents)}\n\n"
            f"Questions? Reply to this message or write to {contact_email}.\n\n"
            f"See you in the moss,\nMatami Möttönen"
        )
    return subject, body
```

`backend/app/services/checkout.py`:
```python
import logging
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.config import settings
from app.domain.capacity import seats_left
from app.models import Event, Registration
from app.repositories.events import holds_for, lock_published_by_slug
from app.services.mail_templates import confirmation
from app.services.mailer import Mailer
from app.services.stripe_gateway import StripeError, StripeGateway

log = logging.getLogger(__name__)


class CheckoutError(Exception):
    def __init__(self, code: str, seats_left: int | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.seats_left = seats_left


@dataclass(frozen=True)
class CheckoutResult:
    registration_id: uuid.UUID
    checkout_url: str | None
    confirmed: bool


def title_for(ev: Event, lang: str) -> str:
    if lang == "fi":
        return ev.title_fi or ev.title_en or "Event"
    return ev.title_en or ev.title_fi or "Event"


def start_checkout(
    db: Session,
    gateway: StripeGateway,
    *,
    slug: str,
    name: str,
    email: str,
    quantity: int,
    lang: str,
    now: datetime | None = None,
) -> CheckoutResult:
    now = now or datetime.now(UTC)
    with db.begin():
        ev = lock_published_by_slug(db, slug)
        if ev is None:
            raise CheckoutError("not_found")
        left = seats_left(ev.capacity, holds_for(db, ev.id), now)
        if quantity > left:
            raise CheckoutError("sold_out", seats_left=left)
        reg = Registration(
            id=uuid.uuid4(),
            event_id=ev.id,
            name=name,
            email=email,
            quantity=quantity,
            amount_cents=ev.price_cents * quantity,
            lang=lang,
            expires_at=now + timedelta(minutes=settings.hold_minutes),
        )
        if ev.price_cents == 0:
            reg.status = "confirmed"
            reg.confirmed_at = now
            db.add(reg)
            return CheckoutResult(reg.id, None, confirmed=True)
        db.add(reg)
        db.flush()
        try:
            session = gateway.create_checkout_session(
                registration_id=str(reg.id),
                product_name=title_for(ev, lang),
                unit_amount=ev.price_cents,
                currency=ev.currency.lower(),
                quantity=quantity,
                customer_email=email,
                expires_at=reg.expires_at,
                success_url=f"{settings.public_base_url}/events/thanks?reg={reg.id}",
                cancel_url=f"{settings.public_base_url}/events/{ev.slug}?cancelled={reg.id}",
            )
        except StripeError as e:
            log.error("Stripe checkout failed for registration %s: %s", reg.id, e)
            raise CheckoutError("payment_unavailable") from e
        reg.stripe_session_id = session.id
        return CheckoutResult(reg.id, session.url, confirmed=False)


def confirmation_payload(reg: Registration, lang: str) -> tuple[str, str, str]:
    ev = reg.event
    subject, body = confirmation(
        lang,
        event_title=title_for(ev, lang),
        starts_at=ev.starts_at,
        location=ev.location,
        quantity=reg.quantity,
        amount_cents=reg.amount_cents,
        contact_email=settings.contact_email,
    )
    return reg.email, subject, body


def send_with_retry(mailer: Mailer, to: str, subject: str, body: str, attempts: int = 3) -> bool:
    for i in range(attempts):
        try:
            mailer.send(to, subject, body)
            return True
        except Exception as e:  # noqa: BLE001 — any transport error is retryable
            log.warning("Email to %s failed (attempt %d/%d): %s", to, i + 1, attempts, e)
            if i < attempts - 1:
                time.sleep(2**i)
    log.error("Giving up sending email to %s: %s", to, subject)
    return False
```

`with db.begin():` commits on normal exit (including the free-event `return`) and rolls back when `CheckoutError` propagates out of it. It requires a session with no transaction begun yet, which is what the endpoint's fresh `get_db` session is; tests call the endpoint, not `start_checkout` directly.

Append to `backend/app/schemas.py`:
```python
class CheckoutIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    quantity: int = Field(ge=1, le=10)
    lang: str = Field(default="en", pattern="^(fi|en|de|futhark)$")


class CheckoutOut(BaseModel):
    registration_id: str
    checkout_url: str | None
```

`backend/app/api/checkout.py`:
```python
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
            db, gateway, slug=slug, name=body.name.strip(), email=body.email,
            quantity=body.quantity, lang=body.lang,
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
    return CheckoutOut(registration_id=str(result.registration_id), checkout_url=result.checkout_url)
```

Mount in `main.py`: `api.include_router(checkout.router)`.

- [ ] **Step 5: Run** — `python -m pytest -q && ruff check . && ruff format .` → all pass, including the race test.

- [ ] **Step 6: Commit**

```bash
git add backend && git commit -m "feat(backend): checkout endpoint with seat holds, Stripe gateway and mailer

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 8: Stripe webhook, registration status, and cancel endpoint

**Files:**
- Create: `backend/app/services/webhook.py`, `backend/app/api/stripe_webhook.py`, `backend/app/api/registrations.py`, `backend/app/repositories/registrations.py`
- Modify: `backend/app/schemas.py`, `backend/app/main.py`
- Test: `backend/tests/test_webhook.py`, `backend/tests/test_registrations.py`

**Interfaces:**
- Consumes: `transition`, `StripeGateway.construct_event/expire_session`, `confirmation_payload`, `send_with_retry`.
- Produces:
  - `repositories.registrations.by_session_id(db, sid)`, `by_payment_intent(db, pi)`, `get(db, id: UUID)` → `Registration | None`
  - `services.webhook.handle_event(db, event: dict) -> Registration | None` — returns the registration that was **confirmed** (caller sends the email) or None; applies `transition` idempotently.
  - `services.webhook.cancel_pending(db, gateway, reg) -> bool` — expire Stripe session (errors logged, not raised) and mark `expired`.
  - Routes: `POST /api/stripe/webhook` (raw body, `Stripe-Signature` header) → 200 `{received: true}` / 400; `GET /api/registrations/{id}/status` → `{status, event_slug, quantity}` / 404; `POST /api/registrations/{id}/cancel` → 204 / 404 / 409.
  - Test helper `tests.stripe_sig.sign(payload: bytes, secret: str) -> str` producing a valid `t=…,v1=…` header.

- [ ] **Step 1: Failing tests**

`backend/tests/stripe_sig.py`:
```python
import hmac
import time
from hashlib import sha256


def sign(payload: bytes, secret: str, ts: int | None = None) -> str:
    ts = ts or int(time.time())
    mac = hmac.new(secret.encode(), f"{ts}.".encode() + payload, sha256).hexdigest()
    return f"t={ts},v1={mac}"
```

`backend/tests/test_webhook.py`:
```python
import json
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Registration
from tests.conftest import RecordingMailer
from tests.factories import make_event
from tests.stripe_sig import sign

SECRET = "whsec_test_secret"


def _reg(db: Session, status: str = "pending", **kw: object) -> Registration:
    ev = make_event(db)
    now = datetime.now(UTC)
    values: dict[str, object] = dict(
        event_id=ev.id, name="A", email="a@x.fi", quantity=2, status=status, amount_cents=4000,
        expires_at=now + timedelta(minutes=30), stripe_session_id="cs_1",
    )
    values.update(kw)
    reg = Registration(**values)
    db.add(reg)
    db.commit()
    db.refresh(reg)
    return reg


def _post(client: TestClient, event: dict, secret: str = SECRET):
    payload = json.dumps(event).encode()
    return client.post("/api/stripe/webhook", content=payload,
                       headers={"Stripe-Signature": sign(payload, secret), "Content-Type": "application/json"})


def _completed(reg: Registration) -> dict:
    return {"id": "evt_1", "type": "checkout.session.completed",
            "data": {"object": {"id": "cs_1", "payment_intent": "pi_1", "client_reference_id": str(reg.id),
                                "metadata": {"registration_id": str(reg.id)}}}}


def test_bad_signature_400(client: TestClient, db: Session) -> None:
    reg = _reg(db)
    assert _post(client, _completed(reg), secret="whsec_wrong").status_code == 400
    db.refresh(reg)
    assert reg.status == "pending"


def test_completed_confirms_and_emails(client: TestClient, db: Session, mailer_fake: RecordingMailer) -> None:
    reg = _reg(db)
    r = _post(client, _completed(reg))
    assert r.status_code == 200 and r.json() == {"received": True}
    db.refresh(reg)
    assert reg.status == "confirmed" and reg.stripe_payment_intent_id == "pi_1" and reg.confirmed_at
    assert len(mailer_fake.sent) == 1 and "Sound Bowl Evening" in mailer_fake.sent[0][1]


def test_completed_is_idempotent(client: TestClient, db: Session, mailer_fake: RecordingMailer) -> None:
    reg = _reg(db)
    _post(client, _completed(reg))
    _post(client, _completed(reg))
    assert len(mailer_fake.sent) == 1


def test_completed_found_via_metadata_when_session_unknown(client: TestClient, db: Session) -> None:
    reg = _reg(db, stripe_session_id=None)
    _post(client, _completed(reg))
    db.refresh(reg)
    assert reg.status == "confirmed"


def test_expired_releases_hold(client: TestClient, db: Session) -> None:
    reg = _reg(db)
    ev = {"id": "evt_2", "type": "checkout.session.expired", "data": {"object": {"id": "cs_1", "metadata": {}}}}
    assert _post(client, ev).status_code == 200
    db.refresh(reg)
    assert reg.status == "expired"


def test_expired_does_not_touch_confirmed(client: TestClient, db: Session) -> None:
    reg = _reg(db, status="confirmed")
    _post(client, {"id": "evt_3", "type": "checkout.session.expired", "data": {"object": {"id": "cs_1", "metadata": {}}}})
    db.refresh(reg)
    assert reg.status == "confirmed"


def test_refund_cancels(client: TestClient, db: Session) -> None:
    reg = _reg(db, status="confirmed", stripe_payment_intent_id="pi_1")
    ev = {"id": "evt_4", "type": "charge.refunded", "data": {"object": {"id": "ch_1", "payment_intent": "pi_1"}}}
    assert _post(client, ev).status_code == 200
    db.refresh(reg)
    assert reg.status == "cancelled"


def test_unknown_registration_and_unknown_type_are_acknowledged(client: TestClient, db: Session) -> None:
    ev = {"id": "evt_5", "type": "checkout.session.completed",
          "data": {"object": {"id": "cs_none", "payment_intent": "pi_x", "client_reference_id": "nope", "metadata": {}}}}
    assert _post(client, ev).status_code == 200
    assert _post(client, {"id": "evt_6", "type": "payment_intent.created", "data": {"object": {}}}).status_code == 200


def test_email_retries_then_succeeds(client: TestClient, db: Session, mailer_fake: RecordingMailer, monkeypatch) -> None:
    import app.services.checkout as co

    monkeypatch.setattr(co.time, "sleep", lambda _s: None)
    mailer_fake.fail_times = 2
    reg = _reg(db)
    _post(client, _completed(reg))
    assert len(mailer_fake.sent) == 1
```

`backend/tests/test_registrations.py`:
```python
import uuid
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Registration
from tests.conftest import FakeStripeGateway
from tests.factories import make_event


def _pending(db: Session) -> Registration:
    ev = make_event(db, capacity=2)
    reg = Registration(event_id=ev.id, name="A", email="a@x.fi", quantity=2, status="pending",
                       amount_cents=4000, expires_at=datetime.now(UTC) + timedelta(minutes=30),
                       stripe_session_id="cs_9")
    db.add(reg)
    db.commit()
    db.refresh(reg)
    return reg


def test_status(client: TestClient, db: Session) -> None:
    reg = _pending(db)
    r = client.get(f"/api/registrations/{reg.id}/status")
    assert r.status_code == 200
    assert r.json() == {"status": "pending", "event_slug": reg.event.slug, "quantity": 2}
    assert client.get(f"/api/registrations/{uuid.uuid4()}/status").status_code == 404
    assert client.get("/api/registrations/not-a-uuid/status").status_code == 404


def test_cancel_pending_frees_seats_and_expires_stripe(
    client: TestClient, db: Session, stripe_fake: FakeStripeGateway
) -> None:
    reg = _pending(db)
    slug = reg.event.slug
    assert client.get(f"/api/events/{slug}").json()["seats_left"] == 0
    assert client.post(f"/api/registrations/{reg.id}/cancel").status_code == 204
    assert stripe_fake.expired == ["cs_9"]
    db.refresh(reg)
    assert reg.status == "expired"
    assert client.get(f"/api/events/{slug}").json()["seats_left"] == 2
    assert client.post(f"/api/registrations/{reg.id}/cancel").status_code == 409
```

- [ ] **Step 2: Run to verify failure** — `python -m pytest tests/test_webhook.py tests/test_registrations.py -q` → failures.

- [ ] **Step 3: Implement**

`backend/app/repositories/registrations.py`:
```python
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Registration


def get(db: Session, reg_id: uuid.UUID) -> Registration | None:
    return db.get(Registration, reg_id)


def by_session_id(db: Session, session_id: str) -> Registration | None:
    return db.scalar(select(Registration).where(Registration.stripe_session_id == session_id))


def by_payment_intent(db: Session, payment_intent: str) -> Registration | None:
    return db.scalar(
        select(Registration).where(Registration.stripe_payment_intent_id == payment_intent)
    )
```

`backend/app/services/webhook.py`:
```python
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.domain.registration_state import transition
from app.models import Registration
from app.repositories import registrations as repo
from app.services.stripe_gateway import StripeError, StripeGateway

log = logging.getLogger(__name__)


def _find_by_session(db: Session, obj: dict[str, Any]) -> Registration | None:
    reg = repo.by_session_id(db, obj.get("id", "")) if obj.get("id") else None
    if reg is not None:
        return reg
    raw = (obj.get("metadata") or {}).get("registration_id") or obj.get("client_reference_id")
    try:
        return repo.get(db, uuid.UUID(str(raw))) if raw else None
    except ValueError:
        return None


def handle_event(db: Session, event: dict[str, Any]) -> Registration | None:
    """Apply a Stripe event. Returns the registration if it was just confirmed (email due)."""
    kind = event.get("type")
    obj: dict[str, Any] = event.get("data", {}).get("object", {}) or {}
    if kind == "checkout.session.completed":
        reg = _find_by_session(db, obj)
        if reg is None:
            log.warning("checkout.session.completed for unknown session %s", obj.get("id"))
            return None
        nxt = transition(reg.status, "paid")
        if nxt is None:
            return None
        reg.status = nxt
        reg.confirmed_at = datetime.now(UTC)
        reg.stripe_payment_intent_id = obj.get("payment_intent") or reg.stripe_payment_intent_id
        if not reg.stripe_session_id and obj.get("id"):
            reg.stripe_session_id = obj["id"]
        db.commit()
        db.refresh(reg)
        return reg
    if kind == "checkout.session.expired":
        reg = _find_by_session(db, obj)
        nxt = transition(reg.status, "expired") if reg else None
        if reg is not None and nxt is not None:
            reg.status = nxt
            db.commit()
        return None
    if kind == "charge.refunded":
        pi = obj.get("payment_intent")
        reg = repo.by_payment_intent(db, pi) if pi else None
        nxt = transition(reg.status, "refunded") if reg else None
        if reg is not None and nxt is not None:
            reg.status = nxt
            db.commit()
        return None
    return None


def cancel_pending(db: Session, gateway: StripeGateway, reg: Registration) -> bool:
    nxt = transition(reg.status, "cancelled")
    if nxt is None:
        return False
    if reg.stripe_session_id:
        try:
            gateway.expire_session(reg.stripe_session_id)
        except StripeError as e:
            log.warning("Could not expire Stripe session %s: %s", reg.stripe_session_id, e)
    reg.status = nxt
    db.commit()
    return True
```

Append to `backend/app/schemas.py`:
```python
class RegistrationStatusOut(BaseModel):
    status: str
    event_slug: str
    quantity: int
```

`backend/app/api/stripe_webhook.py`:
```python
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
```

`backend/app/api/registrations.py`:
```python
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
    return RegistrationStatusOut(status=reg.status, event_slug=reg.event.slug, quantity=reg.quantity)


@router.post("/{reg_id}/cancel", status_code=204)
def cancel(
    reg_id: str,
    db: Session = Depends(get_db),
    gateway: StripeGateway = Depends(get_stripe_gateway),
) -> None:
    reg = _load(db, reg_id)
    if not cancel_pending(db, gateway, reg):
        raise HTTPException(status_code=409, detail="Registration is not pending")
```

Mount both routers in `main.py`.

- [ ] **Step 4: Run** — `python -m pytest -q && ruff check . && ruff format .` → all pass.

- [ ] **Step 5: Commit**

```bash
git add backend && git commit -m "feat(backend): Stripe webhook state transitions, registration status and cancel

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 9: Hold sweep and admin attendee list + CSV

**Files:**
- Create: `backend/app/services/sweep.py`, `backend/app/api/admin_registrations.py`
- Modify: `backend/app/main.py` (background sweep loop), `backend/app/schemas.py`
- Test: `backend/tests/test_sweep.py`, `backend/tests/test_admin_registrations.py`

**Interfaces:**
- Produces:
  - `services.sweep.expire_stale_holds(db, now) -> int` (rows flipped `pending → expired`)
  - Lifespan task: every `settings.sweep_interval_seconds` (skipped when `0`) runs the sweep.
  - `GET /api/admin/events/{id}/registrations` → `list[AdminRegistrationOut]` (`id, name, email, quantity, status, amount_cents, created_at, confirmed_at`), newest first; `GET /api/admin/events/{id}/registrations.csv` → `text/csv` with header `name,email,quantity,status,amount_eur,created_at`.

- [ ] **Step 1: Failing tests**

`backend/tests/test_sweep.py`:
```python
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.models import Registration
from app.services.sweep import expire_stale_holds
from tests.factories import make_event


def test_sweep_expires_only_stale_pending(db: Session) -> None:
    ev = make_event(db)
    now = datetime.now(UTC)
    stale = Registration(event_id=ev.id, name="S", email="s@x.fi", quantity=1, status="pending",
                         amount_cents=2000, expires_at=now - timedelta(seconds=1))
    fresh = Registration(event_id=ev.id, name="F", email="f@x.fi", quantity=1, status="pending",
                         amount_cents=2000, expires_at=now + timedelta(minutes=5))
    done = Registration(event_id=ev.id, name="D", email="d@x.fi", quantity=1, status="confirmed",
                        amount_cents=2000, expires_at=now - timedelta(hours=1), confirmed_at=now)
    db.add_all([stale, fresh, done])
    db.commit()
    assert expire_stale_holds(db, now) == 1
    for r in (stale, fresh, done):
        db.refresh(r)
    assert (stale.status, fresh.status, done.status) == ("expired", "pending", "confirmed")
    assert expire_stale_holds(db, now) == 0
```

`backend/tests/test_admin_registrations.py`:
```python
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Registration
from tests.factories import login, make_event


def _seed(db: Session):
    ev = make_event(db)
    now = datetime.now(UTC)
    db.add_all([
        Registration(event_id=ev.id, name="Aino", email="a@x.fi", quantity=2, status="confirmed",
                     amount_cents=4000, expires_at=now, confirmed_at=now, created_at=now - timedelta(hours=1)),
        Registration(event_id=ev.id, name="Bo", email="b@x.fi", quantity=1, status="expired",
                     amount_cents=2000, expires_at=now, created_at=now),
    ])
    db.commit()
    return ev


def test_requires_login(client: TestClient, db: Session) -> None:
    ev = _seed(db)
    assert client.get(f"/api/admin/events/{ev.id}/registrations").status_code == 401


def test_list_newest_first(client: TestClient, db: Session) -> None:
    ev = _seed(db)
    login(client)
    rows = client.get(f"/api/admin/events/{ev.id}/registrations").json()
    assert [r["name"] for r in rows] == ["Bo", "Aino"]
    assert rows[1] == {**rows[1], "email": "a@x.fi", "quantity": 2, "status": "confirmed", "amount_cents": 4000}
    assert client.get("/api/admin/events/999/registrations").status_code == 404


def test_csv(client: TestClient, db: Session) -> None:
    ev = _seed(db)
    login(client)
    r = client.get(f"/api/admin/events/{ev.id}/registrations.csv")
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/csv")
    lines = r.text.strip().splitlines()
    assert lines[0] == "name,email,quantity,status,amount_eur,created_at"
    assert lines[1].startswith("Bo,b@x.fi,1,expired,20.00,")
    assert lines[2].startswith("Aino,a@x.fi,2,confirmed,40.00,")
```

- [ ] **Step 2: Run to verify failure** — `python -m pytest tests/test_sweep.py tests/test_admin_registrations.py -q`.

- [ ] **Step 3: Implement**

`backend/app/services/sweep.py`:
```python
import logging
from datetime import UTC, datetime

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models import Registration

log = logging.getLogger(__name__)


def expire_stale_holds(db: Session, now: datetime | None = None) -> int:
    now = now or datetime.now(UTC)
    result = db.execute(
        update(Registration)
        .where(Registration.status == "pending", Registration.expires_at <= now)
        .values(status="expired")
    )
    db.commit()
    n = result.rowcount or 0
    if n:
        log.info("Expired %d stale holds", n)
    return n
```

Append to `backend/app/schemas.py`:
```python
class AdminRegistrationOut(BaseModel):
    id: str
    name: str
    email: str
    quantity: int
    status: str
    amount_cents: int
    created_at: datetime
    confirmed_at: datetime | None
```

`backend/app/api/admin_registrations.py`:
```python
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
            id=str(r.id), name=r.name, email=r.email, quantity=r.quantity, status=r.status,
            amount_cents=r.amount_cents, created_at=r.created_at, confirmed_at=r.confirmed_at,
        )
        for r in _rows(db, event_id)
    ]


@router.get("/{event_id}/registrations.csv")
def registrations_csv(event_id: int, db: Session = Depends(get_db)) -> Response:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["name", "email", "quantity", "status", "amount_eur", "created_at"])
    for r in _rows(db, event_id):
        w.writerow([r.name, r.email, r.quantity, r.status, f"{r.amount_cents / 100:.2f}", r.created_at.isoformat()])
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="event-{event_id}-registrations.csv"'},
    )
```

Route ordering: `admin_registrations.router` and `admin_events.router` share the prefix; FastAPI matches `/{event_id}/registrations.csv` before `/{event_id}` only if the more specific router is included **first**. Include `admin_registrations.router` before `admin_events.router` in `main.py`.

`backend/app/main.py` lifespan with sweep loop:
```python
import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from app.api import (
    admin_events, admin_registrations, auth, checkout, events, registrations, stripe_webhook,
)
from app.config import settings
from app.db import SessionLocal
from app.services.auth import ensure_owner
from app.services.sweep import expire_stale_holds

log = logging.getLogger(__name__)


async def _sweep_loop() -> None:
    while True:
        await asyncio.sleep(settings.sweep_interval_seconds)
        try:
            with SessionLocal() as db:
                await asyncio.to_thread(expire_stale_holds, db)
        except Exception:  # noqa: BLE001
            log.exception("sweep failed")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    with SessionLocal() as db:
        ensure_owner(db)
    task = asyncio.create_task(_sweep_loop()) if settings.sweep_interval_seconds > 0 else None
    try:
        yield
    finally:
        if task:
            task.cancel()


def create_app() -> FastAPI:
    app = FastAPI(title="Matami Möttönen API", lifespan=lifespan)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    api = APIRouter(prefix="/api")
    for r in (auth, events, checkout, registrations, stripe_webhook, admin_registrations, admin_events):
        api.include_router(r.router)
    app.include_router(api)
    return app


app = create_app()
```

- [ ] **Step 4: Run** — `python -m pytest -q && ruff check . && ruff format .` → all pass.

- [ ] **Step 5: Backend README**

`backend/README.md`:
```markdown
# Backend

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp ../.env.example .env        # edit APP_* values
alembic upgrade head
uvicorn app.main:app --reload  # http://localhost:8000/docs
python -m pytest -q            # needs Postgres at localhost:5433 (fish/fish); creates matami_test
```

Stripe end-to-end locally: set `APP_STRIPE_SECRET_KEY=sk_test_…`, then
`stripe listen --forward-to localhost:8000/api/stripe/webhook` and put the printed
`whsec_…` into `APP_STRIPE_WEBHOOK_SECRET`. Test card `4242 4242 4242 4242`.
```

- [ ] **Step 6: Commit**

```bash
git add backend && git commit -m "feat(backend): stale-hold sweep, admin attendee list and CSV export

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 10: Frontend foundation — router, language context, translations, API client, localisation helpers

**Files:**
- Create: `frontend/src/lang.tsx`, `frontend/src/components/LangSwitcher.tsx`, `frontend/src/theme.ts`, `frontend/src/api/client.ts`, `frontend/src/localized.ts`, `frontend/src/localized.test.ts`, `frontend/src/pages/LandingPage.tsx`
- Modify: `frontend/src/main.tsx`, `frontend/src/translations.ts`, `frontend/package.json`, `frontend/tsconfig.app.json` (exclude tests from build)
- Delete: `frontend/src/App.tsx` (content moves to `LandingPage.tsx`)

**Interfaces:**
- Produces:
  - `useLang(): { lang: Lang; setLang; t: Strings }`; `LangProvider`
  - `translations.toRunes(text)` exported
  - `pickLocalized(item: { title_fi: string|null; title_en: string|null; description_fi: string|null; description_en: string|null }, lang: Lang): { title: string; description: string }`
  - `formatEventDate(iso: string, lang: Lang): string` (Europe/Helsinki via `Intl.DateTimeFormat`, e.g. `en` → `Sat 10 Oct 2026, 18:00`, `fi` → `la 10.10.2026 klo 18.00`, `de` → `Sa., 10.10.2026, 18:00`, futhark uses `en`)
  - `formatPrice(cents: number, lang: Lang): string` (`0` → `t.free`)
  - `api.getEvents(): Promise<EventOut[]>`, `api.getEvent(slug)`, `api.checkout(slug, body)`, `api.registrationStatus(id)`, `api.cancelRegistration(id)`, `api.login(email,password)`, `api.logout()`, `api.me()`, `api.admin.listEvents()`, `api.admin.getEvent(id)`, `api.admin.createEvent(body)`, `api.admin.updateEvent(id, body)`, `api.admin.deleteEvent(id)`, `api.admin.registrations(id)`; `ApiError { status: number; detail: unknown }`
  - Types `EventOut`, `AdminEventOut`, `EventIn`, `AdminRegistrationOut` matching the backend schemas exactly.
  - Routes in `main.tsx`: `/`, `/events`, `/events/thanks`, `/events/:slug`, `/admin/login`, `/admin`, `/admin/events/new`, `/admin/events/:id`, `/admin/events/:id/attendees` (page components stubbed as `<div>` placeholders in this task, replaced in Tasks 11 and 12).
  - `theme.ts` exports: `colors` (`bg:'#1e2318', bgDeep:'#181d14', border:'#2a3d2b', moss:'#3d5a3e', mossLight:'#7a9e6a', mossDim:'#5c7a50', text:'#e8e0d0', textSoft:'#c8c0a8', textMuted:'#8a8070', plum:'#3a1e38', danger:'#b25a4a'`), `label` (small uppercase tracking style), `heading`, `card`, `button`, `buttonPrimary`, `input` style objects.

- [ ] **Step 1: Install deps**

```bash
cd frontend && npm i react-router-dom@6 && npm i -D vitest@2 @playwright/test
```
Add scripts to `package.json`: `"test": "vitest run"`, `"e2e": "playwright test"`. In `tsconfig.app.json` add `"exclude": ["src/**/*.test.ts"]` so `tsc -b` ignores vitest files (vitest has its own TS handling).

- [ ] **Step 2: Failing vitest**

`frontend/src/localized.test.ts`:
```ts
import { describe, expect, it } from 'vitest'
import { formatEventDate, formatPrice, pickLocalized } from './localized'

const both = { title_fi: 'Äänimaljailta', title_en: 'Sound Bowl Evening', description_fi: 'Tuo huopa.', description_en: 'Bring a blanket.' }
const enOnly = { ...both, title_fi: null, description_fi: null }
const fiOnly = { ...both, title_en: null, description_en: null }

describe('pickLocalized', () => {
  it('fi prefers Finnish, falls back to English', () => {
    expect(pickLocalized(both, 'fi').title).toBe('Äänimaljailta')
    expect(pickLocalized(enOnly, 'fi').title).toBe('Sound Bowl Evening')
  })
  it('en and de prefer English, fall back to Finnish', () => {
    expect(pickLocalized(both, 'de').title).toBe('Sound Bowl Evening')
    expect(pickLocalized(fiOnly, 'en').description).toBe('Tuo huopa.')
  })
  it('futhark transliterates the English text', () => {
    expect(pickLocalized(both, 'futhark').title).toBe('ᛊᛟᚢᚾᛞ ᛒᛟᚹᛚ ᛖᚹᛖᚾᛁᚾᚷ')
  })
  it('empty description becomes empty string', () => {
    expect(pickLocalized({ ...enOnly, description_en: null }, 'en').description).toBe('')
  })
})

describe('formatting', () => {
  it('shows Helsinki local time', () => {
    expect(formatEventDate('2026-10-10T15:00:00Z', 'fi')).toContain('10.10.2026')
    expect(formatEventDate('2026-10-10T15:00:00Z', 'fi')).toMatch(/18[.:]00/) // fi-FI prints 18.00
    expect(formatEventDate('2026-10-10T15:00:00Z', 'en')).toContain('18:00')
  })
  it('formats euros and free', () => {
    expect(formatPrice(2500, 'en')).toBe('25 €')
    expect(formatPrice(2550, 'en')).toBe('25.50 €')
    expect(formatPrice(2550, 'fi')).toBe('25,50 €')
    expect(formatPrice(0, 'en')).toBe('Free')
    expect(formatPrice(0, 'fi')).toBe('Ilmainen')
  })
})
```

Run: `npx vitest run` → fails (module missing).

- [ ] **Step 3: Translations**

In `frontend/src/translations.ts` export `toRunes` (add `export` to the function) and extend `Strings` + all three language objects with these keys (Futhark derives automatically):

| key | en | fi | de |
|---|---|---|---|
| navEvents | Events | Tapahtumat | Veranstaltungen |
| navHome | Home | Etusivu | Startseite |
| upcomingLabel | ✦ upcoming ✦ | ✦ tulossa ✦ | ✦ demnächst ✦ |
| upcomingHeading | Gatherings | Kokoontumiset | Zusammenkünfte |
| seeAllEvents | All events → | Kaikki tapahtumat → | Alle Veranstaltungen → |
| eventsHeading | Events | Tapahtumat | Veranstaltungen |
| eventsEmpty | Nothing on the calendar right now. The moss is resting. | Kalenteri on tyhjä juuri nyt. Sammal lepää. | Gerade ist nichts im Kalender. Das Moos ruht. |
| seatsLeft | {n} seats left | {n} paikkaa jäljellä | {n} Plätze frei |
| soldOut | Sold out | Loppuunmyyty | Ausverkauft |
| free | Free | Ilmainen | Kostenlos |
| perSeat | per seat | / paikka | pro Platz |
| signUpHeading | Sign up | Ilmoittaudu | Anmelden |
| nameLabel | Name | Nimi | Name |
| emailLabel | Email | Sähköposti | E-Mail |
| quantityLabel | Seats | Paikkoja | Plätze |
| payButton | Continue to payment | Siirry maksamaan | Zur Zahlung |
| registerFreeButton | Sign up | Ilmoittaudu | Anmelden |
| submitting | One moment… | Hetki… | Einen Moment… |
| errSoldOut | Those seats just went. | Nuo paikat menivät juuri. | Diese Plätze sind gerade weg. |
| errPayment | The payment service is unavailable. Please try again in a moment. | Maksupalvelu ei vastaa. Yritä hetken päästä uudelleen. | Der Zahlungsdienst ist nicht erreichbar. Bitte gleich noch einmal versuchen. |
| errGeneric | Something went wrong. | Jokin meni pieleen. | Etwas ist schiefgelaufen. |
| cancelledNote | Payment cancelled. Your seats were released. | Maksu peruttu. Paikkasi vapautettiin. | Zahlung abgebrochen. Deine Plätze wurden freigegeben. |
| thanksConfirming | Confirming your payment… | Vahvistetaan maksuasi… | Zahlung wird bestätigt… |
| thanksConfirmed | You're in. A confirmation is on its way to your email. | Olet mukana. Vahvistus on matkalla sähköpostiisi. | Du bist dabei. Eine Bestätigung ist unterwegs an deine E-Mail. |
| thanksPendingLong | Payment received. Your confirmation email will follow shortly. | Maksu vastaanotettu. Vahvistusviesti tulee pian. | Zahlung eingegangen. Die Bestätigung folgt in Kürze. |
| thanksExpired | This sign-up expired before payment completed. Please sign up again. | Ilmoittautuminen vanheni ennen maksun valmistumista. Ilmoittaudu uudelleen. | Diese Anmeldung ist vor Abschluss der Zahlung abgelaufen. Bitte erneut anmelden. |
| backToEvents | ← Back to events | ← Takaisin tapahtumiin | ← Zurück zu den Veranstaltungen |
| adminTitle | Admin | Hallinta | Verwaltung |
| adminLogin | Log in | Kirjaudu | Anmelden |
| adminLogout | Log out | Kirjaudu ulos | Abmelden |
| adminPassword | Password | Salasana | Passwort |
| adminBadLogin | Wrong email or password. | Väärä sähköposti tai salasana. | Falsche E-Mail oder Passwort. |
| adminEvents | Events | Tapahtumat | Veranstaltungen |
| adminNewEvent | New event | Uusi tapahtuma | Neue Veranstaltung |
| adminUpcoming | Upcoming | Tulevat | Bevorstehend |
| adminPast | Past | Menneet | Vergangen |
| adminPublished | Published | Julkaistu | Veröffentlicht |
| adminDraft | Draft | Luonnos | Entwurf |
| adminConfirmed | Confirmed | Vahvistetut | Bestätigt |
| adminCapacity | Capacity | Paikkoja | Kapazität |
| adminPriceEur | Price (€) | Hinta (€) | Preis (€) |
| adminStartsAt | Starts | Alkaa | Beginn |
| adminEndsAt | Ends (optional) | Päättyy (valinnainen) | Ende (optional) |
| adminLocation | Location | Paikka | Ort |
| adminTitleFi | Title (FI) | Otsikko (FI) | Titel (FI) |
| adminTitleEn | Title (EN) | Otsikko (EN) | Titel (EN) |
| adminDescFi | Description (FI) | Kuvaus (FI) | Beschreibung (FI) |
| adminDescEn | Description (EN) | Kuvaus (EN) | Beschreibung (EN) |
| adminSave | Save | Tallenna | Speichern |
| adminDelete | Delete | Poista | Löschen |
| adminDeleteBlocked | Cannot delete: confirmed sign-ups exist. | Ei voi poistaa: vahvistettuja ilmoittautumisia. | Löschen nicht möglich: bestätigte Anmeldungen vorhanden. |
| adminAttendees | Attendees | Osallistujat | Teilnehmende |
| adminDownloadCsv | Download CSV | Lataa CSV | CSV herunterladen |
| adminStatus | Status | Tila | Status |
| adminAmount | Paid | Maksettu | Bezahlt |
| adminCreated | Created | Luotu | Erstellt |
| adminEdit | Edit | Muokkaa | Bearbeiten |
| adminNeedTitle | Give the event a title in at least one language. | Anna tapahtumalle otsikko ainakin yhdellä kielellä. | Gib der Veranstaltung mindestens in einer Sprache einen Titel. |

`seatsLeft` is a template: render with `t.seatsLeft.replace('{n}', String(n))`. Plain `toRunes` would turn `{n}` into `{ᚾ}`, so `runeStrings` must keep placeholders intact:
```ts
function toRunesKeepingPlaceholders(text: string): string {
  return text
    .split(/(\{[a-z]+\})/)
    .map(part => (/^\{[a-z]+\}$/.test(part) ? part : toRunes(part)))
    .join('')
}

function runeStrings(base: Strings): Strings {
  return Object.fromEntries(
    Object.entries(base).map(([k, v]) => [k, toRunesKeepingPlaceholders(v)])
  ) as Strings
}
```

- [ ] **Step 4: Implement helpers**

`frontend/src/localized.ts`:
```ts
import { Lang, toRunes, translations } from './translations'

export interface Localizable {
  title_fi: string | null
  title_en: string | null
  description_fi: string | null
  description_en: string | null
}

export function pickLocalized(item: Localizable, lang: Lang): { title: string; description: string } {
  const fiFirst = lang === 'fi'
  const title = (fiFirst ? item.title_fi ?? item.title_en : item.title_en ?? item.title_fi) ?? ''
  const description =
    (fiFirst ? item.description_fi ?? item.description_en : item.description_en ?? item.description_fi) ?? ''
  if (lang === 'futhark') return { title: toRunes(title), description: toRunes(description) }
  return { title, description }
}

const LOCALE: Record<Lang, string> = { en: 'en-GB', fi: 'fi-FI', de: 'de-DE', futhark: 'en-GB' }

export function formatEventDate(iso: string, lang: Lang): string {
  return new Intl.DateTimeFormat(LOCALE[lang], {
    timeZone: 'Europe/Helsinki',
    weekday: 'short', day: 'numeric', month: lang === 'en' || lang === 'futhark' ? 'short' : 'numeric',
    year: 'numeric', hour: '2-digit', minute: '2-digit',
  }).format(new Date(iso))
}

export function formatPrice(cents: number, lang: Lang): string {
  if (cents === 0) return translations[lang].free
  const whole = cents % 100 === 0
  const n = new Intl.NumberFormat(LOCALE[lang], {
    minimumFractionDigits: whole ? 0 : 2, maximumFractionDigits: 2,
  }).format(cents / 100)
  return `${n} €`
}
```

`frontend/src/lang.tsx`:
```tsx
import { createContext, ReactNode, useContext, useState } from 'react'
import { Lang, Strings, translations } from './translations'

interface LangCtx { lang: Lang; setLang: (l: Lang) => void; t: Strings }
const Ctx = createContext<LangCtx | null>(null)

export function LangProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>(() => {
    try { return (localStorage.getItem('lang') as Lang) || 'en' } catch { return 'en' }
  })
  const set = (l: Lang) => { setLang(l); try { localStorage.setItem('lang', l) } catch { /* ignore */ } }
  return <Ctx.Provider value={{ lang, setLang: set, t: translations[lang] }}>{children}</Ctx.Provider>
}

export function useLang(): LangCtx {
  const v = useContext(Ctx)
  if (!v) throw new Error('useLang outside LangProvider')
  return v
}
```

`frontend/src/components/LangSwitcher.tsx`: move the fixed top-right switcher JSX out of `App.tsx` verbatim, reading `lang`/`setLang` from `useLang()`; export default.

`frontend/src/theme.ts`:
```ts
import type { CSSProperties } from 'react'

export const colors = {
  bg: '#1e2318', bgDeep: '#181d14', border: '#2a3d2b', moss: '#3d5a3e', mossLight: '#7a9e6a',
  mossDim: '#5c7a50', text: '#e8e0d0', textSoft: '#c8c0a8', textMuted: '#8a8070', plum: '#3a1e38',
  danger: '#b25a4a',
}
export const label: CSSProperties = { fontSize: '0.8rem', letterSpacing: '0.3em', textTransform: 'uppercase', color: colors.mossDim, marginBottom: '0.75rem' }
export const heading: CSSProperties = { fontSize: 'clamp(2rem, 5vw, 3rem)', color: colors.textSoft, margin: '0 0 1.5rem' }
export const card: CSSProperties = { border: `1px solid ${colors.border}`, padding: '1.5rem', background: colors.bg }
export const button: CSSProperties = { border: `1px solid ${colors.moss}`, color: colors.mossLight, background: 'transparent', padding: '0.65rem 1.5rem', letterSpacing: '0.12em', fontSize: '0.9rem', cursor: 'pointer', fontFamily: 'inherit' }
export const buttonPrimary: CSSProperties = { ...button, background: colors.moss, color: colors.text }
export const input: CSSProperties = { width: '100%', background: '#141810', border: `1px solid ${colors.border}`, color: colors.text, padding: '0.6rem 0.8rem', fontFamily: 'inherit', fontSize: '1rem' }
```

`frontend/src/api/client.ts`:
```ts
export interface EventOut {
  id: number; slug: string; title_fi: string | null; title_en: string | null
  description_fi: string | null; description_en: string | null
  starts_at: string; ends_at: string | null; location: string | null
  price_cents: number; currency: string; capacity: number; seats_left: number; sold_out: boolean
}
export interface AdminEventOut extends EventOut { is_published: boolean; confirmed_count: number; pending_count: number }
export interface EventIn {
  title_fi: string | null; title_en: string | null; description_fi: string | null; description_en: string | null
  starts_at: string; ends_at: string | null; location: string | null
  price_cents: number; capacity: number; is_published: boolean
}
export interface AdminRegistrationOut {
  id: string; name: string; email: string; quantity: number; status: string
  amount_cents: number; created_at: string; confirmed_at: string | null
}
export type RegistrationStatus = 'pending' | 'confirmed' | 'cancelled' | 'expired'

export class ApiError extends Error {
  constructor(public status: number, public detail: unknown) { super(`API ${status}`) }
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`/api${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    credentials: 'same-origin',
  })
  if (!r.ok) {
    let detail: unknown = null
    try { detail = (await r.json()).detail } catch { /* no body */ }
    throw new ApiError(r.status, detail)
  }
  if (r.status === 204) return undefined as T
  return r.json() as Promise<T>
}
const post = <T,>(path: string, body?: unknown) => req<T>(path, { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) })
const put = <T,>(path: string, body: unknown) => req<T>(path, { method: 'PUT', body: JSON.stringify(body) })

export const api = {
  getEvents: () => req<EventOut[]>('/events'),
  getEvent: (slug: string) => req<EventOut>(`/events/${slug}`),
  checkout: (slug: string, body: { name: string; email: string; quantity: number; lang: string }) =>
    post<{ registration_id: string; checkout_url: string | null }>(`/events/${slug}/checkout`, body),
  registrationStatus: (id: string) => req<{ status: RegistrationStatus; event_slug: string; quantity: number }>(`/registrations/${id}/status`),
  cancelRegistration: (id: string) => post<void>(`/registrations/${id}/cancel`),
  login: (email: string, password: string) => post<void>('/auth/login', { email, password }),
  logout: () => post<void>('/auth/logout'),
  me: () => req<{ email: string }>('/auth/me'),
  admin: {
    listEvents: () => req<AdminEventOut[]>('/admin/events'),
    getEvent: (id: number) => req<AdminEventOut>(`/admin/events/${id}`),
    createEvent: (body: EventIn) => post<AdminEventOut>('/admin/events', body),
    updateEvent: (id: number, body: EventIn) => put<AdminEventOut>(`/admin/events/${id}`, body),
    deleteEvent: (id: number) => req<void>(`/admin/events/${id}`, { method: 'DELETE' }),
    registrations: (id: number) => req<AdminRegistrationOut[]>(`/admin/events/${id}/registrations`),
    registrationsCsvUrl: (id: number) => `/api/admin/events/${id}/registrations.csv`,
  },
}
```

- [ ] **Step 5: Landing page + router**

Rename `App.tsx` → `pages/LandingPage.tsx`: remove the local `useState` for lang and the switcher block; use `const { lang, t } = useLang()`; render `<LangSwitcher />` at the top; leave everything else byte-identical (Task 11 adds `<UpcomingSection />`). Also in the header area add a small fixed top-left nav link to `/events` using `t.navEvents` (`<Link>` from react-router, styled like the switcher's buttons).

`frontend/src/main.tsx`:
```tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import './index.css'
import { LangProvider } from './lang'
import LandingPage from './pages/LandingPage'

const Todo = ({ name }: { name: string }) => <div style={{ padding: '2rem' }}>{name}</div>

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <LangProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/events" element={<Todo name="events" />} />
          <Route path="/events/thanks" element={<Todo name="thanks" />} />
          <Route path="/events/:slug" element={<Todo name="event" />} />
          <Route path="/admin/login" element={<Todo name="admin login" />} />
          <Route path="/admin" element={<Todo name="admin" />} />
          <Route path="/admin/events/new" element={<Todo name="new" />} />
          <Route path="/admin/events/:id" element={<Todo name="edit" />} />
          <Route path="/admin/events/:id/attendees" element={<Todo name="attendees" />} />
        </Routes>
      </BrowserRouter>
    </LangProvider>
  </StrictMode>,
)
```

- [ ] **Step 6: Verify**

Run: `npx vitest run && npm run lint && npx tsc -b && npm run build`
Expected: 6 vitest tests pass, lint clean, build ok. Start `npm run dev`, open `/` and confirm the landing page renders as before with the switcher working.

- [ ] **Step 7: Commit**

```bash
git add frontend && git commit -m "feat(frontend): router, language context, API client and localisation helpers

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 11: Public pages — events list, event detail with sign-up, thanks page, landing "Upcoming" section

**Files:**
- Create: `frontend/src/pages/EventsPage.tsx`, `frontend/src/pages/EventDetailPage.tsx`, `frontend/src/pages/ThanksPage.tsx`, `frontend/src/components/UpcomingSection.tsx`, `frontend/src/components/EventCard.tsx`, `frontend/src/components/PageShell.tsx`
- Modify: `frontend/src/main.tsx` (replace stubs), `frontend/src/pages/LandingPage.tsx` (add `<UpcomingSection />` between Services and Contact)

**Interfaces:**
- Consumes: `api`, `useLang`, `pickLocalized`, `formatEventDate`, `formatPrice`, theme.
- Produces: `PageShell({ children })` — dark background, `<CornerFrames />`, `<LangSwitcher />`, top-left `← navHome` link, centred `maxWidth: 820px` content; `EventCard({ event })` — linked card used by both list and Upcoming.

- [ ] **Step 1: PageShell and EventCard**

`frontend/src/components/PageShell.tsx`:
```tsx
import { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import CornerFrames from '../CornerFrames'
import { useLang } from '../lang'
import { colors } from '../theme'
import LangSwitcher from './LangSwitcher'

export default function PageShell({ children }: { children: ReactNode }) {
  const { t } = useLang()
  return (
    <div style={{ background: colors.bg, minHeight: '100vh' }}>
      <CornerFrames />
      <LangSwitcher />
      <Link to="/" style={{ position: 'fixed', top: '1.3rem', left: '1.5rem', zIndex: 100, color: colors.mossDim, textDecoration: 'none', letterSpacing: '0.12em', fontSize: '0.85rem' }}>
        {t.navHome}
      </Link>
      <main style={{ maxWidth: '820px', margin: '0 auto', padding: '6rem 1.5rem 5rem' }}>{children}</main>
    </div>
  )
}
```

`frontend/src/components/EventCard.tsx`:
```tsx
import { Link } from 'react-router-dom'
import type { EventOut } from '../api/client'
import { useLang } from '../lang'
import { formatEventDate, formatPrice, pickLocalized } from '../localized'
import { card, colors } from '../theme'

export default function EventCard({ event }: { event: EventOut }) {
  const { lang, t } = useLang()
  const { title } = pickLocalized(event, lang)
  const seats = event.sold_out ? t.soldOut : t.seatsLeft.replace('{n}', String(event.seats_left))
  return (
    <Link to={`/events/${event.slug}`} style={{ ...card, display: 'block', textDecoration: 'none', opacity: event.sold_out ? 0.6 : 1 }}>
      <div style={{ color: colors.mossLight, fontSize: '0.85rem', letterSpacing: '0.15em' }}>{formatEventDate(event.starts_at, lang)}</div>
      <h3 style={{ margin: '0.4rem 0 0.5rem', fontSize: '1.6rem', color: colors.textSoft }}>{title}</h3>
      <div style={{ display: 'flex', justifyContent: 'space-between', color: colors.textMuted, fontSize: '0.95rem' }}>
        <span>{event.location ?? ''}</span>
        <span>{formatPrice(event.price_cents, lang)} · {seats}</span>
      </div>
    </Link>
  )
}
```

- [ ] **Step 2: EventsPage**

`frontend/src/pages/EventsPage.tsx`:
```tsx
import { useEffect, useState } from 'react'
import { api, type EventOut } from '../api/client'
import EventCard from '../components/EventCard'
import PageShell from '../components/PageShell'
import { useLang } from '../lang'
import { colors, heading, label } from '../theme'

function monthKey(iso: string, locale: string): string {
  return new Intl.DateTimeFormat(locale, { timeZone: 'Europe/Helsinki', month: 'long', year: 'numeric' }).format(new Date(iso))
}

export default function EventsPage() {
  const { lang, t } = useLang()
  const [events, setEvents] = useState<EventOut[] | null>(null)
  useEffect(() => { api.getEvents().then(setEvents).catch(() => setEvents([])) }, [])
  const locale = { en: 'en-GB', fi: 'fi-FI', de: 'de-DE', futhark: 'en-GB' }[lang]
  const groups = new Map<string, EventOut[]>()
  for (const e of events ?? []) {
    const k = monthKey(e.starts_at, locale)
    groups.set(k, [...(groups.get(k) ?? []), e])
  }
  return (
    <PageShell>
      <p style={{ ...label, textAlign: 'center' }}>{t.upcomingLabel}</p>
      <h2 style={{ ...heading, textAlign: 'center' }}>{t.eventsHeading}</h2>
      {events && events.length === 0 && <p style={{ textAlign: 'center', color: colors.textMuted, fontStyle: 'italic' }}>{t.eventsEmpty}</p>}
      {[...groups].map(([month, list]) => (
        <section key={month} style={{ marginBottom: '2.5rem' }}>
          <h3 style={{ color: colors.mossDim, fontSize: '1rem', letterSpacing: '0.2em', textTransform: 'uppercase', fontStyle: 'normal' }}>{month}</h3>
          <div style={{ display: 'grid', gap: '1rem' }}>{list.map(e => <EventCard key={e.id} event={e} />)}</div>
        </section>
      ))}
    </PageShell>
  )
}
```

- [ ] **Step 3: EventDetailPage with sign-up form and cancel handling**

`frontend/src/pages/EventDetailPage.tsx`:
```tsx
import { FormEvent, useEffect, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { api, ApiError, type EventOut } from '../api/client'
import PageShell from '../components/PageShell'
import { useLang } from '../lang'
import { formatEventDate, formatPrice, pickLocalized } from '../localized'
import { buttonPrimary, colors, heading, input, label } from '../theme'

export default function EventDetailPage() {
  const { slug = '' } = useParams()
  const [params, setParams] = useSearchParams()
  const { lang, t } = useLang()
  const [event, setEvent] = useState<EventOut | null | undefined>(undefined)
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [quantity, setQuantity] = useState(1)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [cancelled, setCancelled] = useState(false)

  const load = () => api.getEvent(slug).then(setEvent).catch(() => setEvent(null))
  useEffect(() => { load() }, [slug]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const reg = params.get('cancelled')
    if (!reg) return
    api.cancelRegistration(reg).catch(() => undefined).finally(() => { setCancelled(true); load(); setParams({}, { replace: true }) })
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  if (event === undefined) return <PageShell><p style={{ color: colors.textMuted }}>…</p></PageShell>
  if (event === null) return <PageShell><p style={{ color: colors.textMuted }}>{t.errGeneric}</p><Link to="/events" style={{ color: colors.mossLight }}>{t.backToEvents}</Link></PageShell>

  const { title, description } = pickLocalized(event, lang)
  const max = Math.min(10, event.seats_left)

  async function submit(e: FormEvent) {
    e.preventDefault()
    setBusy(true); setError(null)
    try {
      const r = await api.checkout(event!.slug, { name, email, quantity, lang })
      if (r.checkout_url) window.location.assign(r.checkout_url)
      else window.location.assign(`/events/thanks?reg=${r.registration_id}`)
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) { setError(t.errSoldOut); load() }
      else if (err instanceof ApiError && err.status === 502) setError(t.errPayment)
      else setError(t.errGeneric)
      setBusy(false)
    }
  }

  return (
    <PageShell>
      <Link to="/events" style={{ color: colors.mossDim, textDecoration: 'none', fontSize: '0.9rem' }}>{t.backToEvents}</Link>
      <p style={{ ...label, marginTop: '2rem' }}>{formatEventDate(event.starts_at, lang)}</p>
      <h2 style={heading}>{title}</h2>
      <p style={{ color: colors.textMuted }}>{event.location}</p>
      <p style={{ color: colors.textSoft, whiteSpace: 'pre-line', fontSize: '1.1rem' }}>{description}</p>
      <p style={{ color: colors.mossLight, letterSpacing: '0.1em' }}>
        {formatPrice(event.price_cents, lang)} {event.price_cents > 0 && t.perSeat} · {event.sold_out ? t.soldOut : t.seatsLeft.replace('{n}', String(event.seats_left))}
      </p>
      {cancelled && <p style={{ color: colors.textMuted, fontStyle: 'italic' }}>{t.cancelledNote}</p>}
      {!event.sold_out && (
        <form onSubmit={submit} style={{ marginTop: '2.5rem', display: 'grid', gap: '1rem', maxWidth: '420px' }}>
          <h3 style={{ margin: 0, color: colors.textSoft }}>{t.signUpHeading}</h3>
          <label style={{ color: colors.textMuted }}>{t.nameLabel}<input style={input} value={name} onChange={e => setName(e.target.value)} required maxLength={120} /></label>
          <label style={{ color: colors.textMuted }}>{t.emailLabel}<input style={input} type="email" value={email} onChange={e => setEmail(e.target.value)} required /></label>
          <label style={{ color: colors.textMuted }}>{t.quantityLabel}
            <select style={input} value={quantity} onChange={e => setQuantity(Number(e.target.value))}>
              {Array.from({ length: max }, (_, i) => i + 1).map(n => <option key={n} value={n}>{n}</option>)}
            </select>
          </label>
          {error && <p style={{ color: colors.danger, margin: 0 }}>{error}</p>}
          <button type="submit" style={buttonPrimary} disabled={busy}>
            {busy ? t.submitting : event.price_cents > 0 ? t.payButton : t.registerFreeButton}
          </button>
        </form>
      )}
    </PageShell>
  )
}
```

- [ ] **Step 4: ThanksPage**

`frontend/src/pages/ThanksPage.tsx`:
```tsx
import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api, type RegistrationStatus } from '../api/client'
import PageShell from '../components/PageShell'
import { useLang } from '../lang'
import { colors, heading } from '../theme'

const POLL_MS = 2000
const MAX_POLLS = 30

export default function ThanksPage() {
  const [params] = useSearchParams()
  const { t } = useLang()
  const reg = params.get('reg')
  const [status, setStatus] = useState<RegistrationStatus | 'unknown' | 'timeout'>('pending')

  useEffect(() => {
    if (!reg) { setStatus('unknown'); return }
    let polls = 0
    let timer: number | undefined
    const tick = async () => {
      try {
        const r = await api.registrationStatus(reg)
        if (r.status !== 'pending') { setStatus(r.status); return }
      } catch { setStatus('unknown'); return }
      if (++polls >= MAX_POLLS) { setStatus('timeout'); return }
      timer = window.setTimeout(tick, POLL_MS)
    }
    tick()
    return () => window.clearTimeout(timer)
  }, [reg])

  const text = {
    pending: t.thanksConfirming, confirmed: t.thanksConfirmed, timeout: t.thanksPendingLong,
    expired: t.thanksExpired, cancelled: t.thanksExpired, unknown: t.errGeneric,
  }[status]

  return (
    <PageShell>
      <h2 style={{ ...heading, textAlign: 'center' }}>{status === 'confirmed' ? '✦' : '☽'}</h2>
      <p data-testid="thanks-status" style={{ textAlign: 'center', color: colors.textSoft, fontSize: '1.2rem' }}>{text}</p>
      <p style={{ textAlign: 'center' }}><Link to="/events" style={{ color: colors.mossLight }}>{t.backToEvents}</Link></p>
    </PageShell>
  )
}
```

- [ ] **Step 5: UpcomingSection on the landing page**

`frontend/src/components/UpcomingSection.tsx`:
```tsx
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type EventOut } from '../api/client'
import { useLang } from '../lang'
import { colors, heading, label } from '../theme'
import EventCard from './EventCard'

export default function UpcomingSection() {
  const { t } = useLang()
  const [events, setEvents] = useState<EventOut[]>([])
  useEffect(() => { api.getEvents().then(list => setEvents(list.slice(0, 3))).catch(() => setEvents([])) }, [])
  if (events.length === 0) return null
  return (
    <section id="events" style={{ padding: '5rem 1.5rem', background: colors.bg }}>
      <div style={{ maxWidth: '820px', margin: '0 auto' }}>
        <p style={{ ...label, textAlign: 'center' }}>{t.upcomingLabel}</p>
        <h2 style={{ ...heading, textAlign: 'center' }}>{t.upcomingHeading}</h2>
        <div style={{ display: 'grid', gap: '1rem' }}>{events.map(e => <EventCard key={e.id} event={e} />)}</div>
        <p style={{ textAlign: 'center', marginTop: '2rem' }}>
          <Link to="/events" style={{ color: colors.mossLight, letterSpacing: '0.12em', textDecoration: 'none' }}>{t.seeAllEvents}</Link>
        </p>
      </div>
    </section>
  )
}
```

Insert `<UpcomingSection />` in `LandingPage.tsx` right after the Services `</section>`. Replace the three public `Todo` routes in `main.tsx` with the real pages.

- [ ] **Step 6: Verify by hand**

Run backend (`uvicorn app.main:app --reload`) and `npm run dev`. Log in with the dev owner via curl and create a published event:
```bash
curl -c c.txt -X POST localhost:8000/api/auth/login -H 'content-type: application/json' -d '{"email":"admin@example.com","password":"admin"}'
curl -b c.txt -X POST localhost:8000/api/admin/events -H 'content-type: application/json' -d '{"title_fi":"Äänimaljailta","title_en":"Sound Bowl Evening","description_en":"Bring a blanket.","starts_at":"2026-10-10T15:00:00Z","location":"The moss","price_cents":2500,"capacity":8,"is_published":true}'
```
Check `/`, `/events`, the detail page, submit the form (with `APP_STRIPE_SECRET_KEY` unset the API returns 502 and the form shows `errPayment`; with a test key it redirects to Stripe). Then `npm run lint && npx tsc -b && npm run build`.

- [ ] **Step 7: Commit**

```bash
git add frontend && git commit -m "feat(frontend): public events list, event sign-up page, thanks page and Upcoming section

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 12: Admin UI — login, events list, event form, attendees

**Files:**
- Create: `frontend/src/pages/admin/AdminLayout.tsx`, `AdminLoginPage.tsx`, `AdminEventsPage.tsx`, `AdminEventFormPage.tsx`, `AdminAttendeesPage.tsx`, `frontend/src/pages/admin/datetime.ts`
- Modify: `frontend/src/main.tsx` (replace admin stubs; nest admin routes under `AdminLayout`)

**Interfaces:**
- Consumes: `api.admin.*`, `api.me/login/logout`, theme, translations.
- Produces: `AdminLayout` — calls `api.me()` on mount; on 401 redirects to `/admin/login`; renders a slim header (`adminTitle`, `adminEvents` link, `adminLogout`) and `<Outlet />`. `datetime.ts`: `isoToLocalInput(iso: string | null): string` (UTC ISO → `YYYY-MM-DDTHH:mm` in Europe/Helsinki) and `localInputToIso(v: string): string | null` (Helsinki wall time → UTC ISO).

- [ ] **Step 1: datetime helpers + vitest**

`frontend/src/pages/admin/datetime.test.ts`:
```ts
import { expect, it } from 'vitest'
import { isoToLocalInput, localInputToIso } from './datetime'

it('round-trips Helsinki wall time', () => {
  expect(isoToLocalInput('2026-10-10T15:00:00Z')).toBe('2026-10-10T18:00')   // EEST
  expect(isoToLocalInput('2026-12-10T15:00:00Z')).toBe('2026-12-10T17:00')   // EET
  expect(localInputToIso('2026-10-10T18:00')).toBe('2026-10-10T15:00:00.000Z')
  expect(localInputToIso('2026-12-10T17:00')).toBe('2026-12-10T15:00:00.000Z')
  expect(localInputToIso('')).toBeNull()
  expect(isoToLocalInput(null)).toBe('')
})
```

`frontend/src/pages/admin/datetime.ts`:
```ts
const TZ = 'Europe/Helsinki'

export function isoToLocalInput(iso: string | null): string {
  if (!iso) return ''
  const parts = new Intl.DateTimeFormat('en-GB', {
    timeZone: TZ, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false,
  }).formatToParts(new Date(iso))
  const g = (type: string) => parts.find(p => p.type === type)?.value ?? '00'
  return `${g('year')}-${g('month')}-${g('day')}T${g('hour') === '24' ? '00' : g('hour')}:${g('minute')}`
}

/** Convert a Helsinki wall-clock `YYYY-MM-DDTHH:mm` to UTC ISO by iterating the offset. */
export function localInputToIso(v: string): string | null {
  if (!v) return null
  const [d, tm] = v.split('T')
  const [y, m, day] = d.split('-').map(Number)
  const [h, min] = tm.split(':').map(Number)
  let guess = Date.UTC(y, m - 1, day, h, min)
  for (let i = 0; i < 2; i++) {
    const back = isoToLocalInput(new Date(guess).toISOString())
    const [bd, bt] = back.split('T')
    const [by, bm, bday] = bd.split('-').map(Number)
    const [bh, bmin] = bt.split(':').map(Number)
    const diff = Date.UTC(by, bm - 1, bday, bh, bmin) - guess
    if (diff === 0) break
    guess -= diff
  }
  return new Date(guess).toISOString()
}
```

Run `npx vitest run` → passes.

- [ ] **Step 2: AdminLayout and login**

`frontend/src/pages/admin/AdminLayout.tsx`:
```tsx
import { useEffect, useState } from 'react'
import { Link, Outlet, useNavigate } from 'react-router-dom'
import { api } from '../../api/client'
import LangSwitcher from '../../components/LangSwitcher'
import { useLang } from '../../lang'
import { button, colors } from '../../theme'

export default function AdminLayout() {
  const { t } = useLang()
  const nav = useNavigate()
  const [ready, setReady] = useState(false)
  useEffect(() => { api.me().then(() => setReady(true)).catch(() => nav('/admin/login', { replace: true })) }, [nav])
  if (!ready) return null
  return (
    <div style={{ background: colors.bgDeep, minHeight: '100vh', color: colors.text }}>
      <LangSwitcher />
      <header style={{ display: 'flex', gap: '1.5rem', alignItems: 'center', padding: '1rem 1.5rem', borderBottom: `1px solid ${colors.border}` }}>
        <strong style={{ letterSpacing: '0.15em' }}>{t.adminTitle}</strong>
        <Link to="/admin" style={{ color: colors.mossLight }}>{t.adminEvents}</Link>
        <Link to="/" style={{ color: colors.mossDim }}>{t.navHome}</Link>
        <button style={{ ...button, marginLeft: 'auto', marginRight: '9rem' }} onClick={() => api.logout().then(() => nav('/admin/login'))}>{t.adminLogout}</button>
      </header>
      <main style={{ maxWidth: '960px', margin: '0 auto', padding: '2rem 1.5rem' }}><Outlet /></main>
    </div>
  )
}
```

`frontend/src/pages/admin/AdminLoginPage.tsx`:
```tsx
import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../../api/client'
import { useLang } from '../../lang'
import { buttonPrimary, colors, input } from '../../theme'

export default function AdminLoginPage() {
  const { t } = useLang()
  const nav = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [err, setErr] = useState(false)
  async function submit(e: FormEvent) {
    e.preventDefault()
    try { await api.login(email, password); nav('/admin') } catch { setErr(true) }
  }
  return (
    <div style={{ background: colors.bgDeep, minHeight: '100vh', display: 'grid', placeItems: 'center' }}>
      <form onSubmit={submit} style={{ display: 'grid', gap: '1rem', width: 'min(360px, 90vw)' }}>
        <h2 style={{ color: colors.textSoft, margin: 0 }}>{t.adminLogin}</h2>
        <input style={input} type="email" placeholder={t.emailLabel} value={email} onChange={e => setEmail(e.target.value)} required />
        <input style={input} type="password" placeholder={t.adminPassword} value={password} onChange={e => setPassword(e.target.value)} required />
        {err && <p style={{ color: colors.danger, margin: 0 }}>{t.adminBadLogin}</p>}
        <button style={buttonPrimary} type="submit">{t.adminLogin}</button>
      </form>
    </div>
  )
}
```

- [ ] **Step 3: Events list**

`frontend/src/pages/admin/AdminEventsPage.tsx`:
```tsx
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type AdminEventOut } from '../../api/client'
import { useLang } from '../../lang'
import { formatEventDate, formatPrice, pickLocalized } from '../../localized'
import { buttonPrimary, colors } from '../../theme'

function Table({ rows }: { rows: AdminEventOut[] }) {
  const { lang, t } = useLang()
  return (
    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.95rem' }}>
      <thead><tr style={{ color: colors.mossDim, textAlign: 'left' }}>
        <th>{t.adminStartsAt}</th><th>{t.eventsHeading}</th><th>{t.adminPriceEur}</th><th>{t.adminConfirmed}</th><th></th><th></th>
      </tr></thead>
      <tbody>{rows.map(e => (
        <tr key={e.id} style={{ borderTop: `1px solid ${colors.border}` }}>
          <td style={{ padding: '0.6rem 0' }}>{formatEventDate(e.starts_at, lang)}</td>
          <td>{pickLocalized(e, lang).title}</td>
          <td>{formatPrice(e.price_cents, lang)}</td>
          <td>{e.confirmed_count} / {e.capacity}{e.pending_count > 0 && <span style={{ color: colors.textMuted }}> (+{e.pending_count})</span>}</td>
          <td style={{ color: e.is_published ? colors.mossLight : colors.textMuted }}>{e.is_published ? t.adminPublished : t.adminDraft}</td>
          <td style={{ textAlign: 'right' }}>
            <Link to={`/admin/events/${e.id}`} style={{ color: colors.mossLight, marginRight: '1rem' }}>{t.adminEdit}</Link>
            <Link to={`/admin/events/${e.id}/attendees`} style={{ color: colors.mossLight }}>{t.adminAttendees}</Link>
          </td>
        </tr>
      ))}</tbody>
    </table>
  )
}

export default function AdminEventsPage() {
  const { t } = useLang()
  const [events, setEvents] = useState<AdminEventOut[]>([])
  useEffect(() => { api.admin.listEvents().then(setEvents) }, [])
  const now = Date.now()
  const upcoming = events.filter(e => new Date(e.starts_at).getTime() >= now).sort((a, b) => a.starts_at.localeCompare(b.starts_at))
  const past = events.filter(e => new Date(e.starts_at).getTime() < now)
  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ color: colors.textSoft }}>{t.adminEvents}</h2>
        <Link to="/admin/events/new" style={{ ...buttonPrimary, textDecoration: 'none' }}>{t.adminNewEvent}</Link>
      </div>
      <h3 style={{ color: colors.mossDim }}>{t.adminUpcoming}</h3>
      <Table rows={upcoming} />
      <h3 style={{ color: colors.mossDim, marginTop: '2.5rem' }}>{t.adminPast}</h3>
      <Table rows={past} />
    </>
  )
}
```

- [ ] **Step 4: Event form**

`frontend/src/pages/admin/AdminEventFormPage.tsx`:
```tsx
import { FormEvent, useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api, ApiError, type EventIn } from '../../api/client'
import { useLang } from '../../lang'
import { button, buttonPrimary, colors, input } from '../../theme'
import { isoToLocalInput, localInputToIso } from './datetime'

interface Form {
  title_fi: string; title_en: string; description_fi: string; description_en: string
  starts_at: string; ends_at: string; location: string; price_eur: string; capacity: string; is_published: boolean
}
const empty: Form = { title_fi: '', title_en: '', description_fi: '', description_en: '', starts_at: '', ends_at: '', location: '', price_eur: '0', capacity: '10', is_published: false }

function toBody(f: Form): EventIn {
  return {
    title_fi: f.title_fi.trim() || null, title_en: f.title_en.trim() || null,
    description_fi: f.description_fi.trim() || null, description_en: f.description_en.trim() || null,
    starts_at: localInputToIso(f.starts_at) ?? '', ends_at: localInputToIso(f.ends_at),
    location: f.location.trim() || null,
    price_cents: Math.round(Number(f.price_eur.replace(',', '.')) * 100), capacity: Number(f.capacity), is_published: f.is_published,
  }
}

export default function AdminEventFormPage() {
  const { id } = useParams()
  const eventId = id ? Number(id) : null
  const { t } = useLang()
  const nav = useNavigate()
  const [f, setF] = useState<Form>(empty)
  const [err, setErr] = useState<string | null>(null)
  const [confirmedCount, setConfirmedCount] = useState(0)

  useEffect(() => {
    if (eventId === null) return
    api.admin.getEvent(eventId).then(e => {
      setConfirmedCount(e.confirmed_count)
      setF({
        title_fi: e.title_fi ?? '', title_en: e.title_en ?? '', description_fi: e.description_fi ?? '', description_en: e.description_en ?? '',
        starts_at: isoToLocalInput(e.starts_at), ends_at: isoToLocalInput(e.ends_at), location: e.location ?? '',
        price_eur: (e.price_cents / 100).toString(), capacity: String(e.capacity), is_published: e.is_published,
      })
    })
  }, [eventId])

  const set = <K extends keyof Form>(k: K) => (e: { target: { value: string } }) => setF({ ...f, [k]: e.target.value })

  async function submit(e: FormEvent) {
    e.preventDefault()
    setErr(null)
    const body = toBody(f)
    if (!body.title_fi && !body.title_en) { setErr(t.adminNeedTitle); return }
    try {
      if (eventId === null) await api.admin.createEvent(body)
      else await api.admin.updateEvent(eventId, body)
      nav('/admin')
    } catch (ex) { setErr(ex instanceof ApiError ? JSON.stringify(ex.detail) : t.errGeneric) }
  }

  async function remove() {
    if (eventId === null || !window.confirm(t.adminDelete + '?')) return
    try { await api.admin.deleteEvent(eventId); nav('/admin') }
    catch (ex) { setErr(ex instanceof ApiError && ex.status === 409 ? t.adminDeleteBlocked : t.errGeneric) }
  }

  const field = (labelText: string, el: JSX.Element) => <label style={{ color: colors.textMuted, display: 'grid', gap: '0.3rem' }}>{labelText}{el}</label>

  return (
    <form onSubmit={submit} style={{ display: 'grid', gap: '1rem', maxWidth: '640px' }}>
      <h2 style={{ color: colors.textSoft, margin: 0 }}>{eventId === null ? t.adminNewEvent : t.adminEdit}</h2>
      {field(t.adminTitleFi, <input style={input} value={f.title_fi} onChange={set('title_fi')} maxLength={200} />)}
      {field(t.adminTitleEn, <input style={input} value={f.title_en} onChange={set('title_en')} maxLength={200} />)}
      {field(t.adminDescFi, <textarea style={{ ...input, minHeight: '6rem' }} value={f.description_fi} onChange={set('description_fi')} />)}
      {field(t.adminDescEn, <textarea style={{ ...input, minHeight: '6rem' }} value={f.description_en} onChange={set('description_en')} />)}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
        {field(t.adminStartsAt, <input style={input} type="datetime-local" value={f.starts_at} onChange={set('starts_at')} required />)}
        {field(t.adminEndsAt, <input style={input} type="datetime-local" value={f.ends_at} onChange={set('ends_at')} />)}
      </div>
      {field(t.adminLocation, <input style={input} value={f.location} onChange={set('location')} maxLength={300} />)}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
        {field(t.adminPriceEur, <input style={input} inputMode="decimal" value={f.price_eur} onChange={set('price_eur')} required />)}
        {field(t.adminCapacity, <input style={input} type="number" min={1} value={f.capacity} onChange={set('capacity')} required />)}
      </div>
      <label style={{ color: colors.textMuted }}>
        <input type="checkbox" checked={f.is_published} onChange={e => setF({ ...f, is_published: e.target.checked })} /> {t.adminPublished}
      </label>
      {err && <p style={{ color: colors.danger, margin: 0 }}>{err}</p>}
      <div style={{ display: 'flex', gap: '1rem' }}>
        <button type="submit" style={buttonPrimary}>{t.adminSave}</button>
        {eventId !== null && <button type="button" style={{ ...button, color: colors.danger, borderColor: colors.danger }} onClick={remove} disabled={confirmedCount > 0} title={confirmedCount > 0 ? t.adminDeleteBlocked : ''}>{t.adminDelete}</button>}
      </div>
    </form>
  )
}
```

- [ ] **Step 5: Attendees**

`frontend/src/pages/admin/AdminAttendeesPage.tsx`:
```tsx
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, type AdminEventOut, type AdminRegistrationOut } from '../../api/client'
import { useLang } from '../../lang'
import { formatEventDate, formatPrice, pickLocalized } from '../../localized'
import { button, colors } from '../../theme'

export default function AdminAttendeesPage() {
  const id = Number(useParams().id)
  const { lang, t } = useLang()
  const [event, setEvent] = useState<AdminEventOut | null>(null)
  const [rows, setRows] = useState<AdminRegistrationOut[]>([])
  useEffect(() => { api.admin.getEvent(id).then(setEvent); api.admin.registrations(id).then(setRows) }, [id])
  if (!event) return null
  return (
    <>
      <Link to="/admin" style={{ color: colors.mossDim }}>← {t.adminEvents}</Link>
      <h2 style={{ color: colors.textSoft }}>{pickLocalized(event, lang).title}</h2>
      <p style={{ color: colors.textMuted }}>{formatEventDate(event.starts_at, lang)} · {t.adminConfirmed}: {event.confirmed_count} / {event.capacity}</p>
      <a href={api.admin.registrationsCsvUrl(id)} style={{ ...button, textDecoration: 'none', display: 'inline-block' }}>{t.adminDownloadCsv}</a>
      <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '1.5rem', fontSize: '0.95rem' }}>
        <thead><tr style={{ color: colors.mossDim, textAlign: 'left' }}>
          <th>{t.nameLabel}</th><th>{t.emailLabel}</th><th>{t.quantityLabel}</th><th>{t.adminStatus}</th><th>{t.adminAmount}</th><th>{t.adminCreated}</th>
        </tr></thead>
        <tbody>{rows.map(r => (
          <tr key={r.id} style={{ borderTop: `1px solid ${colors.border}`, color: r.status === 'confirmed' ? colors.text : colors.textMuted }}>
            <td style={{ padding: '0.5rem 0' }}>{r.name}</td><td>{r.email}</td><td>{r.quantity}</td><td>{r.status}</td>
            <td>{formatPrice(r.amount_cents, lang)}</td><td>{formatEventDate(r.created_at, lang)}</td>
          </tr>
        ))}</tbody>
      </table>
    </>
  )
}
```

- [ ] **Step 6: Routes**

In `main.tsx` replace the admin stubs with:
```tsx
<Route path="/admin/login" element={<AdminLoginPage />} />
<Route path="/admin" element={<AdminLayout />}>
  <Route index element={<AdminEventsPage />} />
  <Route path="events/new" element={<AdminEventFormPage />} />
  <Route path="events/:id" element={<AdminEventFormPage />} />
  <Route path="events/:id/attendees" element={<AdminAttendeesPage />} />
</Route>
```
Remove the `Todo` component.

- [ ] **Step 7: Verify**

`npx vitest run && npm run lint && npx tsc -b && npm run build`. By hand: log in at `/admin/login` (dev owner `admin@example.com` / `admin`), create an event, publish it, see it on `/events`, open attendees, download CSV.

- [ ] **Step 8: Commit**

```bash
git add frontend && git commit -m "feat(frontend): admin login, event list, event form and attendee list

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 13: Playwright smoke test of the sign-up flow (stubbed API)

**Files:**
- Create: `frontend/playwright.config.ts`, `frontend/e2e/signup.spec.ts`
- Modify: `frontend/.gitignore` (add `test-results`, `playwright-report`)

- [ ] **Step 1: Config**

`frontend/playwright.config.ts`:
```ts
import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: 'e2e',
  timeout: 30_000,
  use: { baseURL: 'http://localhost:5173', headless: true },
  webServer: { command: 'npm run dev -- --port 5173', url: 'http://localhost:5173', reuseExistingServer: true },
})
```
Install a browser once: `npx playwright install chromium`.

- [ ] **Step 2: Spec**

`frontend/e2e/signup.spec.ts`:
```ts
import { expect, test } from '@playwright/test'

const event = {
  id: 1, slug: 'sound-bowl-abcd', title_fi: 'Äänimaljailta', title_en: 'Sound Bowl Evening',
  description_fi: null, description_en: 'Bring a blanket.', starts_at: '2030-10-10T15:00:00Z', ends_at: null,
  location: 'The moss', price_cents: 2500, currency: 'EUR', capacity: 8, seats_left: 3, sold_out: false,
}

test('visitor signs up and is sent to checkout', async ({ page }) => {
  await page.route('**/api/events', r => r.fulfill({ json: [event] }))
  await page.route('**/api/events/sound-bowl-abcd', r => r.fulfill({ json: event }))
  let posted: unknown = null
  await page.route('**/api/events/sound-bowl-abcd/checkout', async r => {
    posted = r.request().postDataJSON()
    await r.fulfill({ json: { registration_id: 'reg-1', checkout_url: 'http://localhost:5173/events/thanks?reg=reg-1' } })
  })
  await page.route('**/api/registrations/reg-1/status', r =>
    r.fulfill({ json: { status: 'confirmed', event_slug: 'sound-bowl-abcd', quantity: 2 } }))

  await page.goto('/events')
  await page.getByText('Sound Bowl Evening').click()
  await expect(page).toHaveURL(/\/events\/sound-bowl-abcd$/)
  await expect(page.getByText('3 seats left')).toBeVisible()
  await page.getByLabel('Name').fill('Aino')
  await page.getByLabel('Email').fill('aino@example.fi')
  await page.getByLabel('Seats').selectOption('2')
  await page.getByRole('button', { name: 'Continue to payment' }).click()

  await expect(page).toHaveURL(/\/events\/thanks\?reg=reg-1/)
  expect(posted).toEqual({ name: 'Aino', email: 'aino@example.fi', quantity: 2, lang: 'en' })
  await expect(page.getByTestId('thanks-status')).toHaveText("You're in. A confirmation is on its way to your email.")
})

test('sold out hides the form', async ({ page }) => {
  await page.route('**/api/events/sound-bowl-abcd', r => r.fulfill({ json: { ...event, seats_left: 0, sold_out: true } }))
  await page.goto('/events/sound-bowl-abcd')
  await expect(page.getByText('Sold out')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Continue to payment' })).toHaveCount(0)
})
```

- [ ] **Step 3: Run** — `cd frontend && npx playwright test` → 2 passed.

- [ ] **Step 4: Commit**

```bash
git add frontend && git commit -m "test(frontend): Playwright smoke test for the sign-up flow

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 14: Docker packaging, compose, env example, DEPLOY.md

**Files:**
- Create: `backend/Dockerfile`, `backend/.dockerignore`, `frontend/Dockerfile`, `frontend/nginx.conf`, `frontend/.dockerignore`, `docker-compose.yml`, `.env.example`, `DEPLOY.md`

- [ ] **Step 1: Backend image**

`backend/Dockerfile`:
```dockerfile
FROM python:3.12-slim
WORKDIR /srv
COPY pyproject.toml ./
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
RUN pip install --no-cache-dir .
ENV PYTHONPATH=/srv
EXPOSE 8000
CMD alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000
```
`backend/.dockerignore`: `.venv`, `tests`, `__pycache__`, `.pytest_cache`, `.ruff_cache`, `.env`.

- [ ] **Step 2: Frontend image + nginx**

`frontend/nginx.conf`:
```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    location /api/ {
        proxy_pass http://api:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_request_buffering off;   # webhook body passes through untouched
        client_max_body_size 1m;
    }
    location /health { proxy_pass http://api:8000/health; }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

`frontend/Dockerfile`:
```dockerfile
FROM node:22-slim AS build
WORKDIR /fe
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /fe/dist /usr/share/nginx/html
EXPOSE 80
```
`frontend/.dockerignore`: `node_modules`, `dist`, `e2e`, `test-results`, `playwright-report`.

- [ ] **Step 3: Compose and env**

`docker-compose.yml`:
```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: matami
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: matami
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U matami"]
      interval: 5s
      timeout: 3s
      retries: 10
    restart: unless-stopped

  api:
    build: ./backend
    env_file: .env
    environment:
      APP_ENV: production
      APP_DATABASE_URL: postgresql+psycopg://matami:${POSTGRES_PASSWORD}@db:5432/matami
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

  web:
    build: ./frontend
    ports:
      - "${WEB_PORT:-8080}:80"
    depends_on:
      - api
    restart: unless-stopped

volumes:
  pgdata:
```

`.env.example`:
```
# Postgres (compose)
POSTGRES_PASSWORD=change-me
WEB_PORT=8080

# App
APP_SECRET_KEY=change-me-long-random           # openssl rand -hex 32
APP_PUBLIC_BASE_URL=https://matami.example.fi  # no trailing slash; used in Stripe return URLs
APP_ADMIN_EMAIL=matami@example.com
APP_ADMIN_PASSWORD=change-me                   # only used to create the first admin
APP_CONTACT_EMAIL=matami@example.com           # shown in confirmation emails

# Stripe (dashboard → Developers → API keys / Webhooks)
APP_STRIPE_SECRET_KEY=sk_live_...
APP_STRIPE_WEBHOOK_SECRET=whsec_...

# SMTP for confirmation emails (leave APP_SMTP_HOST empty to only log)
APP_SMTP_HOST=
APP_SMTP_PORT=587
APP_SMTP_USER=
APP_SMTP_PASSWORD=
APP_SMTP_FROM=matami@example.com
```

- [ ] **Step 4: DEPLOY.md**

```markdown
# Deploying

Requirements: a Linux host with Docker + Docker Compose v2, a domain pointing at it, and a reverse proxy for HTTPS (Caddy example below).

1. `git clone … && cd matami-mottonen && cp .env.example .env` and fill every value. Generate `APP_SECRET_KEY` with `openssl rand -hex 32`.
2. `docker compose up -d --build`. The API runs migrations on start. Check `curl localhost:8080/health`.
3. HTTPS with Caddy (`/etc/caddy/Caddyfile`):
   ```
   matami.example.fi {
       reverse_proxy localhost:8080
   }
   ```
4. Stripe: in the dashboard create a webhook endpoint `https://matami.example.fi/api/stripe/webhook` with events `checkout.session.completed`, `checkout.session.expired`, `charge.refunded`. Put its signing secret in `APP_STRIPE_WEBHOOK_SECRET` and `docker compose up -d api`.
   Also enable "Email customers about successful payments" in Stripe if you want Stripe's own receipt in addition to our confirmation email.
5. Log in at `https://matami.example.fi/admin/login` with `APP_ADMIN_EMAIL` / `APP_ADMIN_PASSWORD` and create events. Changing the password later: run
   `docker compose exec api python -c "from app.db import SessionLocal; from app.models import AdminUser; from app.security import hash_password; db=SessionLocal(); u=db.query(AdminUser).first(); u.password_hash=hash_password('NEW'); db.commit()"`.
6. Backups: `0 3 * * * cd /path/to/matami-mottonen && docker compose exec -T db pg_dump -U matami matami | gzip > /backups/matami-$(date +\%F).sql.gz`
7. Updating: `git pull && docker compose up -d --build`.

Refunds are done in the Stripe dashboard; the webhook frees the seats automatically.
```

- [ ] **Step 5: Verify the stack builds**

Docker is unavailable on this WSL machine, so verify what can be verified: `docker compose config` if Docker exists; otherwise check `nginx -t`-free syntax by eye, confirm `frontend/Dockerfile` and `backend/Dockerfile` reference only files that exist (`ls backend/alembic.ini backend/app backend/alembic frontend/nginx.conf`), and note in the commit message that the images were not built locally.

- [ ] **Step 6: Commit**

```bash
git add docker-compose.yml .env.example DEPLOY.md backend/Dockerfile backend/.dockerignore frontend/Dockerfile frontend/nginx.conf frontend/.dockerignore
git commit -m "chore: docker-compose packaging, env example and deployment guide

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```
