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
