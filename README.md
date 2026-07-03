# Mother Teresa Transport — Full Project

Website + booking backend for Mother Teresa Transport (Saravanampatti, Coimbatore).

```
frontend/     Customer-facing site (plain HTML/CSS/JS) — home, booking form, tracking page
admin/        Staff dashboard (plain HTML/CSS/JS) — login, manage bookings, update status
backend/      FastAPI + PostgreSQL API — bookings, tracking, admin auth, notifications
```

Frontend and admin are static, no-build sites. The backend is a real API with a
database, so it needs to be deployed somewhere it can run continuously (a VPS,
Render, Railway, Fly.io, etc.) rather than a static host.

## How it fits together

1. A customer fills the booking form on the website → it's saved to Postgres via
   the API → the customer gets a **tracking code** and an automated confirmation
   (email and/or WhatsApp/SMS, if configured) → the form also opens WhatsApp with
   a pre-filled message as a human-readable backup.
2. The customer can check progress any time on the **Track** page using their
   tracking code + phone number.
3. Staff log into **/admin** with a username and password, see every booking,
   search/filter them, and update status (Received → Confirmed → Picked up →
   In transit → Delivered). Each update can automatically notify the customer.

## Before you launch — fill these in

| What | Where |
|---|---|
| WhatsApp number (customer-facing) | `frontend/js/script.js` → `WHATSAPP_NUMBER` |
| Phone number in `tel:` links | `frontend/index.html` |
| Services list (currently sample content) | `frontend/index.html` → `<section class="services">` |
| Secret key, DB URL, SMTP/Twilio credentials | `backend/.env` (copy from `.env.example`) |
| `API_BASE_URL` in `frontend/js/script.js` / `admin/js/admin.js` | Only if you're **not** using the nginx setup below — see Architecture section |

## Architecture: one nginx container in front of everything

```
                    ┌────────────────────────────┐
   browser ───────▶ │   nginx (web)  :80          │
                    │   /        → frontend/      │
                    │   /admin/  → admin/          │
                    │   /api/    → proxy to api:8000
                    └──────────────┬───────────────┘
                                   ▼
                          ┌────────────────┐
                          │  api (FastAPI) │
                          └────────┬───────┘
                                   ▼
                          ┌────────────────┐
                          │  db (Postgres) │
                          └────────────────┘
```

Because nginx proxies `/api/` to the backend, requests from the browser are
same-origin — that's why `API_BASE_URL` in `frontend/js/script.js` and
`admin/js/admin.js` is left as `""` by default. Only change it if you're
running the backend standalone without nginx in front of it.

## Running the full stack locally with Docker

```bash
cp backend/.env.example backend/.env    # then edit real values
docker compose up --build
```
This builds and starts `db`, `api`, and `web` together. Visit:
- Site: http://localhost
- Admin: http://localhost/admin
- API docs: http://localhost/docs

Create your first staff login (run once, against the running `api` container):
```bash
docker compose exec api python -m app.create_admin
```

## Database migrations (Alembic)

The API auto-creates tables on first run for convenience, but for anything
beyond local development, use Alembic migrations instead:
```bash
docker compose exec api alembic revision --autogenerate -m "init"
docker compose exec api alembic upgrade head
```
Run `alembic revision --autogenerate` again any time you change `app/models.py`.

## CI/CD with Jenkins

`Jenkinsfile` at the repo root defines the pipeline:
1. **Checkout** the repo
2. **Backend sanity check** — installs deps, byte-compiles the backend as a fast smoke test
3. **Build images** — `mtt-api` from `backend/Dockerfile`, `mtt-web` from `nginx/Dockerfile`
4. **Push images** to your registry, tagged with the build number and `latest`
5. **Deploy** — SSHes into your server, pulls the new images via `docker-compose.prod.yml`, and restarts the stack

### One-time setup before the pipeline can run

**On the Jenkins server:**
- Install the Docker Pipeline and SSH Agent plugins
- Add credentials (Manage Jenkins → Credentials):
  - `dockerhub-creds` — Username/Password for your registry (Docker Hub, GHCR, etc.)
  - `deploy-ssh-key` — SSH private key for the deploy server
- Create a Pipeline job pointed at this repo, using the `Jenkinsfile`

**In the `Jenkinsfile`**, replace the placeholders:
- `REGISTRY_NAMESPACE` — your Docker Hub username (or full registry path)
- `DEPLOY_HOST` — your server's IP/hostname
- `DEPLOY_USER` — the SSH user Jenkins deploys as
- `DEPLOY_PATH` — where this repo lives on that server

**On the deploy server, once, before the first pipeline run:**
```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git /opt/mother-teresa-transport
cd /opt/mother-teresa-transport
cp backend/.env.example backend/.env     # fill in real values — this file stays on the server, never in git
```
After that, every push to `main` (once the Jenkins job is wired to trigger on
push — add a webhook or poll SCM) rebuilds, pushes, and redeploys automatically.

### Two compose files, two purposes
- `docker-compose.yml` — builds images locally from source. Use this for local dev (`docker compose up --build`).
- `docker-compose.prod.yml` — pulls pre-built images from the registry by tag. This is what the deploy server runs; Jenkins never builds on the server itself.

## Security notes

- There is no public admin signup endpoint on purpose — only someone with
  server/CLI access can create a staff account (`python -m app.create_admin`).
- `SECRET_KEY` in `.env` signs login tokens — generate a real random one before
  going live (`python -c "import secrets; print(secrets.token_hex(32))"`) and
  never reuse the placeholder.
- `CORS_ORIGINS` in `.env` should list only your real frontend/admin domains
  once deployed — remove the localhost defaults.
- The tracking endpoint requires both the tracking code *and* the phone number
  used at booking time, so a guessed code alone can't expose someone else's
  booking details.

## What's not built yet (future work, if you want it)

- Real-time chat between customer and staff (current "messaging" = automated
  status notifications only, per your earlier answer).
- Customer accounts / login (current design is guest booking + tracking code,
  no customer signup).
- Payment collection online (business currently takes cash, per the listing).

Happy to build any of these next when you're ready.
