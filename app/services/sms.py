import random
import redis
from typing import Optional
from app.core.config import settings
from app.utils.phone import normalize_phone

redis_client = redis.from_url(settings.REDIS_URL)

OTP_EXPIRY_SECONDS = 900  # 15 minutes
DEV_OTP = "123456"


def generate_otp() -> str:
    """Generate a 6-digit OTP"""
    if settings.DEBUG:
        return DEV_OTP
    return str(random.randint(100000, 999999))


def store_otp(phone_number: str, otp: str) -> None:
    """Store OTP in Redis with expiry"""
    phone = normalize_phone(phone_number)
    key = f"otp:{phone}"
    redis_client.setex(key, OTP_EXPIRY_SECONDS, otp)


def verify_otp(phone_number: str, otp: str) -> bool:
    """Verify OTP against stored value"""
    phone = normalize_phone(phone_number)
    otp_clean = (otp or '').strip()

    if settings.DEBUG and otp_clean == DEV_OTP:
        return True

    key = f"otp:{phone}"
    stored_otp = redis_client.get(key)

    if stored_otp is None:
        return False

    if stored_otp.decode() == otp_clean:
        redis_client.delete(key)
        return True

    return False


async def send_otp(phone_number: str) -> str:
    """Send OTP (dev: always 123456 when DEBUG=True)"""
    phone = normalize_phone(phone_number)
    otp = generate_otp()
    store_otp(phone, otp)

    print(f"OTP for {phone}: {otp}")

    return otp
