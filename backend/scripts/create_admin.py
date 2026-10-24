import argparse
import os
import sys

# Ensure backend root is in Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.staff import Staff
from app.models.user import User
from app.services import activity_log


def create_or_update_admin(username: str, password: str, name: str = "Admin User"):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user:
            print(f"User '{username}' already exists. Updating password and ensuring admin role.")
            user.password_hash = hash_password(password)
            user.role = "admin"
            user.is_active = True
            if not user.staff_profile:
                staff = Staff(user_id=user.user_id, name=name)
                db.add(staff)
            else:
                user.staff_profile.name = name
            db.commit()
            print(f"Admin user '{username}' updated successfully.")
            return

        user = User(
            username=username,
            password_hash=hash_password(password),
            role="admin",
            is_active=True,
        )
        db.add(user)
        db.flush()

        staff = Staff(user_id=user.user_id, name=name)
        db.add(staff)
        db.flush()

        activity_log.record(
            db,
            user_id=user.user_id,
            action="create",
            entity_type="user",
            entity_id=user.user_id,
            details={"username": username, "role": "admin", "bootstrap": True},
        )

        db.commit()
        print(f"Admin user '{username}' created successfully (Staff ID: {staff.staff_id}).")
    except Exception as e:
        db.rollback()
        print(f"Error creating admin: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Bootstrap an initial administrator account for BloodLink.")
    parser.add_argument("--username", required=True, help="Admin username")
    parser.add_argument("--password", required=True, help="Admin password (min 8 chars)")
    parser.add_argument("--name", default="System Administrator", help="Admin staff display name")

    args = parser.parse_args()

    if len(args.password) < 8:
        print("Error: Password must be at least 8 characters long.", file=sys.stderr)
        sys.exit(1)

    create_or_update_admin(args.username, args.password, args.name)


if __name__ == "__main__":
    main()
