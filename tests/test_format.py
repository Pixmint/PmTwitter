from datetime import datetime, timezone

from twitter.models import TweetData
from utils.text_format import build_full_text


def test_build_full_text():
    tweet = TweetData(
        display_name="Автор",
        username="tester",
        tweet_url="https://x.com/tester/status/1",
        created_at=datetime(2024, 1, 1, 10, 30, tzinfo=timezone.utc),
        text="Привет",
        replies="1",
        reposts="2",
        likes="3",
        views="4",
    )
    parts = build_full_text(tweet, include_translation=False)
    assert len(parts) == 1
    assert "💬 1" in parts[0]
