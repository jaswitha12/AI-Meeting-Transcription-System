
import sqlite3
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from .database import get_connection


def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256."""
    salt = secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        310_000,
    ).hex()

    return f"{salt}${password_hash}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against its stored salted hash."""
    try:
        salt, expected_hash = stored_hash.split("$", 1)

        actual_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            310_000,
        ).hex()

        return hmac.compare_digest(actual_hash, expected_hash)

    except (ValueError, TypeError):
        return False


def register_user(email: str, password: str) -> int:
    """Create a user account and return its ID."""
    email = email.strip().lower()

    if not email or "@" not in email:
        raise ValueError("Enter a valid email address.")

    if len(password) < 8:
        raise ValueError("Password must contain at least 8 characters.")

    password_hash = hash_password(password)
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO users (email, password_hash)
            VALUES (?, ?)
            """,
            (email, password_hash),
        )

        connection.commit()
        return cursor.lastrowid

    except sqlite3.IntegrityError:
        raise ValueError("An account with this email already exists.")

    finally:
        connection.close()


def authenticate_user(email: str, password: str):
    """Return safe user details if the credentials are valid."""
    email = email.strip().lower()
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id, email, password_hash
            FROM users
            WHERE email = ?
            """,
            (email,),
        )

        user = cursor.fetchone()

        if not user or not verify_password(
            password, user["password_hash"]
        ):
            return None

        return {
            "id": user["id"],
            "email": user["email"],
        }

    finally:
        connection.close()

def create_session(user_id: int) -> str:
    """Create a random session token and store only its hash."""
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

    now = datetime.now(timezone.utc)
    expires_at = (now + timedelta(hours=12)).isoformat()

    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO sessions (user_id, token_hash, expires_at)
            VALUES (?, ?, ?)
            """,
            (user_id, token_hash, expires_at),
        )
        connection.commit()
        return token
    finally:
        connection.close()


def get_user_from_token(token: str):
    """Return the session owner's details if the token is valid."""
    if not token:
        return None

    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    now = datetime.now(timezone.utc).isoformat()

    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT users.id, users.email
            FROM sessions
            JOIN users ON users.id = sessions.user_id
            WHERE sessions.token_hash = ?
              AND sessions.expires_at > ?
            """,
            (token_hash, now),
        ).fetchone()

        if row is None:
            return None

        return {"id": row["id"], "email": row["email"]}
    finally:
        connection.close()


def delete_session(token: str) -> None:
    """Revoke a session token."""
    if not token:
        return

    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    connection = get_connection()

    try:
        connection.execute(
            "DELETE FROM sessions WHERE token_hash = ?",
            (token_hash,),
        )
        connection.commit()
    finally:
        connection.close()

