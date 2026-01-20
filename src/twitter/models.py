from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class MediaItem:
    url: str
    type: str  # "photo" or "video"


@dataclass
class PollOption:
    text: str
    percent: int | None = None
    votes: int | None = None


@dataclass
class PollData:
    question: str
    options: list[PollOption] = field(default_factory=list)
    total_votes: int | None = None
    time_left: str | None = None
    status: str | None = None


@dataclass
class TweetData:
    display_name: str
    username: str
    tweet_url: str
    created_at: datetime | None
    text: str
    media: list[MediaItem] = field(default_factory=list)
    replies: str | None = None
    reposts: str | None = None
    likes: str | None = None
    views: str | None = None
    quoted: "TweetData | None" = None
    poll: PollData | None = None
    source_language: str | None = None
    translated_text: str | None = None
