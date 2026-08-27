"""Background worker.

Runs as its own deployment. Blocks on the shared Redis queue and delivers each
queued notification. Uses the same Redis and Postgres instances as reptrack.
"""
import json
import logging
import signal
import time

import redis as redis_lib

from app.queue import QUEUE_KEY, get_redis

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("notif-worker")

# Bounded block so the loop wakes periodically to honour shutdown and reconnect.
BLPOP_TIMEOUT_SECONDS = 5

_shutdown = False


def _request_shutdown(signum, _frame) -> None:
    global _shutdown
    logger.info("received signal %s, shutting down after current job", signum)
    _shutdown = True


def process(job: dict) -> None:
    logger.info("delivering notification to=%s channel=%s", job.get("to"), job.get("channel"))
    # TODO: actually send the notification and persist a delivery record to Postgres
    #       (app.db.SessionLocal is available for that).


def main() -> None:
    signal.signal(signal.SIGTERM, _request_shutdown)
    signal.signal(signal.SIGINT, _request_shutdown)

    r = get_redis()
    logger.info("notif-worker started, waiting for jobs on %s", QUEUE_KEY)
    while not _shutdown:
        try:
            item = r.blpop(QUEUE_KEY, timeout=BLPOP_TIMEOUT_SECONDS)
        except redis_lib.RedisError:
            logger.exception("redis error while polling queue, reconnecting")
            time.sleep(1)
            r = get_redis()
            continue
        if item is None:
            continue  # timeout, no job — loop back to check for shutdown
        _, raw = item
        try:
            process(json.loads(raw))
        except Exception:
            logger.exception("failed to process job: %s", raw)

    logger.info("notif-worker stopped")


if __name__ == "__main__":
    main()
