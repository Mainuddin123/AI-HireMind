
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from backend.config import settings


# Initialize Argon2 password hashing
password_hash = PasswordHash.recommended()


# Hash a user's password
def hash_password(password: str) -> str:
    return password_hash.hash(password)


# Verify a password against its stored hash
def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:

    return password_hash.verify(
        plain_password,
        hashed_password
    )


# Generate JWT access token
def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None
) -> str:

    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(
            minutes=settings.access_token_expire_minutes
        )
    )

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    })

    encoded_token = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )

    return encoded_token


# Decode and validate JWT access token
def decode_access_token(token: str) -> dict:

    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm]
    )

    return payload
