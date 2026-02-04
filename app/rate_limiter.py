import time
from typing import Dict, Tuple
from datetime import datetime, timedelta

from app.config import get_settings

settings = get_settings()

# ===============================
# Redis setup (optional, safe)
# ===============================

USE_REDIS = bool(settings.enable_redis)
redis_client = None

if USE_REDIS:
    try:
        import redis  # lazy import

        redis_client = redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
            retry_on_timeout=True,
        )

        redis_client.ping()
        print("✅ Redis rate limiting enabled")

    except Exception as e:
        USE_REDIS = False
        redis_client = None
        print(f"⚠️ Redis unavailable, using in-memory limiter ({e})")

# ===============================
# In-memory fallback (DEV / FAILSAFE)
# ===============================

_user_requests: Dict[str, list] = {}


def check_rate_limit(user_id: str) -> Tuple[bool, int]:
    """
    Check if user has exceeded rate limit.

    Returns:
        (is_allowed: bool, remaining_requests: int)
    """

    window_seconds = settings.rate_limit_window_seconds
    max_requests = settings.rate_limit_per_user

    # ===============================
    # Redis-based rate limiting (PROD)
    # ===============================
    if USE_REDIS and redis_client:
        key = f"rate_limit:{user_id}"
        now = time.time()
        window_start = now - window_seconds

        try:
            pipe = redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            results = pipe.execute()

            request_count = results[1]

            if request_count >= max_requests:
                return False, 0

            redis_client.zadd(key, {str(now): now})
            redis_client.expire(key, window_seconds)

            remaining = max_requests - request_count - 1
            return True, remaining

        except Exception:
            # Redis failed mid-request → fallback
            pass

    # ===============================
    # In-memory fallback (SAFE)
    # ===============================
    now = datetime.utcnow()
    window_start = now - timedelta(seconds=window_seconds)

    if user_id not in _user_requests:
        _user_requests[user_id] = []

    _user_requests[user_id] = [
        t for t in _user_requests[user_id] if t > window_start
    ]

    if len(_user_requests[user_id]) >= max_requests:
        return False, 0

    _user_requests[user_id].append(now)
    remaining = max_requests - len(_user_requests[user_id])
    return True, remaining