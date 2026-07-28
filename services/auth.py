from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from models.auth import RefreshToken, User


def find_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def create_user(db: Session, email: str, password: str) -> User:
    user = User(email=email, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = find_user_by_email(db, email)
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user


def create_token_pair(db: Session, user: User) -> tuple[str, str]:
    access_token = create_access_token(user.id)
    refresh_token, token_id, expires_at = create_refresh_token(user.id)

    db.add(
        RefreshToken(
            token_id=token_id,
            user_id=user.id,
            expires_at=expires_at,
        )
    )
    db.commit()
    return access_token, refresh_token


def find_refresh_token(db: Session, token_id: str) -> RefreshToken | None:
    return db.scalar(
        select(RefreshToken).where(RefreshToken.token_id == token_id)
    )


def rotate_refresh_token(
    db: Session, old_token: RefreshToken, user: User
) -> tuple[str, str]:
    db.delete(old_token)
    db.flush()

    access_token = create_access_token(user.id)
    refresh_token, token_id, expires_at = create_refresh_token(user.id)
    db.add(
        RefreshToken(
            token_id=token_id,
            user_id=user.id,
            expires_at=expires_at,
        )
    )
    db.commit()
    return access_token, refresh_token


def revoke_all_user_tokens(db: Session, user_id: int) -> None:
    db.execute(delete(RefreshToken).where(RefreshToken.user_id == user_id))
    db.commit()
