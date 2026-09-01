import random
from app.core.config import settings

DEV_PICKUP_OTP = "987653"


def generate_pickup_otp() -> str:
    """Customer tells this OTP to the driver at pickup (demo: 987653)."""
    if settings.DEBUG:
        return DEV_PICKUP_OTP
    return str(random.randint(100000, 999999))
