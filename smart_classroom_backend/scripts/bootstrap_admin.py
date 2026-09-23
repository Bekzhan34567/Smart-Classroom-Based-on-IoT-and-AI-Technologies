import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import models  # noqa: E402
from app.auth_utils import hash_password  # noqa: E402
from app.database import SessionLocal  # noqa: E402


def bootstrap_admin():
    db = SessionLocal()
    try:
        legacy_admin_email = "admin@smartclassroom.local"
        admin_email = "admin@smartclassroom.edu"

        legacy_admin = (
            db.query(models.User)
            .filter(models.User.email == legacy_admin_email)
            .first()
        )
        if legacy_admin is not None:
            conflict = (
                db.query(models.User)
                .filter(models.User.email == admin_email)
                .first()
            )
            if conflict is None:
                legacy_admin.email = admin_email
                db.commit()
                print(f"Updated legacy admin email to: {admin_email}")

        existing_admin = db.query(models.User).filter(models.User.email == admin_email).first()
        if existing_admin is not None:
            print(f"Admin already exists: {admin_email}")
            return

        admin = models.User(
            full_name="System Administrator",
            email=admin_email,
            password=hash_password("Admin12345!"),
            role="admin",
        )
        db.add(admin)
        db.commit()
        print("Bootstrap admin created successfully")
        print(f"Email: {admin_email}")
        print("Password: Admin12345!")
        print("Please change this password after first login.")
    finally:
        db.close()


if __name__ == "__main__":
    bootstrap_admin()
