from typing import Optional, Dict, Any
import json


async def send_push_notification(
    fcm_token: Optional[str],
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None
) -> bool:
    """In-app / FCM notification placeholder (logged for demo)."""
    token_preview = fcm_token[:20] if fcm_token else "in-app"
    print(f"PUSH NOTIFICATION to {token_preview}...")
    print(f"Title: {title}")
    print(f"Body: {body}")
    if data:
        print(f"Data: {json.dumps(data)}")
    return True


async def notify_driver_ride_request(
    fcm_token: str,
    ride_id: str,
    pickup_address: str,
    estimated_fare: float
) -> bool:
    """Notify driver about new ride request"""
    return await send_push_notification(
        fcm_token=fcm_token,
        title="New Ride Request!",
        body=f"Pickup: {pickup_address}\nFare: ₹{estimated_fare}",
        data={
            "type": "ride_request",
            "ride_id": ride_id
        }
    )


async def notify_customer_ride_accepted(
    fcm_token: Optional[str],
    ride_id: str,
    driver_name: str,
    vehicle_number: str,
    pickup_otp: str,
) -> bool:
    """Notify customer that driver accepted — includes pickup OTP."""
    return await send_push_notification(
        fcm_token=fcm_token,
        title="Driver Accepted!",
        body=(
            f"{driver_name} is coming ({vehicle_number}). "
            f"Your pickup OTP: {pickup_otp} — tell this to the driver."
        ),
        data={
            "type": "ride_accepted",
            "ride_id": ride_id,
            "pickup_otp": pickup_otp,
        }
    )


async def notify_ride_status_change(
    fcm_token: str,
    ride_id: str,
    status: str,
    message: str
) -> bool:
    """Generic ride status change notification"""
    return await send_push_notification(
        fcm_token=fcm_token,
        title=f"Ride {status.title()}",
        body=message,
        data={
            "type": "ride_status",
            "ride_id": ride_id,
            "status": status
        }
    )
