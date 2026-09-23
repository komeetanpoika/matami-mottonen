from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import AdminUser
from app.security import hash_password, verify_password


def ensure_owner(db: Session) -> None:
    if db.scalar(select(AdminUser.id).limit(1)) is None:
        db.add(
            AdminUser(
                email=settings.admin_email.strip().lower(),
                password_hash=hash_password(settings.admin_password),
            )
        )
        db.commit()


def authenticate(db: Session, email: str, password: str) -> AdminUser | None:
    user = db.scalar(select(AdminUser).where(AdminUser.email == email.strip().lower()))
    if verify_password(password, user.password_hash if user else None):
        return user
    return None
