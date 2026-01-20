import html
from datetime import datetime

from twitter.models import PollData, PollOption, TweetData

TEXT_LIMIT = 4096
CAPTION_LIMIT = 1024


def escape(text: str) -> str:
    return html.escape(text, quote=False)


def format_datetime(dt: datetime | None) -> str:
    if not dt:
        return "—"
    return dt.strftime("%d.%m.%Y, %H:%M")


def format_stats(value: str | None) -> str:
    return value if value else "—"


def render_poll_bar(percent: int | None, length: int = 20) -> str:
    if percent is None:
        return "".join(["░" for _ in range(length)])
    filled = max(0, min(length, int(round(length * percent / 100))))
    return "".join(["█" for _ in range(filled)] + ["░" for _ in range(length - filled)])


def render_poll(poll: PollData) -> str:
    lines = [f"<b>{escape(poll.question)}</b>"]
    for opt in poll.options:
        percent = f"{opt.percent}%" if opt.percent is not None else "—%"
        bar = render_poll_bar(opt.percent)
        lines.append(f"<code>{escape(opt.text)}  {percent}  {bar}</code>")
    total = f"{poll.total_votes} голосов" if poll.total_votes is not None else "Голоса: —"
    status = poll.time_left or poll.status or "—"
    lines.append(f"{total} · {status}")
    return "\n".join(lines)


def render_quoted(tweet: TweetData) -> str:
    profile_url = f"https://x.com/{tweet.username}" if tweet.username else tweet.tweet_url
    header = (
        f"<b>Цитата {escape(tweet.display_name)} ("
        f"<a href=\"{escape(profile_url)}\">@{escape(tweet.username)}</a>) — "
        f"{format_datetime(tweet.created_at)}:</b>"
    )
    text_lines = [f"│ {escape(line)}" for line in tweet.text.splitlines() if line.strip()]
    body = "\n".join(text_lines) if text_lines else "│ —"
    return "\n".join([header, body])


def build_message_block(tweet: TweetData) -> list[str]:
    profile_url = f"https://x.com/{tweet.username}" if tweet.username else tweet.tweet_url
    header = (
        f"{escape(tweet.display_name)} ("
        f"<a href=\"{escape(profile_url)}\">@{escape(tweet.username)}</a>) — "
        f"{format_datetime(tweet.created_at)}"
    )
    parts = [header, escape(tweet.text or "—")]

    if tweet.quoted:
        parts.append(render_quoted(tweet.quoted))

    if tweet.poll:
        parts.append(render_poll(tweet.poll))

    stats = (
        f"💬 {format_stats(tweet.replies)}  "
        f"🔁 {format_stats(tweet.reposts)}  "
        f"❤️ {format_stats(tweet.likes)}  "
        f"👁 {format_stats(tweet.views)}"
    )
    parts.append(stats)

    parts.append(f"<i>Оригинал: <a href=\"{escape(tweet.tweet_url)}\">открыть пост</a></i>")
    return parts


def build_full_text(tweet: TweetData, include_translation: bool) -> list[str]:
    blocks = build_message_block(tweet)

    if include_translation:
        if tweet.translated_text:
            source = tweet.source_language or "неизвестного языка"
            blocks.append(f"Переведено с {escape(source)}")
            blocks.append(escape(tweet.translated_text))
        else:
            blocks.append("Перевод недоступен")

    combined = "\n\n".join(blocks)
    if len(combined) <= TEXT_LIMIT:
        return [combined]

    parts: list[str] = []
    current = ""
    for block in blocks:
        next_part = (current + "\n\n" + block) if current else block
        if len(next_part) > TEXT_LIMIT:
            if current:
                parts.append(current)
                current = block
            else:
                parts.append(block[:TEXT_LIMIT])
                current = block[TEXT_LIMIT:]
        else:
            current = next_part
    if current:
        parts.append(current)
    return parts
