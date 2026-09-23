import hmac
import time
from hashlib import sha256


def sign(payload: bytes, secret: str, ts: int | None = None) -> str:
    ts = ts or int(time.time())
    mac = hmac.new(secret.encode(), f"{ts}.".encode() + payload, sha256).hexdigest()
    return f"t={ts},v1={mac}"
