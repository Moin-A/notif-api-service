"""JWT verification config.

reptrack signs push tokens with HS256 using its Rails secret_key_base
(see reptrack app/services/jwt_token_service.rb). notif must verify incoming
push tokens with the exact same secret + algorithm.

Both are injected from the `notif-secrets` Kubernetes secret; the defaults
below are for local dev only. JWT_SECRET must match your local Rails
secret_key_base — get it with:

    cd reptrack && bundle exec rails runner 'puts Rails.application.secret_key_base'
"""
import os

import jwt

JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")


class JWTService:
    def __init__(self, secret: str = JWT_SECRET, algorithm: str = JWT_ALGORITHM):
        self.secret = secret
        self.algorithm = algorithm

    def encode(self, payload: dict) -> str:
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    def decode(self, token: str) -> dict:
        return jwt.decode(token, self.secret, algorithms=[self.algorithm])
