"""Capability URLs for generated workshop files.

Generated creative outputs stay on disk under ``static/generated`` but are no longer
readable by URL alone: every response that mentions such a file gets a short-lived
signature, and the static route refuses unsigned reads.
"""
import hashlib
import hmac
import os
import posixpath
import re
import time
from pathlib import Path
from urllib.parse import unquote

GENERATED_PREFIX = "/static/generated/"
SECRET_PATH = Path(__file__).resolve().parents[2] / "data" / "file_url_secret.key"
TTL_SECONDS = 12 * 3600
_NAME = r"[A-Za-z0-9._%\-]{1,200}"
# A generated URL is only rewritten when the name ends cleanly: no trailing name character
# (that would let backtracking sign a truncated path) and no existing query string.
_URL_IN_JSON = re.compile((r"/static/generated/" + _NAME + r"(?![A-Za-z0-9._%\-?])").encode(), re.ASCII)
_QUERY = re.compile(r"^exp=(\d+)&sig=([0-9a-f]{64})$")


def _secret() -> bytes:
    SECRET_PATH.parent.mkdir(parents=True, exist_ok=True)
    if SECRET_PATH.exists():
        return SECRET_PATH.read_bytes()
    # Concurrent workers on a fresh install must not each mint their own key.
    try:
        with open(os.open(SECRET_PATH, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), "wb") as handle:
            handle.write(os.urandom(32))
    except FileExistsError:
        pass
    return SECRET_PATH.read_bytes()


def _signature(path: str, expires: int) -> str:
    return hmac.new(_secret(), f"{path}|{expires}".encode(), hashlib.sha256).hexdigest()


def normalize_path(path: str) -> str:
    """Collapse duplicate slashes and resolve ``..`` the way StaticFiles does.

    The guard in ``main.py`` and the signed URLs must agree on one spelling of a file path,
    otherwise ``/static//generated/x`` or ``/static/uploads/../generated/x`` reaches the bytes
    without a signature even though the plain form is refused.
    """
    return posixpath.normpath(re.sub(r"/{2,}", "/", unquote(path)))


def signed_url(url: str, now: int | None = None) -> str:
    if not url.startswith(GENERATED_PREFIX) or "?exp=" in url:
        return url
    expires = (now if now is not None else int(time.time())) + TTL_SECONDS
    return f"{url}?exp={expires}&sig={_signature(url, expires)}"


def split_signature(url: str) -> tuple[str, str]:
    path, _, query = url.partition("?")
    return path, query


def verify(path: str, query: str, now: int | None = None) -> bool:
    match = _QUERY.fullmatch(query or "")
    if not match or not path.startswith(GENERATED_PREFIX):
        return False
    expires = int(match.group(1))
    if expires < (now if now is not None else int(time.time())):
        return False
    return hmac.compare_digest(match.group(2), _signature(path, expires))


def sign_json(body: bytes) -> bytes:
    """Rewrite every generated file URL in a JSON response body with a signed one."""
    if GENERATED_PREFIX not in body.decode("utf-8", "ignore"):
        return body
    # One expiry per response keeps two fields that name the same file byte-identical.
    now = int(time.time())
    return _URL_IN_JSON.sub(lambda match: signed_url(match.group().decode(), now).encode(), body)
