import json
import re
from datetime import datetime
from email.utils import parsedate_to_datetime

from bs4 import BeautifulSoup

from twitter.models import MediaItem, PollData, PollOption, TweetData


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return datetime.fromisoformat(value)
    except ValueError:
        try:
            return parsedate_to_datetime(value)
        except Exception:  # noqa: BLE001
            return None


def _find_json_objects(soup: BeautifulSoup) -> list[object]:
    items: list[object] = []
    for script in soup.find_all("script"):
        if not script.string:
            continue
        content = script.string.strip()
        if not content:
            continue
        if content.startswith("{") or content.startswith("["):
            try:
                items.append(json.loads(content))
            except json.JSONDecodeError:
                continue
        if "__NEXT_DATA__" in script.get("id", ""):
            try:
                items.append(json.loads(content))
            except json.JSONDecodeError:
                continue
    return items


def _deep_find(data: object, predicate) -> list[dict]:
    matches: list[dict] = []
    if isinstance(data, dict):
        if predicate(data):
            matches.append(data)
        for value in data.values():
            matches.extend(_deep_find(value, predicate))
    elif isinstance(data, list):
        for item in data:
            matches.extend(_deep_find(item, predicate))
    return matches


def _extract_poll(poll_data: dict | None) -> PollData | None:
    if not poll_data:
        return None
    options = [
        PollOption(
            text=o.get("label") or o.get("text") or "",
            percent=o.get("percentage"),
            votes=o.get("votes"),
        )
        for o in poll_data.get("options", [])
    ]
    return PollData(
        question=poll_data.get("question") or "",
        options=options,
        total_votes=poll_data.get("totalVotes") or poll_data.get("total_votes"),
        time_left=poll_data.get("timeLeft") or poll_data.get("time_left"),
        status=poll_data.get("status"),
    )


def _tweet_from_dict(cand: dict) -> TweetData:
    text = cand.get("full_text") or cand.get("text") or ""
    user = cand.get("user") or {}
    display = user.get("name") or cand.get("author", {}).get("name") or "—"
    username = user.get("screen_name") or user.get("username") or "—"
    created = cand.get("created_at") or cand.get("createdAt") or cand.get("date")
    created_at = _parse_datetime(created)

    media: list[MediaItem] = []
    media_items = cand.get("media") or cand.get("extended_entities", {}).get("media") or []
    for item in media_items:
        media_url = item.get("media_url_https") or item.get("url") or item.get("media_url")
        media_type = item.get("type") or "photo"
        if media_url:
            media.append(MediaItem(url=media_url, type=media_type))

    replies = cand.get("reply_count") or cand.get("replies") or cand.get("replyCount")
    reposts = cand.get("retweet_count") or cand.get("reposts") or cand.get("repostCount")
    likes = cand.get("favorite_count") or cand.get("likes") or cand.get("likeCount")
    views = cand.get("view_count") or cand.get("views") or cand.get("viewCount")

    poll = _extract_poll(cand.get("poll") or cand.get("pollData"))

    quoted = None
    quoted_raw = (
        cand.get("quoted_status")
        or cand.get("quotedStatus")
        or cand.get("quotedTweet")
        or cand.get("quoted_status_result")
    )
    if isinstance(quoted_raw, dict):
        quoted = _tweet_from_dict(quoted_raw.get("result") or quoted_raw)

    return TweetData(
        display_name=str(display),
        username=str(username).lstrip("@"),
        tweet_url=cand.get("url") or "",
        created_at=created_at,
        text=text,
        media=media,
        replies=str(replies) if replies is not None else None,
        reposts=str(reposts) if reposts is not None else None,
        likes=str(likes) if likes is not None else None,
        views=str(views) if views is not None else None,
        poll=poll,
        quoted=quoted,
    )


def _extract_from_json(data: object) -> TweetData | None:
    candidates = _deep_find(
        data,
        lambda d: any(k in d for k in ("full_text", "text"))
        and any(k in d for k in ("created_at", "createdAt", "date")),
    )
    if not candidates:
        return None

    for cand in candidates:
        return _tweet_from_dict(cand)
    return None


def _media_from_syndication(data: dict) -> list[MediaItem]:
    items: list[MediaItem] = []
    for entry in data.get("mediaDetails", []) or []:
        url = entry.get("media_url_https") or entry.get("media_url") or entry.get("url")
        media_type = entry.get("type") or "photo"
        if url:
            items.append(MediaItem(url=url, type=media_type))

    for url in data.get("photos", []) or []:
        if url:
            items.append(MediaItem(url=url, type="photo"))

    video = data.get("video") or {}
    variants = video.get("variants") or []
    if variants:
        url = variants[0].get("url")
        if url:
            items.append(MediaItem(url=url, type="video"))
    return items


def _tweet_from_syndication(data: dict, tweet_url: str) -> TweetData:
    user = data.get("user") or {}
    display = user.get("name") or data.get("name") or "—"
    username = user.get("screen_name") or user.get("username") or data.get("screen_name") or "—"
    text = data.get("full_text") or data.get("text") or data.get("quoted_text") or ""
    created = data.get("created_at") or data.get("createdAt") or data.get("date")
    created_at = _parse_datetime(created)

    replies = data.get("reply_count") or data.get("replyCount")
    reposts = data.get("retweet_count") or data.get("repost_count") or data.get("repostCount")
    likes = data.get("favorite_count") or data.get("like_count") or data.get("likeCount")
    views = data.get("view_count") or data.get("views")

    quoted = None
    quoted_raw = data.get("quoted_tweet") or data.get("quotedTweet") or data.get("quoted_status")
    if isinstance(quoted_raw, dict):
        quoted = _tweet_from_syndication(quoted_raw, tweet_url)

    return TweetData(
        display_name=str(display),
        username=str(username).lstrip("@"),
        tweet_url=tweet_url,
        created_at=created_at,
        text=text,
        media=_media_from_syndication(data),
        replies=str(replies) if replies is not None else None,
        reposts=str(reposts) if reposts is not None else None,
        likes=str(likes) if likes is not None else None,
        views=str(views) if views is not None else None,
        quoted=quoted,
    )


def parse_syndication_json(data: dict, tweet_url: str) -> TweetData:
    return _tweet_from_syndication(data, tweet_url)


def _extract_meta(soup: BeautifulSoup) -> dict[str, str]:
    data: dict[str, str] = {}
    for meta in soup.find_all("meta"):
        key = meta.get("property") or meta.get("name")
        value = meta.get("content")
        if key and value:
            data[key] = value
    return data


def _parse_poll_from_html(soup: BeautifulSoup) -> PollData | None:
    poll_box = soup.find(attrs={"data-testid": "poll"})
    if not poll_box:
        return None
    question = poll_box.get_text(" ", strip=True)
    options = []
    for option in poll_box.find_all("div"):
        text = option.get_text(" ", strip=True)
        if text:
            options.append(PollOption(text=text))
    return PollData(question=question, options=options)


def parse_tweet(html: str, tweet_url: str, include_quoted_media: bool = False) -> TweetData:
    soup = BeautifulSoup(html, "lxml")

    for obj in _find_json_objects(soup):
        parsed = _extract_from_json(obj)
        if parsed:
            if not parsed.tweet_url:
                parsed.tweet_url = tweet_url
            lang = soup.html.get("lang") if soup.html else None
            if lang:
                parsed.source_language = lang
            return parsed

    meta = _extract_meta(soup)
    title = meta.get("og:title") or meta.get("twitter:title") or "—"
    description = meta.get("og:description") or meta.get("twitter:description") or ""
    image = meta.get("og:image") or meta.get("twitter:image")

    display_name = title.split("(")[0].strip() if title else "—"
    username_match = re.search(r"@([A-Za-z0-9_]+)", title)
    username = username_match.group(1) if username_match else "—"

    created_at = _parse_datetime(meta.get("article:published_time") or meta.get("date"))
    lang = meta.get("og:locale") or (soup.html.get("lang") if soup.html else None)

    media = []
    if image:
        media.append(MediaItem(url=image, type="photo"))

    poll = _parse_poll_from_html(soup)

    return TweetData(
        display_name=display_name,
        username=username,
        tweet_url=tweet_url,
        created_at=created_at,
        text=description,
        media=media,
        poll=poll,
        source_language=lang,
    )
