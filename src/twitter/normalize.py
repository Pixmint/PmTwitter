import re
from dataclasses import dataclass

STATUS_RE = re.compile(
    r"https?://(?P<host>[^/]+)/(?P<user>[^/]+)/status/(?P<id>\d+)",
    re.IGNORECASE,
)

SUPPORTED_HOSTS = {
    "x.com",
    "twitter.com",
    "fxtwitter.com",
    "fixupx.com",
}


@dataclass
class NormalizedUrl:
    user: str
    status_id: str
    original_url: str
    normalized_url: str


def extract_status_urls(text: str) -> list[str]:
    return [m.group(0) for m in STATUS_RE.finditer(text)]


def normalize_status_url(url: str) -> NormalizedUrl | None:
    match = STATUS_RE.search(url)
    if not match:
        return None

    host = match.group("host").lower()
    user = match.group("user")
    status_id = match.group("id")
    if host not in SUPPORTED_HOSTS:
        return None

    normalized = f"https://x.com/{user}/status/{status_id}"
    return NormalizedUrl(user=user, status_id=status_id, original_url=url, normalized_url=normalized)
