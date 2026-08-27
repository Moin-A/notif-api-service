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

### How the Redis queue works

The queue is hand-rolled on a single Redis **list** at key `notif:queue` (defined in
`app/queue.py`). There is no queue library — just two Redis list commands:

- **Producer** (`app/main.py`) — on `POST /notifications`, serializes the payload to
  JSON and `RPUSH`es it onto the right end of the list. The HTTP request returns `202`
  immediately; delivery happens later, out of band.
- **Consumer** (`app/worker.py`) — loops on `BLPOP notif:queue`, which pops from the
  left end (FIFO). `BLPOP` *blocks* until a job is available instead of busy-polling,
  so an idle worker uses no CPU. We pass a 5s timeout so the loop wakes periodically to
  check for shutdown; on timeout `BLPOP` returns `None` and we just loop again.

Both sides connect via `get_redis()`, which reads the `REDIS_URL` env var (set in the
k8s deployments; falls back to `redis://localhost:6379/2` for local dev) — there is no
shared state beyond the Redis list itself, so
the API and worker are fully decoupled and each can be scaled or restarted independently.

Caveats of this simple design: `BLPOP` removes the job *before* it's processed, so a
worker crash mid-delivery loses that job (no retry/ack). The worker reconnects on
Redis errors and shuts down gracefully on `SIGTERM`, but at-least-once delivery would
need a reliable-queue pattern (e.g. `BLMOVE` into a processing list, or a library like RQ).

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
