from cryptography.fernet import Fernet, InvalidToken
from msal import SerializableTokenCache
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.token_cache import MicrosoftTokenCache


def _encrypt(value: str, settings: Settings) -> str:
    cipher = Fernet(settings.token_encryption_key.encode())
    return cipher.encrypt(value.encode()).decode()


def _decrypt(value: str, settings: Settings) -> str:
    cipher = Fernet(settings.token_encryption_key.encode())
    try:
        return cipher.decrypt(value.encode()).decode()
    except InvalidToken as error:
        raise ValueError("The stored Microsoft token cache cannot be decrypted") from error


def save_token_cache(
    db: Session,
    user_id: int,
    cache: SerializableTokenCache,
    settings: Settings,
) -> None:
    """Encrypt and save the MSAL cache for one user."""
    saved_cache = db.scalar(
        select(MicrosoftTokenCache).where(MicrosoftTokenCache.user_id == user_id)
    )
    encrypted_cache = _encrypt(cache.serialize(), settings)

    if saved_cache is None:
        saved_cache = MicrosoftTokenCache(
            user_id=user_id,
            encrypted_cache=encrypted_cache,
        )
        db.add(saved_cache)
    else:
        saved_cache.encrypted_cache = encrypted_cache

    db.commit()


def delete_token_cache(db: Session, user_id: int) -> None:
    db.execute(
        delete(MicrosoftTokenCache).where(MicrosoftTokenCache.user_id == user_id)
    )
    db.commit()


def load_token_cache(
    db: Session,
    user_id: int,
    settings: Settings,
) -> SerializableTokenCache | None:
    saved_cache = db.scalar(
        select(MicrosoftTokenCache).where(MicrosoftTokenCache.user_id == user_id)
    )
    if saved_cache is None:
        return None

    cache = SerializableTokenCache()
    cache.deserialize(_decrypt(saved_cache.encrypted_cache, settings))
    return cache
