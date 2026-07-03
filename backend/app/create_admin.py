"""
One-off CLI to create an admin user, since there's no public signup endpoint
(admin accounts should only ever be created by someone with server access).

Usage:
    python -m app.create_admin
"""
import getpass

from app.database import SessionLocal
from app.auth import hash_password
from app.models import AdminUser


def main():
    username = input("Admin username: ").strip()
    full_name = input("Full name: ").strip()
    password = getpass.getpass("Password: ")
    confirm = getpass.getpass("Confirm password: ")

    if password != confirm:
        print("Passwords do not match.")
        return
    if len(password) < 8:
        print("Password should be at least 8 characters.")
        return

    db = SessionLocal()
    try:
        existing = db.query(AdminUser).filter(AdminUser.username == username).first()
        if existing:
            print(f"An admin with username '{username}' already exists.")
            return

        admin = AdminUser(
            username=username,
            full_name=full_name or username,
            hashed_password=hash_password(password),
        )
        db.add(admin)
        db.commit()
        print(f"Admin user '{username}' created.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
