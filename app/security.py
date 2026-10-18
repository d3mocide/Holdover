"""Password hashing, session tokens and login throttling. Standard library only (hashlib.scrypt)."""
import base64
import hashlib
import hmac
import re
import secrets
import time
from collections import defaultdict, deque

# scrypt: 16 MiB, ~50 ms on a laptop. Parameters are stored in each hash so they can be raised later.
_N, _R, _P = 2**14, 8, 1
USERNAME_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{2,31}$")
MIN_PASSWORD = 10


def _b64(b: bytes) -> str:
    return base64.b64encode(b).decode()


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P, maxmem=64 * 1024 * 1024, dklen=32)
    return f"scrypt${_N}${_R}${_P}${_b64(salt)}${_b64(dk)}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, n, r, p, salt, dk = stored.split("$")
        if scheme != "scrypt":
            return False
        calc = hashlib.scrypt(password.encode(), salt=base64.b64decode(salt), n=int(n), r=int(r), p=int(p),
                              maxmem=64 * 1024 * 1024, dklen=32)
        return hmac.compare_digest(calc, base64.b64decode(dk))
    except (ValueError, TypeError):
        return False


# Verifying against this when the username is unknown keeps "no such user" and "wrong password" the same speed.
_DUMMY = hash_password("not-a-real-password")


def burn_time(password: str) -> None:
    verify_password(password, _DUMMY)


def new_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def validate_username(name: str) -> str:
    name = (name or "").strip().lower()
    if not USERNAME_RE.match(name):
        raise ValueError("username must be 3-32 characters: letters, numbers, dot, dash or underscore")
    return name


def validate_password(pw: str) -> str:
    if len(pw or "") < MIN_PASSWORD:
        raise ValueError(f"password must be at least {MIN_PASSWORD} characters")
    if len(pw) > 200:
        raise ValueError("password too long")
    return pw


class Throttle:
    """Sliding-window failure counter, in memory. The app runs a single worker on purpose (the scheduler is
    in-process), so this holds; a restart clears it, which is acceptable for a handful of users."""

    def __init__(self, limit: int, window_s: int):
        self.limit, self.window = limit, window_s
        self.hits: dict[str, deque[float]] = defaultdict(deque)

    def _trim(self, key: str, now: float) -> deque[float]:
        q = self.hits[key]
        while q and now - q[0] > self.window:
            q.popleft()
        return q

    def blocked(self, key: str) -> int:
        """Seconds until the next attempt is allowed, or 0."""
        now = time.monotonic()
        q = self._trim(key, now)
        return int(self.window - (now - q[0])) + 1 if len(q) >= self.limit else 0

    def fail(self, key: str) -> None:
        now = time.monotonic()
        self._trim(key, now).append(now)

    def clear(self, key: str) -> None:
        self.hits.pop(key, None)


by_user = Throttle(limit=5, window_s=15 * 60)
by_ip = Throttle(limit=30, window_s=15 * 60)
