import logging
from telegram import InputMediaPhoto, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from config import Config
from media.cleanup import cleanup_temp
from media.compress import compress_image, compress_video, size_mb
from media.download import download_media
from twitter.fetcher import fetch_html, fetch_json
from twitter.normalize import extract_status_urls, normalize_status_url
from twitter.parser import parse_syndication_json, parse_tweet
from twitter.translate import code_to_name
from utils.rate_limit import RateLimiter
from utils.settings import SettingsStore
from utils.text_format import CAPTION_LIMIT, build_full_text
from utils.topics import get_thread_id

logger = logging.getLogger(__name__)


def _should_reply_in_group(update: Update, config: Config, bot_username: str | None) -> bool:
    chat = update.effective_chat
    if not chat:
        return False
    if chat.type in {"private"}:
        return True
    if config.reply_in_groups:
        return True
    if not bot_username or not update.message or not update.message.entities:
        return False
    text = update.message.text or ""
    for entity in update.message.entities:
        if entity.type == "mention":
            mention = text[entity.offset : entity.offset + entity.length]
            if mention.lower() == f"@{bot_username.lower()}":
                return True
    return False


def _limit_media(items: list, limit: int = 10) -> tuple[list, int]:
    if len(items) <= limit:
        return items, 0
    return items[:limit], len(items) - limit


async def _reply_text(message, text: str, thread_id: int | None) -> None:
    await message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        message_thread_id=thread_id,
    )


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if not message or not message.text:
        return

    config: Config = context.application.bot_data["config"]
    limiter: RateLimiter = context.application.bot_data["rate_limiter"]
    store: SettingsStore = context.application.bot_data["settings_store"]

    if config.telegram_user_ids and update.effective_user.id not in config.telegram_user_ids:
        return

    if not _should_reply_in_group(update, config, context.bot.username):
        return

    urls = extract_status_urls(message.text)
    if not urls:
        return

    allowed = await limiter.allow(update.effective_user.id, update.effective_chat.id)
    if not allowed:
        return

    thread_id = get_thread_id(message)

    for raw_url in urls:
        normalized = normalize_status_url(raw_url)
        if not normalized:
            continue

        try:
            fetch, source_kind, base_url = await _fetch_tweet_html(normalized, config)
        except Exception as exc:  # noqa: BLE001
            await _reply_text(
                message,
                "Твит недоступен: фронтенды не отвечают.",
                thread_id,
            )
            continue
        if any(phrase in fetch.text.lower() for phrase in ("tweet not found", "tweet unavailable", "this tweet is")):
            await _reply_text(
                message,
                "Твит недоступен: приватный, удалённый или с ограничением по возрасту.",
                thread_id,
            )
            continue

        tweet = parse_tweet(fetch.text, normalized.normalized_url, config.include_quoted_media)
        if not tweet.text or tweet.username in {"", "-"}:
            try:
                data = await fetch_json(
                    f"https://cdn.syndication.twimg.com/tweet-result?id={normalized.status_id}&lang=en"
                )
                tweet = parse_syndication_json(data.data, normalized.normalized_url)
            except Exception:  # noqa: BLE001
                pass
        tweet.tweet_url = normalized.original_url
        tweet.source_language = code_to_name(tweet.source_language)

        translate_setting = await store.get_translate(update.effective_user.id, config.default_translate_lang)
        include_translation = translate_setting != "off"
        if include_translation and source_kind == "frontend" and base_url:
            lang_code = translate_setting
            try:
                trans_fetch, _, _ = await _fetch_tweet_html(normalized, config, lang_code, base_url)
                trans_tweet = parse_tweet(trans_fetch.text, normalized.normalized_url, config.include_quoted_media)
                if trans_tweet.text and trans_tweet.text != tweet.text:
                    tweet.translated_text = trans_tweet.text
                    if not tweet.source_language:
                        tweet.source_language = code_to_name(trans_tweet.source_language)
                else:
                    tweet.translated_text = None
            except Exception:  # noqa: BLE001
                tweet.translated_text = None
        elif include_translation:
            tweet.translated_text = None

        parts = build_full_text(tweet, include_translation)

        media_items = list(tweet.media)
        if config.include_quoted_media and tweet.quoted:
            media_items.extend(tweet.quoted.media)

        media_items, skipped = _limit_media(media_items, limit=10)

        if media_items:
            if len(parts) == 1 and len(parts[0]) <= CAPTION_LIMIT:
                await _send_media_with_caption(
                    update,
                    context,
                    media_items,
                    parts[0],
                    thread_id,
                    config,
                )
            else:
                for part in parts:
                    await _reply_text(message, part, thread_id)
                await _send_media_with_caption(update, context, media_items, None, thread_id, config)
        else:
            for part in parts:
                await _reply_text(message, part, thread_id)

        if skipped:
            await _reply_text(message, f"Ещё {skipped} медиа пропущено", thread_id)

    await cleanup_temp()


async def _send_media_with_caption(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    media_items,
    caption: str | None,
    thread_id: int | None,
    config: Config,
) -> None:
    message = update.message
    downloaded = await download_media(media_items)
    if not downloaded:
        if caption:
            await _reply_text(message, caption, thread_id)
        return

    first_caption_used = False
    all_photos = all(item.type == "photo" for item, _ in downloaded)
    if all_photos and len(downloaded) > 1:
        media_group = []
        for item, path in downloaded:
            if config.compress_media or size_mb(path) > config.max_media_mb:
                path = compress_image(path, config.max_media_mb)
            if caption and not first_caption_used:
                media_group.append(InputMediaPhoto(media=str(path), caption=caption, parse_mode=ParseMode.HTML))
                first_caption_used = True
            else:
                media_group.append(InputMediaPhoto(media=str(path)))
        await context.bot.send_media_group(
            chat_id=message.chat_id,
            media=media_group,
            message_thread_id=thread_id,
        )
    else:
        for item, path in downloaded:
            if item.type == "photo":
                if config.compress_media or size_mb(path) > config.max_media_mb:
                    path = compress_image(path, config.max_media_mb)
                if caption and not first_caption_used:
                    await context.bot.send_photo(
                        chat_id=message.chat_id,
                        photo=str(path),
                        caption=caption,
                        parse_mode=ParseMode.HTML,
                        message_thread_id=thread_id,
                    )
                    first_caption_used = True
                else:
                    await context.bot.send_photo(
                        chat_id=message.chat_id,
                        photo=str(path),
                        message_thread_id=thread_id,
                    )
            else:
                if config.compress_media or size_mb(path) > config.max_media_mb:
                    path = compress_video(path, config.max_media_mb)
                if caption and not first_caption_used:
                    await context.bot.send_video(
                        chat_id=message.chat_id,
                        video=str(path),
                        caption=caption,
                        parse_mode=ParseMode.HTML,
                        message_thread_id=thread_id,
                    )
                    first_caption_used = True
                else:
                    await context.bot.send_video(
                        chat_id=message.chat_id,
                        video=str(path),
                        message_thread_id=thread_id,
                    )

    for _, path in downloaded:
        try:
            path.unlink(missing_ok=True)
        except Exception:  # noqa: BLE001
            continue


def _jina_url(url: str) -> str:
    if url.startswith("https://"):
        return "https://r.jina.ai/https://" + url[len("https://") :]
    if url.startswith("http://"):
        return "https://r.jina.ai/http://" + url[len("http://") :]
    return "https://r.jina.ai/https://" + url


async def _fetch_tweet_html(
    normalized,
    config: Config,
    lang_code: str | None = None,
    single_base: str | None = None,
):
    bases = [single_base] if single_base else list(config.fx_base_urls)
    for base_url in bases:
        base_url = base_url.rstrip("/")
        if not base_url:
            continue
        if lang_code:
            url = f"{base_url}/{normalized.user}/status/{normalized.status_id}/{lang_code}"
        else:
            url = f"{base_url}/{normalized.user}/status/{normalized.status_id}"
        try:
            fetch = await fetch_html(url, allow_x_fallback=False)
            return fetch, "frontend", base_url
        except Exception:
            continue

    if config.enable_jina_fallback:
        x_url = f"https://x.com/{normalized.user}/status/{normalized.status_id}"
        try:
            fetch = await fetch_html(_jina_url(x_url), allow_x_fallback=True)
            return fetch, "jina", None
        except Exception:
            pass

    if config.allow_x_fallback:
        x_url = f"https://x.com/{normalized.user}/status/{normalized.status_id}"
        fetch = await fetch_html(x_url, allow_x_fallback=True)
        return fetch, "x", None

    raise RuntimeError("Фронтенды недоступны")
