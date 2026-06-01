from database.database import SessionLocal
from database.models import User, WardrobeItem, Outfit

db = SessionLocal()

print("=== ALL USERS ===")
users = db.query(User).all()
for user in users:
    print(f"ID: {user.id}, Name: {user.name}, Email: {user.email}")
    print(f"  Body Shape: {user.body_shape}, Undertone: {user.undertone}, BMI: {user.bmi}")
    print(f"  Created: {user.created_at}\n")

print(f"\nTotal users: {len(users)}")

db.close()