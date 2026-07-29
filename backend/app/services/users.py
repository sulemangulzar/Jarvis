from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


def save_microsoft_user(
    db: Session,
    microsoft_oid: str,
    email: str | None,
    name: str | None,
) -> User:
    """Create a Microsoft user the first time, then update their profile."""
    user = db.scalar(select(User).where(User.microsoft_oid == microsoft_oid))

    if user is None:
        user = User(
            microsoft_oid=microsoft_oid,
            email=email,
            name=name,
        )
        db.add(user)
    else:
        user.email = email
        user.name = name

    db.commit()
    db.refresh(user)
    return user
