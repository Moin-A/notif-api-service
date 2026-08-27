"""Background worker.

Runs as its own deployment. Blocks on the shared Redis queue and delivers each
queued notification. Uses the same Redis and Postgres instances as reptrack.
"""
import json
import logging

from app.queue import QUEUE_KEY, get_redis

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("notif-worker")


def process(job: dict) -> None:
    logger.info("delivering notification to=%s channel=%s", job.get("to"), job.get("channel"))
    # TODO: actually send the notification and persist a delivery record to Postgres
    #       (app.db.SessionLocal is available for that).


def main() -> None:
    r = get_redis()
    logger.info("notif-worker started, waiting for jobs on %s", QUEUE_KEY)
    while True:
        _, raw = r.blpop(QUEUE_KEY)
        try:
            process(json.loads(raw))
        except Exception:
            logger.exception("failed to process job: %s", raw)


if __name__ == "__main__":
    main()
