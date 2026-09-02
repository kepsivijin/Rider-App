"""Track per-driver ride rejections so declined requests stay hidden for that driver."""

import logging
from typing import Set
from uuid import UUID

from app.core.redis_client import redis_client

logger = logging.getLogger(__name__)

_REJECT_TTL_SECONDS = 86_400  # 24 hours

# Fast in-process fallback when Redis is slow or unavailable
_memory_rejections: dict[str, Set[str]] = {}


def _key(driver_id: UUID) -> str:
    return f"driver:rejected:{driver_id}"


def _decode_member(value) -> str:
    return value.decode() if isinstance(value, bytes) else str(value)


def get_rejected_ride_ids(driver_id: UUID) -> Set[str]:
    """All ride IDs this driver declined — one Redis round-trip max."""
    did = str(driver_id)
    rejected = set(_memory_rejections.get(did, set()))
    try:
        members = redis_client.smembers(_key(driver_id))
        rejected.update(_decode_member(m) for m in members)
    except Exception as exc:
        logger.warning("Redis reject lookup failed, using memory only: %s", exc)
    return rejected


def record_driver_rejection(driver_id: UUID, ride_id: UUID) -> None:
    did, rid = str(driver_id), str(ride_id)
    _memory_rejections.setdefault(did, set()).add(rid)
    try:
        key = _key(driver_id)
        redis_client.sadd(key, rid)
        redis_client.expire(key, _REJECT_TTL_SECONDS)
    except Exception as exc:
        logger.warning("Redis reject record failed, using memory only: %s", exc)


def is_rejected_by_driver(driver_id: UUID, ride_id: UUID) -> bool:
    return str(ride_id) in get_rejected_ride_ids(driver_id)
