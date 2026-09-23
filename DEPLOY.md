# Deploying

Requirements: a Linux host with Docker + Docker Compose v2, a domain pointing at it, and a reverse proxy for HTTPS (Caddy example below).

1. `git clone … && cd matami-mottonen && cp .env.example .env` and fill every value. Generate `APP_SECRET_KEY` with `openssl rand -hex 32`. The API refuses to boot with `APP_ENV=production` while any of `APP_SECRET_KEY`, `APP_ADMIN_PASSWORD`, `APP_STRIPE_SECRET_KEY` or `APP_STRIPE_WEBHOOK_SECRET` still holds a placeholder — check `docker compose logs api` if the container restarts.
2. `docker compose up -d --build`. The API runs migrations on start. Check `curl localhost:8080/health`.
3. HTTPS with Caddy (`/etc/caddy/Caddyfile`):
   ```
   matami.example.fi {
       reverse_proxy localhost:8080 {
           header_up X-Forwarded-For {http.request.remote.host}
       }
   }
   ```
   `header_up X-Forwarded-For {http.request.remote.host}` *replaces* any header the
   client sent with the real peer address, so a caller cannot forge someone else's
   IP past the per-IP login rate limit. (Login is also limited per account, so a
   proxy misconfigured here does not leave the admin password open to a botnet.)
4. Stripe: in the dashboard create a webhook endpoint `https://matami.example.fi/api/stripe/webhook` subscribed to all five events the API handles: `checkout.session.completed`, `checkout.session.async_payment_succeeded`, `checkout.session.async_payment_failed`, `checkout.session.expired`, `charge.refunded`. (The two `async_payment_*` events settle delayed payment methods, whose session completes before the money arrives; without them such seats stay pending until the hold sweep drops them.) Put its signing secret in `APP_STRIPE_WEBHOOK_SECRET` and `docker compose up -d api`.
   Also enable "Email customers about successful payments" in Stripe if you want Stripe's own receipt in addition to our confirmation email.
5. Log in at `https://matami.example.fi/admin/login` with `APP_ADMIN_EMAIL` / `APP_ADMIN_PASSWORD` and create events. Changing the password later: run
   `docker compose exec api python -c "from app.db import SessionLocal; from app.models import AdminUser; from app.security import hash_password; db=SessionLocal(); u=db.query(AdminUser).first(); u.password_hash=hash_password('NEW'); db.commit()"`.
6. Backups: `0 3 * * * cd /path/to/matami-mottonen && docker compose exec -T db pg_dump -U matami matami | gzip > /backups/matami-$(date +\%F).sql.gz`
7. Updating: `git pull && docker compose up -d --build`.

Refunds are done in the Stripe dashboard; the webhook frees the seats automatically.
