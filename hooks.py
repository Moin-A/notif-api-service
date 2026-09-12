import json
import sys

import dredd_hooks as hooks

from app.auth import JWTService

TXN_202 = "/notifications > Enqueue Notification > 202 > application/json"
TXN_401 = "/notifications > Enqueue Notification > 401 > application/json"
TXN_422 = "/notifications > Enqueue Notification > 422 > application/json"


@hooks.before_all
def log_transaction_names(transactions):
    for t in transactions:
        print(f"[hook] transaction name: {t['name']}", file=sys.stderr)

VALID_BODY = {
    "endpoint": "https://fcm.googleapis.com/fcm/send/abc123",
    "expirationTime": None,
    "keys": {"p256dh": "BNxxxx", "auth": "k9xxxx"},
}


@hooks.before(TXN_202)
def valid_jwt_for_202(transaction):
    token = JWTService().encode({"user_id": 42})
    transaction["request"]["headers"]["Authorization"] = f"Bearer {token}"


@hooks.before(TXN_401)
def invalid_jwt_gets_401(transaction):
    transaction["request"]["body"] = json.dumps(VALID_BODY)
    transaction["request"]["headers"]["Content-Type"] = "application/json"
    transaction["request"]["headers"]["Authorization"] = "Bearer invalid.token.here"

    transaction["expected"]["statusCode"] = "401"
    transaction["expected"]["body"] = '{"detail": "invalid token"}'
    transaction["expected"].pop("bodySchema", None)


@hooks.before(TXN_422)
def valid_jwt_gets_202(transaction):
    token = JWTService().encode({"user_id": 42})

    transaction["request"]["body"] = json.dumps(VALID_BODY)
    transaction["request"]["headers"]["Content-Type"] = "application/json"
    transaction["request"]["headers"]["Authorization"] = f"Bearer {token}"

    transaction["expected"]["statusCode"] = "202"
    transaction["expected"]["body"] = '{"status": "queued"}'
    transaction["expected"].pop("bodySchema", None)
