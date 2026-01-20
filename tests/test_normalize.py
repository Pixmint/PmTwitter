from twitter.normalize import normalize_status_url


def test_normalize_status_url():
    url = "https://x.com/user/status/1234567890"
    normalized = normalize_status_url(url)
    assert normalized is not None
    assert normalized.normalized_url == "https://x.com/user/status/1234567890"
    assert normalized.original_url == url
