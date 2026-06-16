import hashlib
import hmac
import json
import logging
import time
from urllib.parse import parse_qsl

import jwt

from hub.config import BOT_TOKEN, JWT_SECRET

logger = logging.getLogger(__name__)


def verify_init_data(init_data: str) -> dict | None:
    """Verify Telegram WebApp initData and return user info."""
    try:
        parsed = dict(parse_qsl(init_data))
        received_hash = parsed.pop("hash", "")
        if not received_hash:
            return None

        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(parsed.items())
        )

        secret_key = hmac.new(
            b"WebAppData",
            BOT_TOKEN.encode("utf-8"),
            hashlib.sha256,
        ).digest()

        computed_hash = hmac.new(
            secret_key,
            data_check_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        if computed_hash != received_hash:
            logger.warning("initData hash mismatch")
            return None

        auth_date = int(parsed.get("auth_date", "0"))
        if time.time() - auth_date > 86400:
            logger.warning("initData expired")
            return None

        user = json.loads(parsed.get("user", "{}"))
        return user

    except Exception as e:
        logger.exception("initData verification failed: %s", e)
        return None


def create_token(user_id: int) -> str:
    """Create JWT for the TMA client session."""
    payload = {
        "user_id": user_id,
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def verify_token(token: str) -> dict | None:
    """Verify JWT and return payload."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        logger.warning("JWT expired")
        return None
    except jwt.InvalidTokenError:
        logger.warning("Invalid JWT")
        return None
