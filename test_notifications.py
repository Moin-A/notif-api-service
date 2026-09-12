from app.auth import JWTService
from app.models import Recipient, Subscription

VALID_BODY = {
    "endpoint": "https://fcm.googleapis.com/fcm/send/abc123",
    "expirationTime": None,
    "keys": {"p256dh": "BNxxxx", "auth": "k9xxxx"},
}


def _auth_headers():
    token = JWTService().encode({"user_id": 42})
    return {"Authorization": f"Bearer {token}"}


def test_post_notification_returns_202(client):
    resp = client.post("/notifications", json=VALID_BODY, headers=_auth_headers())
    assert resp.status_code == 202
    assert resp.json() == {"status": "queued"}


def test_enqueue_saves_subscription_to_db(client, db_session):
    client.post("/notifications", json=VALID_BODY, headers=_auth_headers())

    sub = db_session.query(Subscription).filter_by(endpoint=VALID_BODY["endpoint"]).first()
    assert sub is not None
    assert sub.p256dh == "BNxxxx"
    assert sub.auth == "k9xxxx"
    assert sub.expiration_time is None

    recipient = db_session.get(Recipient, sub.device.recipient_id)
    assert recipient.external_id == "42"
