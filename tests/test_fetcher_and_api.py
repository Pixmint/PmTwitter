import asyncio

import pytest

from src.twitter.fetcher import MediaTooLargeError, _download_media_once
from src.twitter.parser_api import parse_tweet_api


class FakeStreamResponse:
    def __init__(self, status_code=200, chunks=None, headers=None):
        self.status_code = status_code
        self._chunks = chunks or []
        self.headers = headers or {}
        self.request = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def aiter_bytes(self):
        for chunk in self._chunks:
            yield chunk


class FakeClient:
    def __init__(self, response):
        self.response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def stream(self, method, url, headers):
        return self.response


def test_download_media_rejects_large_content_length(monkeypatch):
    response = FakeStreamResponse(headers={"Content-Length": "11"})
    monkeypatch.setattr("src.twitter.fetcher.httpx.AsyncClient", lambda *args, **kwargs: FakeClient(response))

    with pytest.raises(MediaTooLargeError):
        asyncio.run(_download_media_once("https://example.com/file.jpg", {}, max_bytes=10))


def test_download_media_rejects_stream_that_exceeds_limit(monkeypatch):
    response = FakeStreamResponse(chunks=[b"12345", b"67890", b"x"])
    monkeypatch.setattr("src.twitter.fetcher.httpx.AsyncClient", lambda *args, **kwargs: FakeClient(response))

    with pytest.raises(MediaTooLargeError):
        asyncio.run(_download_media_once("https://example.com/file.jpg", {}, max_bytes=10))


def test_parse_tweet_api_minimal_payload():
    tweet = parse_tweet_api(
        {
            "tweet": {
                "text": "Hello from API",
                "created_at": "2026-02-14T12:19:00Z",
                "author": {"name": "Display", "screen_name": "user"},
                "media": {"photos": [{"url": "https://example.com/photo.jpg"}]},
                "stats": {"likes": 12, "retweets": "1.5K", "views": "2M"},
            }
        },
        "https://x.com/user/status/1",
    )

    assert tweet is not None
    assert tweet.display_name == "Display"
    assert tweet.username == "user"
    assert tweet.text == "Hello from API"
    assert tweet.media[0].url == "https://example.com/photo.jpg"
    assert tweet.stats.likes == 12
    assert tweet.stats.reposts == 1500
    assert tweet.stats.views == 2_000_000
