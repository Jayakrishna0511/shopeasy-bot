"""Seed script for ShopEasy users and orders.

Idempotent: uses session.merge to update existing records or insert new ones.
Run from backend/: python scripts/make_orders.py
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

# Add backend directory to sys.path so app modules can be imported
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.db import SessionLocal
from app.models import Order, User

USERS_DATA = [
    {"id": "ravi", "name": "Ravi Kumar", "is_premium": True},
    {"id": "priya", "name": "Priya Sharma", "is_premium": False},
    {"id": "arjun", "name": "Arjun Reddy", "is_premium": False},
]

ORDERS_DATA = [
    # Ravi's orders (Hyderabad / South, premium member)
    {
        "id": "A1001",
        "user_id": "ravi",
        "item": "Wireless Earbuds",
        "price": 2499,
        "status": "delivered",
        "city": "Hyderabad",
        "eta_days": 0,
    },
    {
        "id": "A1002",
        "user_id": "ravi",
        "item": "Laptop 15-inch",
        "price": 54999,
        "status": "processing",
        "city": "Hyderabad",
        "eta_days": 2,
    },
    {
        "id": "A1003",
        "user_id": "ravi",
        "item": "Phone Case",
        "price": 499,
        "status": "shipped",
        "city": "Hyderabad",
        "eta_days": 1,
    },
    {
        "id": "A1004",
        "user_id": "ravi",
        "item": "USB-C Charger",
        "price": 799,
        "status": "delivered",
        "city": "Hyderabad",
        "eta_days": 0,
    },
    {
        "id": "A1005",
        "user_id": "ravi",
        "item": "Smartwatch",
        "price": 4500,
        "status": "processing",
        "city": "Bengaluru",
        "eta_days": 3,
    },
    {
        "id": "A1006",
        "user_id": "ravi",
        "item": "Bluetooth Speaker",
        "price": 1999,
        "status": "cancelled",
        "city": "Hyderabad",
        "eta_days": 0,
    },
    {
        "id": "A1007",
        "user_id": "ravi",
        "item": "USB-C Charger",
        "price": 799,
        "status": "shipped",
        "city": "Hyderabad",
        "eta_days": 2,
    },
    {
        "id": "A1008",
        "user_id": "ravi",
        "item": "Wireless Earbuds",
        "price": 2499,
        "status": "processing",
        "city": "Mumbai",
        "eta_days": 2,
    },
    # Priya's orders (Delhi / North, standard member)
    {
        "id": "B1001",
        "user_id": "priya",
        "item": "Smartwatch",
        "price": 4500,
        "status": "delivered",
        "city": "Delhi",
        "eta_days": 0,
    },
    {
        "id": "B1002",
        "user_id": "priya",
        "item": "Phone Case",
        "price": 499,
        "status": "processing",
        "city": "Delhi",
        "eta_days": 3,
    },
    {
        "id": "B1003",
        "user_id": "priya",
        "item": "Bluetooth Speaker",
        "price": 1999,
        "status": "shipped",
        "city": "Delhi",
        "eta_days": 2,
    },
    {
        "id": "B1004",
        "user_id": "priya",
        "item": "Laptop 15-inch",
        "price": 54999,
        "status": "delivered",
        "city": "Pune",
        "eta_days": 0,
    },
    {
        "id": "B1005",
        "user_id": "priya",
        "item": "USB-C Charger",
        "price": 799,
        "status": "cancelled",
        "city": "Delhi",
        "eta_days": 0,
    },
    {
        "id": "B1006",
        "user_id": "priya",
        "item": "Wireless Earbuds",
        "price": 2499,
        "status": "shipped",
        "city": "Delhi",
        "eta_days": 1,
    },
    {
        "id": "B1007",
        "user_id": "priya",
        "item": "Phone Case",
        "price": 499,
        "status": "delivered",
        "city": "Chennai",
        "eta_days": 0,
    },
    {
        "id": "B1008",
        "user_id": "priya",
        "item": "Bluetooth Speaker",
        "price": 1999,
        "status": "processing",
        "city": "Delhi",
        "eta_days": 4,
    },
    # Arjun's orders (Bengaluru / South, standard member)
    {
        "id": "C1001",
        "user_id": "arjun",
        "item": "Phone Case",
        "price": 499,
        "status": "delivered",
        "city": "Bengaluru",
        "eta_days": 0,
    },
    {
        "id": "C1002",
        "user_id": "arjun",
        "item": "Wireless Earbuds",
        "price": 2499,
        "status": "processing",
        "city": "Hyderabad",
        "eta_days": 2,
    },
    {
        "id": "C1003",
        "user_id": "arjun",
        "item": "USB-C Charger",
        "price": 799,
        "status": "shipped",
        "city": "Bengaluru",
        "eta_days": 1,
    },
    {
        "id": "C1004",
        "user_id": "arjun",
        "item": "Smartwatch",
        "price": 4500,
        "status": "cancelled",
        "city": "Bengaluru",
        "eta_days": 0,
    },
    {
        "id": "C1005",
        "user_id": "arjun",
        "item": "Bluetooth Speaker",
        "price": 1999,
        "status": "delivered",
        "city": "Mumbai",
        "eta_days": 0,
    },
    {
        "id": "C1006",
        "user_id": "arjun",
        "item": "Laptop 15-inch",
        "price": 54999,
        "status": "shipped",
        "city": "Bengaluru",
        "eta_days": 3,
    },
    {
        "id": "C1007",
        "user_id": "arjun",
        "item": "Wireless Earbuds",
        "price": 2499,
        "status": "delivered",
        "city": "Chennai",
        "eta_days": 0,
    },
    {
        "id": "C1008",
        "user_id": "arjun",
        "item": "Smartwatch",
        "price": 4500,
        "status": "processing",
        "city": "Bengaluru",
        "eta_days": 2,
    },
]


def seed_data() -> None:
    session = SessionLocal()
    try:
        # Seed users first (orders depend on user foreign keys)
        for user_dict in USERS_DATA:
            user = User(
                id=user_dict["id"],
                name=user_dict["name"],
                is_premium=user_dict["is_premium"],
            )
            session.merge(user)

        # Seed orders
        for order_dict in ORDERS_DATA:
            order = Order(
                id=order_dict["id"],
                user_id=order_dict["user_id"],
                item=order_dict["item"],
                price=order_dict["price"],
                status=order_dict["status"],
                city=order_dict["city"],
                eta_days=order_dict["eta_days"],
                created_at=datetime.now(timezone.utc),
            )
            session.merge(order)

        session.commit()
        print(f"Seeding completed successfully: {len(USERS_DATA)} users, {len(ORDERS_DATA)} orders.")
    except Exception as e:
        session.rollback()
        print(f"Error during seeding: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_data()
