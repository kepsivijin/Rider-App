#!/usr/bin/env python3
"""Test rural fare: bike ₹10/km, auto/car per person per km."""
import sys
import requests

BASE = "http://localhost:8001/api/v1"
CUSTOMER = "9876543210"
LOGIN_OTP = "123456"

POOTHURAI = (8.264, 77.138)
NITHIRAVILAI = (8.2739, 77.1436)


def login():
    requests.post(f"{BASE}/auth/send-otp", json={"phone_number": CUSTOMER}, timeout=30)
    r = requests.post(f"{BASE}/auth/verify-otp", json={"phone_number": CUSTOMER, "otp": LOGIN_OTP}, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]


def book(token, vehicle_type, passenger_count):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "pickup_latitude": POOTHURAI[0],
        "pickup_longitude": POOTHURAI[1],
        "pickup_address": "Poothurai (Pottur)",
        "dropoff_latitude": NITHIRAVILAI[0],
        "dropoff_longitude": NITHIRAVILAI[1],
        "dropoff_address": "Nithiravilai",
        "payment_method": "cash",
        "vehicle_type": vehicle_type,
        "passenger_count": passenger_count,
    }
    r = requests.post(f"{BASE}/rides/request", json=payload, headers=headers, timeout=30)
    return r


def main():
    print("=== Rural Fare Test ===\n")
    token = login()
    print("✓ Customer logged in\n")

    cases = [
        ("bike", 1, "~₹13"),
        ("auto", 1, "~₹10"),
        ("auto", 3, "~₹31"),
        ("car", 4, "~₹52"),
    ]

    for vehicle, pax, expected in cases:
        r = book(token, vehicle, pax)
        if r.status_code != 200:
            print(f"✗ {vehicle} {pax}pax: HTTP {r.status_code} {r.text[:120]}")
            return 1
        ride = r.json()
        km = ride["distance_km"]
        fare = ride["estimated_fare"]
        print(f"✓ {vehicle.upper()} · {pax} passenger(s): {km:.1f} km → ₹{round(fare)} (expected {expected})")

    print("\n=== ALL FARE TESTS PASSED ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
