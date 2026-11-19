import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

DEFAULT_ITERATIONS = 600_000
SESSION_LIFETIME_DAYS = 7


def hash_password(password: str, iterations: int = DEFAULT_ITERATIONS) -> str:
    """Hash a plaintext password using PBKDF2-HMAC-SHA256 with a cryptographically secure salt."""
    if not password:
        raise ValueError("Mật khẩu không được để trống.")
    salt = secrets.token_bytes(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return f"pbkdf2_sha256${iterations}${salt.hex()}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored PBKDF2 hash using constant-time comparison."""
    if not plain_password or not hashed_password:
        return False
    try:
        algorithm, iter_str, salt_hex, key_hex = hashed_password.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iter_str)
        salt = bytes.fromhex(salt_hex)
        expected_key = bytes.fromhex(key_hex)
    except (ValueError, AttributeError):
        return False

    computed_key = hashlib.pbkdf2_hmac(
        "sha256",
        plain_password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(computed_key, expected_key)


def generate_session_token() -> str:
    """Generate a high-entropy URL-safe session token for authentication cookies/headers."""
    return secrets.token_urlsafe(32)


def get_session_expiry(days: int = SESSION_LIFETIME_DAYS) -> datetime:
    """Return a timezone-aware UTC datetime when a new session should expire."""
    return datetime.now(UTC) + timedelta(days=days)
