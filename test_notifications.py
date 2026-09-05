def test_post_notification_returns_202(client):
    resp = client.post(
        "/notifications",
        json={
            "endpoint": "https://fcm.googleapis.com/fcm/send/abc123",
            "expirationTime": None,
            "keys": {"p256dh": "BNxxxx", "auth": "k9xxxx"},
        },
    )
    assert resp.status_code == 202
    assert resp.json() == {"status": "queued"}
