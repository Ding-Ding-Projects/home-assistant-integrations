"""Pure helpers for GitHub Releases (no Home Assistant imports)."""

from __future__ import annotations

import re
from datetime import datetime

BASE_INTERVAL_HOURS = 6
MAX_INTERVAL_HOURS = 24
_REPO_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})/[A-Za-z0-9._-]{1,100}$")


def parse_repo(text: str) -> str:
    """Normalise and validate an owner/repo string."""
    value = text.strip()
    for prefix in ("https://github.com/", "http://github.com/", "github.com/"):
        if value.lower().startswith(prefix):
            value = value[len(prefix):]
    value = value.removesuffix(".git").strip("/")
    if not _REPO_RE.match(value):
        raise ValueError(f"not a valid owner/repo: {text!r}")
    return value


def parse_release(payload: dict) -> tuple[str, datetime | None]:
    """Return (tag, published_at) from a GitHub release JSON object."""
    tag = payload.get("tag_name")
    if not tag:
        raise ValueError("release has no tag_name")
    published = payload.get("published_at") or payload.get("created_at")
    when = None
    if published:
        when = datetime.fromisoformat(str(published).replace("Z", "+00:00"))
    return str(tag), when


def backoff_hours(consecutive_failures: int) -> int:
    """Return the polling interval after a number of rate-limit failures."""
    if consecutive_failures <= 0:
        return BASE_INTERVAL_HOURS
    return min(BASE_INTERVAL_HOURS * 2**consecutive_failures, MAX_INTERVAL_HOURS)


def is_rate_limited(status: int, remaining: str | None) -> bool:
    """Return True when a response means polling should back off."""
    if status == 429:
        return True
    return status == 403 and (remaining is None or remaining == "0")
