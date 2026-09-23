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
