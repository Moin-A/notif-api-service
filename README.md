# notif-api-service

A FastAPI notification service with a Redis-backed background worker. Shares
reptrack's Redis and Postgres instances (own db/namespace) and deploys to the
same k3s cluster on the Raspberry Pi.

## Architecture

- **API** (`app/main.py`) — accepts notifications and pushes them onto a Redis queue.
- **Worker** (`app/worker.py`) — blocks on the Redis queue and delivers each notification.
- **Redis** — reuses reptrack's Redis (`redis.reptrack.svc.cluster.local:6379`), db `2`
  (reptrack uses 0 = sidekiq, 1 = cable).
- **Postgres** — reuses reptrack's Postgres instance
  (`postgres.practify.svc.cluster.local:5432`), separate `notif_staging` database.

## Local development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# needs a local Redis + Postgres, or point at real ones:
export REDIS_URL="redis://localhost:6379/2"
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/notif"

uvicorn app.main:app --reload    # API on :8000, docs at /docs
python -m app.worker             # worker (separate shell)
```

Enqueue a notification:

```bash
curl -X POST http://127.0.0.1:8000/notifications \
  -H 'Content-Type: application/json' \
  -d '{"to":"a@b.com","channel":"email","message":"hi"}'
```

## Deployment

Pushing to `main` triggers `.github/workflows/deploy-staging.yml`, which SSHes into
the Pi and runs `deploy_script.sh` (git sync → docker build/push → `kubectl apply`
+ rollout of the `notif-api` and `notif-worker` deployments in the `notif` namespace).

### One-time cluster setup (on the Pi)

Create the `notif_staging` database on the shared Postgres instance, then create the
secret (keeps the DB password out of git, same pattern as `reptrack-secrets`):

```bash
kubectl create namespace notif

kubectl create secret generic notif-secrets -n notif \
  --from-literal=DATABASE_URL='postgresql://practify:your_password_here@postgres.practify.svc.cluster.local:5432/notif_staging'
```

Required GitHub Actions secrets (same as reptrack): `SSH_PRIVATE_KEY`, `PI_USER`,
`PI_HOST`, `DOCKER_USERNAME`, `DOCKER_PASSWORD`.
