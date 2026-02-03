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

def get_reply_to_message_id(update: Update) -> int | None:
    """Возвращает ID исходного сообщения для reply, если включено"""
    if config.REPLY_TO_MESSAGE and update.message:
        return update.message.message_id
    return None

async def send_text_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
    thread_id: int = None,
    **kwargs
):
    """Отправляет текст без reply, если настройка выключена"""
    chat_id = update.effective_chat.id
    reply_to_message_id = get_reply_to_message_id(update)
    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        message_thread_id=thread_id,
        reply_to_message_id=reply_to_message_id,
        **kwargs
    )

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
    thread_id: int = None,
    user_comment: str = None
):
    """Отправляет карточку твита"""
    
    # Проверяем перевод
    user_id = update.effective_user.id
    lang_code = translate_settings.get_language(user_id)
    include_translation = bool(tweet.translated_text)
    
    # Форматируем карточку
    card_text = format_tweet_card(tweet, include_translation=include_translation, user_comment=user_comment)
    
    temp_files = []
    
    try:
        # Если нет медиа - просто отправляем текст
        if not tweet.media:
            await send_text_message(
                update,
                context,
                card_text,
                thread_id=thread_id,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
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
            await send_text_message(
                update,
                context,
                card_text + "\n\n⚠️ Не удалось загрузить медиа",
                thread_id=thread_id,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            return
        
        # Проверяем длину caption
        caption, is_truncated = shorten_text_for_caption(card_text, max_length=1024)
        
        # Если текст слишком длинный - отправляем отдельно
        if is_truncated or len(card_text) > 1024:
            await send_text_message(
                update,
                context,
                card_text,
                thread_id=thread_id,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            caption = None
        
        # Отправляем медиа
        if len(media_files) == 1:
            # Одно медиа
            media_type, file_path = media_files[0]
            reply_to_message_id = get_reply_to_message_id(update)
            
            with open(file_path, 'rb') as f:
                if media_type == "photo":
                    await context.bot.send_photo(
                        chat_id=update.effective_chat.id,
                        photo=f,
                        caption=caption,
                        parse_mode=ParseMode.HTML if caption else None,
                        message_thread_id=thread_id,
                        reply_to_message_id=reply_to_message_id
                    )
                else:
                    await context.bot.send_video(
                        chat_id=update.effective_chat.id,
                        video=f,
                        caption=caption,
                        parse_mode=ParseMode.HTML if caption else None,
                        message_thread_id=thread_id,
                        reply_to_message_id=reply_to_message_id
                    )
        else:
            # Несколько медиа - альбом
            media_group = []
            reply_to_message_id = get_reply_to_message_id(update)
            
            for idx, (media_type, file_path) in enumerate(media_files):
                if media_type == "photo":
                    media_obj = InputMediaPhoto(
                        media=open(file_path, 'rb'),
                        caption=caption if idx == 0 else None,
                        parse_mode=ParseMode.HTML if (idx == 0 and caption) else None
                    )
                else:
                    media_obj = InputMediaVideo(
                        media=open(file_path, 'rb'),
                        caption=caption if idx == 0 else None,
                        parse_mode=ParseMode.HTML if (idx == 0 and caption) else None
                    )
                
                media_group.append(media_obj)
            
            await context.bot.send_media_group(
                chat_id=update.effective_chat.id,
                media=media_group,
                message_thread_id=thread_id,
                reply_to_message_id=reply_to_message_id
            )
    
    except TelegramError as e:
        logger.error(f"Ошибка Telegram при отправке: {e}")
        await send_text_message(
            update,
            context,
            f"❌ Ошибка при отправке медиа: {e}\n\n{card_text}",
            thread_id=thread_id,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
    finally:
        # Удаляем временные файлы
        delete_files(temp_files)

async def process_tweet_url(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    original_url: str,
    thread_id: int = None,
    user_comment: str = None
):
    """Обрабатывает одну ссылку на твит"""
    normalized_url = normalize_url(original_url)
    
    if not normalized_url:
        logger.warning(f"Не удалось нормализовать URL: {original_url}")
        return False
    
    tweet_id = extract_tweet_id(normalized_url)
    username = extract_username(normalized_url)
    
    if not tweet_id or not username:
        logger.warning(f"Не удалось извлечь данные из URL: {normalized_url}")
        return False
    
    # Проверяем настройку перевода
    user_id = update.effective_user.id
    lang_code = translate_settings.get_language(user_id)
    
    # Получаем данные твита
    logger.info(f"Обработка твита: {tweet_id} (язык: {lang_code or 'нет'})")
    
    # Получаем HTML твита
    html = await fetch_tweet_html(tweet_id, username, lang_code)
    
    if not html:
        await send_text_message(
            update,
            context,
            f"❌ Твит недоступен (возможно приватный, удалён или 18+): {original_url}",
            thread_id=thread_id
        )
        return False
    
    # Парсим твит
    tweet = parse_tweet_html(html, normalized_url)
    
    if not tweet:
        await send_text_message(
            update,
            context,
            f"❌ Не удалось распарсить твит: {original_url}",
            thread_id=thread_id
        )
        return False
    
    # Если перевод не получен, но запрошен
    if lang_code and not tweet.translated_text:
        logger.info("Перевод не получен от источника")
    
    # Отправляем карточку
    try:
        await send_tweet_card(update, context, tweet, thread_id, user_comment)
        return True
    except Exception as e:
        logger.error(f"Ошибка при отправке твита: {e}")
        await send_text_message(
            update,
            context,
            f"❌ Ошибка при отправке: {str(e)[:100]}",
            thread_id=thread_id
        )
        return False

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
    
    # Извлекаем комментарий если есть текст перед первой ссылкой
    user_comment = None
    first_url_pos = message_text.find(tweet_urls[0])
    if first_url_pos > 0:
        user_comment = message_text[:first_url_pos].strip()
        # Убираем упоминание бота из комментария
        bot_username = update.get_bot().username
        user_comment = user_comment.replace(f"@{bot_username}", "").strip()
        if user_comment:
            logger.info(f"Найден комментарий пользователя: {user_comment[:50]}")
    
    # Обрабатываем все найденные ссылки
    processed_count = 0
    for idx, original_url in enumerate(tweet_urls):
        # Комментарий только для первого твита
        comment = user_comment if idx == 0 else None
        
        success = await process_tweet_url(
            update,
            context,
            original_url,
            thread_id,
            comment
        )
        
        if success:
            processed_count += 1
    
    logger.info(f"Обработано {processed_count} из {len(tweet_urls)} ссылок")
    
    # Удаляем исходное сообщение в группах если включена опция
    chat = update.effective_chat
    if (config.REMOVE_MESSAGE_IN_GROUPS and 
        chat.type in ["group", "supergroup"] and 
        update.message.message_id and
        processed_count > 0):  # Только если хотя бы одна ссылка обработана
        try:
            await context.bot.delete_message(
                chat_id=chat.id,
                message_id=update.message.message_id
            )
            logger.info(f"Удалено сообщение {update.message.message_id} в группе {chat.id}")
        except TelegramError as e:
            logger.warning(f"Не удалось удалить сообщение: {e}")
