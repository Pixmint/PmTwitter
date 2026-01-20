from pathlib import Path

from twitter.parser import parse_tweet


def test_parse_stats_and_poll():
    html = Path("tests/data/sample_tweet.html").read_text(encoding="utf8")
    tweet = parse_tweet(html, "https://x.com/tester/status/1")
    assert tweet.replies == "12"
    assert tweet.reposts == "5"
    assert tweet.likes == "100"
    assert tweet.views == "2000"
    assert tweet.poll is not None
    assert tweet.poll.question == "Ваш выбор?"
