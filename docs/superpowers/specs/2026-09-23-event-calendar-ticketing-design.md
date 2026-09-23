# Event calendar with paid sign-ups — design

**Date:** 2026-09-23
**Status:** approved (brainstormed with the owner)

## Goal

Add an event calendar to the Matami Möttönen site where visitors browse
upcoming events (sound bowl ceremonies, tarot evenings, …) and sign up by
paying for a ticket. Matami creates and manages events herself through a
small admin UI. The whole stack is self-hosted by a friend of the owner with
one `docker compose up`.

## Decisions already made

| Question | Decision |
|---|---|
| Paywall model | Pay per event (ticketing). Calendar is public; a sign-up is a paid ticket. |
| Event admin | Matami, through an admin UI on the site. |
| Backend | FastAPI + Postgres + Alembic, packaged with docker-compose. |
| Payments | Stripe Checkout (hosted page) + webhook. Holvi has no payment API (only PSD2/accounting APIs and a hosted shop with iframe embeds), so it stays Matami's bank account for payouts. Paytrail rejected for its monthly fee. |
| Sign-up data | Name + email, quantity 1..N (N = seats left, capped at 10). |
| Event copy | Finnish + English fields. German falls back to English; Futhark is transliterated from English as today. UI chrome is translated in all four languages. |
| Seat holding | Reserve-then-pay: a `pending` registration counts against capacity for 30 minutes while the buyer is on Stripe. |
| Frontend | React Router added. Landing page unchanged apart from an "Upcoming" section. |

## Repository layout

```
matami-mottonen/
  frontend/            # existing Vite app moved here unchanged, plus new pages
  backend/
    app/
      main.py          # FastAPI app, CORS, router mounting, startup migrations
      config.py        # pydantic-settings, APP_ prefix
      security.py      # password hashing, session cookie signing
      api/             # routers: auth, events (public), checkout, stripe_webhook, admin_events, admin_registrations
      domain/          # pure logic, no SQLAlchemy/FastAPI: capacity.py, registration_state.py
      models/          # SQLAlchemy: base, admin_user, event, registration
      repositories/    # DB access
      services/        # checkout.py, webhook.py, mailer.py, sweep.py
    alembic/
    tests/
    Dockerfile
  docker-compose.yml   # db (postgres:16), api (uvicorn), web (nginx: static build + /api proxy)
  .env.example
  DEPLOY.md
```

The backend follows the layered shape of `fish-inventory` but stays small.
`domain/` has no framework imports so capacity rules and the registration
state machine are unit-testable without a database.

## Data model

### events

| column | type | notes |
|---|---|---|
| id | int PK | |
| slug | text unique | generated from title_en (or title_fi) + short random suffix; immutable |
| title_fi, title_en | text | at least one required |
| description_fi, description_en | text | optional, plain text with line breaks |
| starts_at | timestamptz | required |
| ends_at | timestamptz | optional |
| location | text | free text |
| price_cents | int | ≥ 0; 0 means free (still goes through registration, skips Stripe) |
| currency | text | always `EUR` for now |
| capacity | int | ≥ 1 |
| is_published | bool | drafts are admin-only |
| created_at, updated_at | timestamptz | |

Past events remain in the DB and drop off the public list once `starts_at`
is in the past.

### registrations

| column | type | notes |
|---|---|---|
| id | uuid PK | exposed to the browser; unguessable |
| event_id | FK events | |
| name, email | text | |
| quantity | int | 1..10 |
| status | enum | `pending`, `confirmed`, `cancelled`, `expired` |
| amount_cents | int | quantity × price at time of checkout |
| stripe_session_id | text unique nullable | |
| stripe_payment_intent_id | text nullable | |
| expires_at | timestamptz | pending hold deadline (created_at + 30 min) |
| created_at, confirmed_at | timestamptz | |

**Seats taken** for an event = Σ quantity over registrations where
`status = 'confirmed'` OR (`status = 'pending'` AND `expires_at > now()`).
**Seats left** = capacity − seats taken.

### admin_users

| column | type |
|---|---|
| id | int PK |
| email | text unique |
| password_hash | text |

One owner account, created on first start from `APP_ADMIN_EMAIL` /
`APP_ADMIN_PASSWORD` if the table is empty. No roles.

### Registration state machine

```
pending ──checkout.session.completed──▶ confirmed ──charge.refunded──▶ cancelled
   │
   ├──checkout.session.expired / sweep past expires_at──▶ expired
   └──buyer cancels (POST /registrations/{id}/cancel)───▶ expired
```

Transitions out of `confirmed`, `cancelled`, `expired` other than the one
shown are ignored (idempotent webhooks). A free event (price 0) goes
`pending → confirmed` immediately in the checkout endpoint.

## API

All under `/api`. JSON in/out. Times in ISO 8601 UTC.

### Public

- `GET /events` — published, `starts_at >= now()`, ordered by `starts_at`.
  Each item: id, slug, titles, descriptions, starts_at, ends_at, location,
  price_cents, currency, capacity, seats_left, sold_out.
- `GET /events/{slug}` — one published event, same shape. 404 for drafts.
- `POST /events/{slug}/checkout` — body `{ name, email, quantity }`.
  Validates (name 1..120 chars, email syntactically valid, quantity 1..10).
  In one transaction: `SELECT … FOR UPDATE` the event, compute seats left,
  409 `sold_out` if quantity > seats left, insert `pending` registration.
  Then create the Stripe Checkout Session (see below); on Stripe failure,
  roll the registration back and return 502. Returns
  `{ registration_id, checkout_url }`. For a free event returns
  `{ registration_id, checkout_url: null }` with the registration already
  confirmed and the email sent.
- `GET /registrations/{id}/status` — `{ status, event_slug, quantity }`.
  Used by the thanks page.
- `POST /registrations/{id}/cancel` — only while `pending`: expires the
  Stripe session via the API (`checkout.Session.expire`) and marks the
  registration `expired`, releasing the seats immediately. Any other
  status → 409. Called by the event page when it loads with
  `?cancelled={id}`.
- `POST /stripe/webhook` — raw body, `Stripe-Signature` verified with
  `APP_STRIPE_WEBHOOK_SECRET`; 400 on bad signature. Handles
  `checkout.session.completed`, `checkout.session.expired`,
  `charge.refunded`. Always 200 after successful handling; unknown event
  types are acknowledged and ignored.

### Admin (session cookie required, 401 otherwise)

- `POST /auth/login` `{ email, password }` → sets HTTP-only cookie.
  Rate-limited 5 / 5 min per IP.
- `POST /auth/logout`, `GET /auth/me`.
- `GET /admin/events` — all events incl. drafts and past, with
  `confirmed_count`, `pending_count`.
- `POST /admin/events`, `PUT /admin/events/{id}`, `DELETE /admin/events/{id}`
  (delete only if no confirmed registrations; else 409).
- `GET /admin/events/{id}/registrations` — all registrations for the event.
- `GET /admin/events/{id}/registrations.csv` — same as CSV.

### Stripe Checkout Session

Created with `mode=payment`, one `line_item` using `price_data` built from
our DB (currency, unit_amount = price_cents, product name = title in the
buyer's language, quantity), `customer_email` prefilled,
`client_reference_id` = registration id, `metadata.registration_id`,
`expires_at` = the registration's `expires_at` (Stripe minimum is 30 min,
so the hold is exactly 30 min), `success_url` =
`{PUBLIC_BASE_URL}/events/thanks?reg={id}`, `cancel_url` =
`{PUBLIC_BASE_URL}/events/{slug}?cancelled={registration id}`. The webhook handler looks
the registration up by `stripe_session_id` first, then by
`metadata.registration_id`.

## Sign-up flow

1. Visitor opens `/events/:slug`: date, place, price, seats left, form
   (name, email, quantity ≤ min(seats left, 10)).
2. Submit → `POST checkout` → browser navigates to `checkout_url`.
3. Stripe webhook confirms the registration and sends the confirmation
   email.
4. `/events/thanks?reg=…` polls status every 2 s for up to 60 s. Shows
   "Confirming your payment…" while `pending`; the confirmation when
   `confirmed`; a "payment received, confirmation email will follow" note
   if still pending after 60 s (Stripe retries webhooks); an explanation
   if `expired`.
5. Seats-left reads always exclude pending rows past `expires_at`, so a
   stuck hold never blocks seats. A background task every 5 minutes marks
   such rows `expired` (the `sweep` service) to keep the table honest.

## Email

`services/mailer.py` sends via SMTP from `APP_SMTP_HOST/PORT/USER/PASSWORD/FROM`.
One template, in the buyer's site language (FI or EN; DE/Futhark buyers get
EN): event title, date and time (Europe/Helsinki), location, quantity,
amount paid, Matami's contact address. Sending runs in a FastAPI
`BackgroundTask` after the webhook has committed; a failure is logged with
the registration id and retried up to 3 times with backoff. It never
blocks or fails the confirmation. Stripe's own receipt is optional and
configured in the Stripe dashboard.

## Admin UI (`/admin`)

- **Login** — email + password.
- **Events list** — two groups, upcoming and past; columns: date, title,
  price, confirmed / capacity, published badge; "New event" button.
- **Event form** — the columns from the data model; datetime pickers in
  Europe/Helsinki; "Published" toggle; delete (disabled when confirmed
  registrations exist).
- **Attendees** — per event: name, email, quantity, status, amount,
  created; CSV download. Refunds happen in the Stripe dashboard; the
  `charge.refunded` webhook cancels the registration and frees the seats.

Visual language matches the site (dark moss palette, serif headings) but
prioritises legibility over ornament.

## Public UI

- `/` — existing landing page plus an **Upcoming** section between
  offerings and contact: next three published events with date, title,
  price, seats-left/sold-out, linking to `/events/:slug`, and a link to
  `/events`. Section hidden if there are no upcoming events.
- `/events` — all upcoming published events grouped by month, with the
  corner frames and language switcher.
- `/events/:slug` — detail + sign-up form; `?cancelled={id}` calls the
  cancel endpoint, strips the param, and shows a quiet "payment
  cancelled, your seats were released" note.
- `/events/thanks` — as in the flow above.

New UI copy is added to `translations.ts` (`Strings` grows; Futhark stays
transliterated from EN). Event titles/descriptions are chosen by a helper
`pickLocalized(event, lang)`: `fi` → fi ?? en; `en`/`de` → en ?? fi;
`futhark` → toRunes(en ?? fi).

Routing: `react-router-dom` v6 with `BrowserRouter`; nginx serves
`index.html` for unknown paths.

## Errors

| situation | behaviour |
|---|---|
| Sold out at submit | 409 `{ code: 'sold_out', seats_left }`; form re-renders seats left |
| Stripe create fails | pending row rolled back, 502; form shows "payment service unavailable, try again" |
| Bad webhook signature | 400, logged |
| Webhook for unknown registration | 200, logged at warning (nothing to do) |
| Email send fails | logged, retried ×3, registration stays confirmed |
| Admin deletes event with confirmed registrations | 409 |

## Configuration (`.env.example`)

```
APP_DATABASE_URL=postgresql+psycopg://matami:matami@db:5432/matami
APP_SECRET_KEY=change-me                # cookie signing
APP_PUBLIC_BASE_URL=https://example.fi
APP_ADMIN_EMAIL=matami@example.com
APP_ADMIN_PASSWORD=change-me
APP_STRIPE_SECRET_KEY=sk_test_…
APP_STRIPE_WEBHOOK_SECRET=whsec_…
APP_SMTP_HOST=
APP_SMTP_PORT=587
APP_SMTP_USER=
APP_SMTP_PASSWORD=
APP_SMTP_FROM=matami@example.com
POSTGRES_PASSWORD=matami
```

## Deployment (`docker-compose.yml`, `DEPLOY.md`)

- `db`: postgres:16, named volume.
- `api`: built from `backend/Dockerfile`; entrypoint runs
  `alembic upgrade head` then uvicorn on 8000; depends on db healthy.
- `web`: nginx serving `frontend/dist` (multi-stage build) on port 80,
  proxying `/api/` to `api:8000` with the raw body intact for the webhook.
- The friend puts HTTPS in front (Caddy example given), fills `.env`,
  registers `https://<host>/api/stripe/webhook` in the Stripe dashboard
  with the three event types, and installs the documented `pg_dump` cron
  line for backups.

## Testing

- **Backend (pytest, `matami_test` DB created/dropped by the suite):**
  domain unit tests for seats-left arithmetic and the state machine;
  API tests for checkout (happy path, sold out, validation, free event),
  concurrent last-seat race (two threads, one 409), webhook handling
  (signature check, completed, expired, refunded, idempotent replay,
  unknown registration), sweep, admin auth and CRUD, CSV. Stripe is
  mocked at the SDK boundary; webhook payloads are signed in tests with
  the test secret.
- **Frontend:** `tsc -b` and `eslint` as today; vitest unit test for
  `pickLocalized`; one Playwright smoke test that loads `/events`, opens
  an event, submits the form against a stubbed checkout endpoint, and
  asserts the redirect.
- **Manual end-to-end:** Stripe test keys + `stripe listen --forward-to
  localhost:8000/api/stripe/webhook`, documented in `backend/README.md`.

## Out of scope

Recurring events, discount codes, waitlists, refunds from the admin UI,
multiple admins/roles, per-event images, Paytrail. Each can be added later
without changing the data model except where noted.
