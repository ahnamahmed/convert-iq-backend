import json
from typing import Optional
from app.config import get_settings

settings = get_settings()

USE_REDIS = False
redis_client = None

_memory_cache: dict[str, str] = {}

# ===============================
# Redis Initialization
# ===============================
if settings.enable_redis:
    try:
        import redis  # lazy import

        redis_client = redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        redis_client.ping()
        USE_REDIS = True
        print("✅ Redis cache enabled")

    except Exception as e:
        USE_REDIS = False
        redis_client = None
        print(f"⚠️ Redis cache unavailable, using memory cache ({e})")


def _make_key(user_id: str, product_url: str) -> str:
    return f"prompt1:{user_id}:{product_url}"


def cache_prompt1_output(user_id: str, product_url: str, output: dict) -> None:
    cache_key = _make_key(user_id, product_url)
    cache_data = json.dumps(output)

    if USE_REDIS and redis_client:
        try:
            redis_client.setex(cache_key, 86400, cache_data)  # 24h TTL
        except Exception:
            # fail silently → fallback
            _memory_cache[cache_key] = cache_data
    else:
        _memory_cache[cache_key] = cache_data


def get_cached_prompt1_output(
    user_id: str, product_url: str
) -> Optional[dict]:
    cache_key = _make_key(user_id, product_url)

    if USE_REDIS and redis_client:
        try:
            cached_data = redis_client.get(cache_key)
        except Exception:
            cached_data = _memory_cache.get(cache_key)
    else:
        cached_data = _memory_cache.get(cache_key)

    return json.loads(cached_data) if cached_data else None