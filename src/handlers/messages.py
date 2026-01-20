import logging
from telegram import Update, InputMediaPhoto, InputMediaVideo
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import TelegramError
from src.config import config
from src.twitter.normalize import find_tweet_urls, normalize_url, extract_tweet_id, extract_username
from src.twitter.fetcher import fetch_tweet_html
from src.twitter.parser import parse_tweet_html
from src.twitter.translate import translate_settings
from src.utils.text_format import format_tweet_card, shorten_text_for_caption
from src.utils.rate_limit import rate_limiter
from src.media.download import download_media_file
from src.media.compress import compress_image, compress_video
from src.media.cleanup import delete_files

logger = logging.getLogger(__name__)

def should_reply_in_chat(update: Update) -> bool:
    """Определяет, нужно ли отвечать в этом чате"""
    message = update.message
    chat = message.chat
    
    # В личке всегда отвечаем
    if chat.type == "private":
        return True
    
    # В группах
    bot_username = update.get_bot().username
    
    # Если бот упомянут
    if message.text and f"@{bot_username}" in message.text:
        return True
    
    # Если включен режим ответов в группах
    if config.REPLY_IN_GROUPS:
        return True
    
    return False

def check_whitelist(user_id: int) -> bool:
    """Проверяет whitelist пользователей"""
    if config.TELEGRAM_USER_IDS is None:
        return True
    return user_id in config.TELEGRAM_USER_IDS

async def send_tweet_card(
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE,
    tweet,
    thread_id: int = None
):
    """Отправляет карточку твита"""
    
    # Проверяем перевод
    user_id = update.effective_user.id
    lang_code = translate_settings.get_language(user_id)
    include_translation = bool(tweet.translated_text)
    
    # Форматируем карточку
    card_text = format_tweet_card(tweet, include_translation=include_translation)
    
    temp_files = []
    
    try:
        # Если нет медиа - просто отправляем текст
        if not tweet.media:
            await update.message.reply_text(
                card_text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                message_thread_id=thread_id
            )
            return
        
        # Скачиваем медиа
        media_files = []
        for media_item in tweet.media[:10]:  # Ограничение 10 медиа
            file_path = await download_media_file(media_item.url, media_item.type)
            if file_path:
                # Сжимаем если нужно
                if media_item.type == "photo":
                    compressed_path = compress_image(file_path)
                else:
                    compressed_path = compress_video(file_path)
                
                media_files.append((media_item.type, compressed_path))
                temp_files.append(file_path)
                if compressed_path != file_path:
                    temp_files.append(compressed_path)
        
        if not media_files:
            # Медиа не удалось скачать
            await update.message.reply_text(
                card_text + "\n\n⚠️ Не удалось загрузить медиа",
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                message_thread_id=thread_id
            )
            return
        
        # Проверяем длину caption
        caption, is_truncated = shorten_text_for_caption(card_text, max_length=1024)
        
        # Если текст слишком длинный - отправляем отдельно
        if is_truncated or len(card_text) > 1024:
            await update.message.reply_text(
                card_text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                message_thread_id=thread_id
            )
            caption = None
        
        # Отправляем медиа
        if len(media_files) == 1:
            # Одно медиа
            media_type, file_path = media_files[0]
            
            with open(file_path, 'rb') as f:
                if media_type == "photo":
                    await update.message.reply_photo(
                        photo=f,
                        caption=caption,
                        parse_mode=ParseMode.HTML if caption else None,
                        message_thread_id=thread_id
                    )
                else:
                    await update.message.reply_video(
                        video=f,
                        caption=caption,
                        parse_mode=ParseMode.HTML if caption else None,
                        message_thread_id=thread_id
                    )
        else:
            # Несколько медиа - альбом
            media_group = []
            
            for idx, (media_type, file_path) in enumerate(media_files):
                with open(file_path, 'rb') as f:
                    media_content = f.read()
                
                if media_type == "photo":
                    media_obj = InputMediaPhoto(
                        media=media_content,
                        caption=caption if idx == 0 else None,
                        parse_mode=ParseMode.HTML if (idx == 0 and caption) else None
                    )
                else:
                    media_obj = InputMediaVideo(
                        media=media_content,
                        caption=caption if idx == 0 else None,
                        parse_mode=ParseMode.HTML if (idx == 0 and caption) else None
                    )
                
                media_group.append(media_obj)
            
            await update.message.reply_media_group(
                media=media_group,
                message_thread_id=thread_id
            )
    
    except TelegramError as e:
        logger.error(f"Ошибка Telegram при отправке: {e}")
        await update.message.reply_text(
            f"❌ Ошибка при отправке медиа: {e}\n\n{card_text}",
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            message_thread_id=thread_id
        )
    
    finally:
        # Удаляем временные файлы
        delete_files(temp_files)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    
    # Проверка нужно ли отвечать
    if not should_reply_in_chat(update):
        return
    
    # Whitelist
    user_id = update.effective_user.id
    if not check_whitelist(user_id):
        logger.warning(f"Пользователь {user_id} не в whitelist")
        return
    
    # Rate limiting
    chat_id = update.effective_chat.id
    if not rate_limiter.is_allowed(user_id, chat_id):
        logger.info(f"Rate limit для пользователя {user_id}")
        return
    
    # Ищем ссылки на твиты
    message_text = update.message.text or ""
    tweet_urls = find_tweet_urls(message_text)
    
    if not tweet_urls:
        return
    
    # Определяем thread_id для топиков
    thread_id = None
    if update.message.is_topic_message:
        thread_id = update.message.message_thread_id
        logger.info(f"Ответ в топик: {thread_id}")
    
    # Обрабатываем первую ссылку
    original_url = tweet_urls[0]
    normalized_url = normalize_url(original_url)
    
    if not normalized_url:
        await update.message.reply_text(
            "❌ Не удалось распознать ссылку на твит",
            message_thread_id=thread_id
        )
        return
    
    tweet_id = extract_tweet_id(normalized_url)
    username = extract_username(normalized_url)
    
    if not tweet_id or not username:
        await update.message.reply_text(
            "❌ Не удалось извлечь данные из ссылки",
            message_thread_id=thread_id
        )
        return
    
    # Проверяем настройку перевода
    lang_code = translate_settings.get_language(user_id)
    
    # Получаем HTML твита
    logger.info(f"Обработка твита: {tweet_id} (язык: {lang_code or 'нет'})")
    
    html = await fetch_tweet_html(tweet_id, username, lang_code)
    
    if not html:
        await update.message.reply_text(
            "❌ Твит недоступен (возможно приватный, удалён или 18+)",
            message_thread_id=thread_id
        )
        return
    
    # Парсим твит
    tweet = parse_tweet_html(html, normalized_url)
    
    if not tweet:
        await update.message.reply_text(
            "❌ Не удалось распарсить твит",
            message_thread_id=thread_id
        )
        return
    
    # Если перевод не получен, но запрошен
    if lang_code and not tweet.translated_text:
        logger.info("Перевод не получен от источника")
    
    # Отправляем карточку
    await send_tweet_card(update, context, tweet, thread_id)