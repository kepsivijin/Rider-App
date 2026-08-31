#!/usr/bin/env python3
"""Seed test customer and driver for full flow testing."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.models.driver import Driver, VehicleType
from app.models.wallet import Wallet

CUSTOMER_PHONE = "9876543210"
DRIVER_PHONE = "9876543212"
ADMIN_PHONE = "9876543213"

def get_or_create_user(db, phone, name, role):
    user = db.query(User).filter(User.phone_number == phone).first()
    if user:
        user.role = role
        user.is_verified = True
        user.is_active = True
        print(f"  Updated existing user: {phone} ({role.value})")
    else:
        user = User(
            phone_number=phone,
            full_name=name,
            role=role,
            is_verified=True,
            is_active=True,
        )
        db.add(user)
        db.flush()
        db.add(Wallet(user_id=user.id, balance=0.0))
        print(f"  Created user: {phone} ({role.value})")
    return user


def main():
    db = SessionLocal()
    try:
        print("Seeding test users...")
        customer = get_or_create_user(db, CUSTOMER_PHONE, "Test Customer", UserRole.CUSTOMER)
        driver_user = get_or_create_user(db, DRIVER_PHONE, "Test Driver", UserRole.DRIVER)
        get_or_create_user(db, ADMIN_PHONE, "Admin User", UserRole.ADMIN)

        driver = db.query(Driver).filter(Driver.user_id == driver_user.id).first()
        if not driver:
            driver = Driver(
                user_id=driver_user.id,
                vehicle_type=VehicleType.BIKE,
                vehicle_number="TN-75-DV-9999",
                license_number="DL-TEST-999",
                license_expiry=datetime(2027, 12, 31),
                is_approved=True,
                is_online=False,
                current_latitude=8.2875,
                current_longitude=77.105,
                passenger_capacity=1,
            )
            db.add(driver)
            print("  Created driver profile (approved)")
        else:
            driver.is_approved = True
            driver.current_latitude = 8.2875
            driver.current_longitude = 77.105
            driver.vehicle_number = "TN-75-DV-9999"
            driver.passenger_capacity = driver.passenger_capacity or 1
            print("  Updated driver profile (approved)")

        db.commit()
        print("\nTest accounts ready:")
        print(f"  Customer: {CUSTOMER_PHONE} → http://localhost:3000/login")
        print(f"  Driver:   {DRIVER_PHONE} → http://localhost:3001/login")
        print(f"  Admin:    {ADMIN_PHONE} → http://localhost:3002/login")
        print("\nUse OTP from backend logs after login attempt.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
