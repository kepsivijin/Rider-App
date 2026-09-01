import redis
from app.core.config import settings


def create_redis_client() -> redis.Redis:
    """Create Redis client with TLS support for Upstash (rediss://)."""
    url = settings.REDIS_URL.strip()
    kwargs = {"decode_responses": False}

    if url.startswith("rediss://"):
        kwargs["ssl_cert_reqs"] = None

    return redis.from_url(url, **kwargs)


redis_client = create_redis_client()
