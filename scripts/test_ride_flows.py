#!/usr/bin/env python3
"""Test now ride, scheduled ride, driver accept, and admin visibility."""
import sys
from datetime import datetime, timedelta, timezone

import requests

BASE = "http://localhost:8001/api/v1"
CUSTOMER = "9876543210"
DRIVER = "9876543212"
ADMIN = "9876543213"
LOGIN_OTP = "123456"
PICKUP_OTP = "987653"

POOTHURAI = {
    "pickup_latitude": 8.264,
    "pickup_longitude": 77.138,
    "pickup_address": "Poothurai (Pottur)",
}
NITHIRAVILAI = {
    "dropoff_latitude": 8.2739,
    "dropoff_longitude": 77.1436,
    "dropoff_address": "Nithiravilai",
}


def login(phone):
    r = requests.post(f"{BASE}/auth/send-otp", json={"phone_number": phone}, timeout=30)
    r.raise_for_status()
    r = requests.post(f"{BASE}/auth/verify-otp", json={"phone_number": phone, "otp": LOGIN_OTP}, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]


def ride_payload(**extra):
    return {
        **POOTHURAI,
        **NITHIRAVILAI,
        "payment_method": "cash",
        "vehicle_type": "auto",
        "passenger_count": 2,
        **extra,
    }


def main():
    print("=== Ride Flow Test: Poothurai → Nithiravilai ===\n")
    customer_token = login(CUSTOMER)
    driver_token = login(DRIVER)
    admin_token = login(ADMIN)
    print("✓ Customer, driver, admin logged in")

    headers_c = {"Authorization": f"Bearer {customer_token}"}
    headers_d = {"Authorization": f"Bearer {driver_token}"}
    headers_a = {"Authorization": f"Bearer {admin_token}"}

    # --- Scheduled ride (future) ---
    scheduled_at = (datetime.now(timezone.utc) + timedelta(hours=2)).replace(microsecond=0).isoformat()
    r = requests.post(
        f"{BASE}/rides/request",
        json=ride_payload(scheduled_at=scheduled_at),
        headers=headers_c,
        timeout=30,
    )
    r.raise_for_status()
    scheduled_ride = r.json()
    scheduled_id = scheduled_ride["id"]
    assert scheduled_ride.get("scheduled_at"), "Scheduled ride missing scheduled_at"
    print(f"✓ Scheduled ride booked: {scheduled_id} at {scheduled_ride['scheduled_at']}")

    # Scheduled ride should NOT appear for driver pending list yet
    requests.patch(f"{BASE}/drivers/me/status", json={"is_online": True}, headers=headers_d, timeout=30)
    r = requests.get(f"{BASE}/rides/pending", headers=headers_d, timeout=30)
    r.raise_for_status()
    pending_ids = [x["id"] for x in r.json()]
    assert scheduled_id not in pending_ids, "Future scheduled ride should not be in driver pending list"
    print("✓ Scheduled ride hidden from driver until time")

    # --- Now ride ---
    r = requests.post(f"{BASE}/rides/request", json=ride_payload(), headers=headers_c, timeout=30)
    r.raise_for_status()
    now_ride = r.json()
    now_id = now_ride["id"]
    assert now_ride["status"] == "requested"
    print(f"✓ Now ride booked: {now_id} ({POOTHURAI['pickup_address']} → {NITHIRAVILAI['dropoff_address']})")

    # Driver sees now ride
    r = requests.get(f"{BASE}/rides/pending", headers=headers_d, timeout=30)
    r.raise_for_status()
    pending_ids = [x["id"] for x in r.json()]
    assert now_id in pending_ids, "Now ride should appear in driver pending list"
    print("✓ Now ride visible to driver")

    # Driver accepts
    r = requests.post(f"{BASE}/rides/{now_id}/accept", headers=headers_d, timeout=30)
    r.raise_for_status()
    accepted = r.json()
    assert accepted["status"] == "accepted"
    print("✓ Driver accepted now ride")

    # Admin sees both rides
    r = requests.get(f"{BASE}/admin/rides", headers=headers_a, timeout=30)
    r.raise_for_status()
    admin_rides = r.json()
    admin_ids = {x["id"] for x in admin_rides}
    assert now_id in admin_ids, "Now ride missing from admin panel"
    assert scheduled_id in admin_ids, "Scheduled ride missing from admin panel"
    print("✓ Both rides visible on admin panel")

    now_admin = next(x for x in admin_rides if x["id"] == now_id)
    sched_admin = next(x for x in admin_rides if x["id"] == scheduled_id)
    assert now_admin["status"] == "accepted"
    assert sched_admin["status"] == "requested"
    assert "Poothurai" in now_admin["pickup_address"]
    assert "Nithiravilai" in now_admin["dropoff_address"]
    print(f"✓ Admin now ride: {now_admin['status']} | scheduled: {sched_admin['status']}")

    # Complete now ride flow (OTP → start → complete)
    r = requests.get(f"{BASE}/rides/{now_id}", headers=headers_c, timeout=30)
    assert r.json().get("pickup_otp") == PICKUP_OTP
    requests.post(f"{BASE}/rides/{now_id}/verify-pickup", json={"pickup_otp": PICKUP_OTP}, headers=headers_d, timeout=30).raise_for_status()
    requests.post(f"{BASE}/rides/{now_id}/start", headers=headers_d, timeout=30).raise_for_status()
    requests.post(f"{BASE}/rides/{now_id}/complete", headers=headers_d, timeout=30).raise_for_status()
    print("✓ Now ride completed (pickup OTP verified)")

    print("\n=== ALL RIDE FLOW TESTS PASSED ===")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n✗ FAILED: {e}")
        sys.exit(1)
