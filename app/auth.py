import os
from datetime import datetime, timedelta, timezone
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError
from passlib.context import CryptContext

# Lazy initialization of CryptContext to avoid passlib's internal bug detection issues
# The error occurs during module import when passlib tries to detect bcrypt backend issues
_pwd_context = None


def _get_pwd_context():
    """Get or create the password context (lazy initialization)."""
    global _pwd_context
    if _pwd_context is None:
        try:
            _pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        except ValueError as e:
            # If initialization fails due to bcrypt detection issues, try with explicit config
            # This can happen if passlib's internal bug detection uses a hash > 72 bytes
            _pwd_context = CryptContext(
                schemes=["bcrypt"],
                bcrypt__rounds=12,
                deprecated="auto",
            )
    return _pwd_context


JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALG = "HS256"
JWT_EXPIRE_MIN = 60 * 24 * 7  # 7 days


def hash_password(pw: str) -> str:
    """Hash a password using bcrypt."""
    return _get_pwd_context().hash(pw)


def verify_password(pw: str, pw_hash: str) -> bool:
    """Verify a password against its hash."""
    return _get_pwd_context().verify(pw, pw_hash)


def make_token(user_id: str) -> str:
    """Create a JWT token for a user."""
    exp = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MIN)
    return jwt.encode({"sub": user_id, "exp": exp}, JWT_SECRET, algorithm=JWT_ALG)


def decode_token(token: str) -> dict:
    """Decode and verify a JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        return payload
    except ExpiredSignatureError:
        raise ValueError("Token has expired")
    except JWTError:
        raise ValueError("Invalid token")
