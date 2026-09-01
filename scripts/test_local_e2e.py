#!/usr/bin/env python3
"""Local E2E test: customer book → driver accept → OTP verify → complete → rating."""
import sys
import requests

BASE = "http://localhost:8001/api/v1"
CUSTOMER = "9876543210"
DRIVER = "9876543212"
LOGIN_OTP = "123456"
PICKUP_OTP = "987653"


def login(phone):
    r = requests.post(f"{BASE}/auth/send-otp", json={"phone_number": phone}, timeout=30)
    r.raise_for_status()
    r = requests.post(f"{BASE}/auth/verify-otp", json={"phone_number": phone, "otp": LOGIN_OTP}, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]


def main():
    print("=== Local E2E Test ===\n")
    customer_token = login(CUSTOMER)
    driver_token = login(DRIVER)
    print("✓ Customer & driver login")

    headers_c = {"Authorization": f"Bearer {customer_token}"}
    headers_d = {"Authorization": f"Bearer {driver_token}"}

    # Book ride
    ride_payload = {
        "pickup_latitude": 8.264,
        "pickup_longitude": 77.138,
        "pickup_address": "Poothurai (Pottur)",
        "dropoff_latitude": 8.261,
        "dropoff_longitude": 77.1431,
        "dropoff_address": "St Thomas Forane Church, Thoothoor",
        "payment_method": "cash",
        "vehicle_type": "auto",
        "passenger_count": 2,
    }
    r = requests.post(f"{BASE}/rides/request", json=ride_payload, headers=headers_c, timeout=30)
    r.raise_for_status()
    ride = r.json()
    ride_id = ride["id"]
    print(f"✓ Ride booked: {ride_id}")

    # Driver online (if needed)
    requests.patch(f"{BASE}/drivers/me/status", json={"is_online": True}, headers=headers_d, timeout=30)

    # Accept
    r = requests.post(f"{BASE}/rides/{ride_id}/accept", headers=headers_d, timeout=30)
    r.raise_for_status()
    accepted = r.json()
    assert accepted["status"] == "accepted"
    print("✓ Driver accepted ride")

    # Customer sees pickup OTP
    r = requests.get(f"{BASE}/rides/{ride_id}", headers=headers_c, timeout=30)
    r.raise_for_status()
    customer_view = r.json()
    assert customer_view.get("pickup_otp") == PICKUP_OTP, f"Expected OTP {PICKUP_OTP}, got {customer_view.get('pickup_otp')}"
    print(f"✓ Customer pickup OTP: {customer_view['pickup_otp']}")

    # Driver cannot see OTP
    r = requests.get(f"{BASE}/rides/{ride_id}", headers=headers_d, timeout=30)
    driver_view = r.json()
    assert driver_view.get("pickup_otp") is None, "Driver should not see pickup OTP"
    print("✓ Driver cannot see customer OTP")

    # Start without OTP should fail
    r = requests.post(f"{BASE}/rides/{ride_id}/start", headers=headers_d, timeout=30)
    assert r.status_code == 400, "Start should fail without OTP verify"
    print("✓ Start blocked without OTP verify")

    # Wrong OTP
    r = requests.post(f"{BASE}/rides/{ride_id}/verify-pickup", json={"pickup_otp": "000000"}, headers=headers_d, timeout=30)
    assert r.status_code == 400
    print("✓ Wrong OTP rejected")

    # Verify correct OTP
    r = requests.post(f"{BASE}/rides/{ride_id}/verify-pickup", json={"pickup_otp": PICKUP_OTP}, headers=headers_d, timeout=30)
    r.raise_for_status()
    assert r.json()["pickup_verified"] is True
    print(f"✓ Pickup OTP verified: {PICKUP_OTP}")

    # Start ride
    r = requests.post(f"{BASE}/rides/{ride_id}/start", headers=headers_d, timeout=30)
    r.raise_for_status()
    assert r.json()["status"] == "started"
    print("✓ Ride started")

    # Complete ride
    r = requests.post(f"{BASE}/rides/{ride_id}/complete", headers=headers_d, timeout=30)
    r.raise_for_status()
    completed = r.json()
    assert completed["status"] == "completed"
    driver_user_id = completed["driver_user_id"]
    print("✓ Ride completed")

    # Rating before complete would fail - already completed, should work
    r = requests.post(
        f"{BASE}/ratings",
        json={"ride_id": ride_id, "to_user_id": driver_user_id, "rating": 5, "comment": "Great driver!"},
        headers=headers_c,
        timeout=30,
    )
    if r.status_code == 400 and "already rated" in r.json().get("detail", "").lower():
        print("✓ Rating already exists (from prior test) — OK")
    else:
        r.raise_for_status()
        print("✓ Rating submitted")

    # Health check
    r = requests.get("http://localhost:8001/health", timeout=10)
    assert r.json()["status"] == "healthy"
    print("✓ Health check OK")

    print("\n=== ALL LOCAL TESTS PASSED ===")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n✗ FAILED: {e}")
        sys.exit(1)
