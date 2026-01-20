import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from src.config import config
from src.twitter.translate import (
    translate_settings, 
    parse_language_input, 
    get_supported_languages_text,
    SUPPORTED_LANGUAGES
)

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    welcome_text = """
<b>👋 Привет! Я бот для просмотра твитов из X/Twitter.</b>

Просто отправьте мне ссылку на твит, и я покажу его содержимое красиво оформленным с:
• Текстом и медиа
• Статистикой (лайки, репосты, просмотры)
• Цитируемыми твитами
• Опросами с прогресс-барами
• Переводом (если включен)

<b>Команды:</b>
/help — подробная справка
/translate — настройка перевода
/settings — текущие настройки

Попробуйте отправить любую ссылку на твит!
"""
    
    await update.message.reply_text(
        welcome_text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
<b>📖 Справка по использованию бота</b>

<b>Как использовать:</b>
Отправьте боту ссылку на твит из X/Twitter (или альтернативных фронтендов), и бот покажет красиво оформленную карточку с содержимым.

<b>Поддерживаемые ссылки:</b>
• https://x.com/username/status/123...
• https://twitter.com/username/status/123...
• https://fxtwitter.com/username/status/123...
• https://fixupx.com/username/status/123...

<b>Что показывает бот:</b>
✅ Автор, дата и время публикации
✅ Текст твита
✅ Фото и видео (встроенно, не файлом)
✅ Цитируемые твиты
✅ Опросы с прогресс-барами
✅ Статистика: комментарии, репосты, лайки, просмотры
✅ Перевод твита (если включен)

<b>Команды:</b>
/start — начало работы
/help — эта справка
/translate &lt;язык|код&gt; — включить перевод
/translate off — выключить перевод
/translate status — текущий статус перевода
/translate list — список языков
/settings — показать настройки

<b>Работа в группах:</b>
• В супергруппах с топиками (темами) бот отвечает в тот же топик
• В обычных группах бот отвечает при упоминании или если включен REPLY_IN_GROUPS

<b>Защита:</b>
• Rate limiting: не более 1 запроса в 5 секунд на пользователя
• Whitelist по ID (если настроен администратором)
"""
    
    await update.message.reply_text(
        help_text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )

async def translate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /translate"""
    user_id = update.effective_user.id
    
    # Если нет аргументов - показываем статус
    if not context.args:
        current_lang = translate_settings.get_language(user_id)
        if current_lang:
            lang_name = SUPPORTED_LANGUAGES.get(current_lang, current_lang)
            status_text = f"✅ <b>Перевод включен:</b> {lang_name} (<code>{current_lang}</code>)\n\n"
            status_text += "Используйте <code>/translate off</code> для отключения"
        else:
            status_text = "❌ <b>Перевод выключен</b>\n\n"
            status_text += "Используйте <code>/translate &lt;язык&gt;</code> для включения\n"
            status_text += "Например: <code>/translate Русский</code> или <code>/translate ru</code>\n\n"
            status_text += "Список языков: /translate list"
        
        await update.message.reply_text(status_text, parse_mode=ParseMode.HTML)
        return
    
    input_text = " ".join(context.args)
    parsed = parse_language_input(input_text)
    
    # Специальные команды
    if parsed == "off":
        translate_settings.disable(user_id)
        await update.message.reply_text(
            "✅ Перевод <b>выключен</b>",
            parse_mode=ParseMode.HTML
        )
        return
    
    if parsed == "status":
        # Перенаправляем на обработку без аргументов
        context.args = []
        await translate_command(update, context)
        return
    
    if parsed == "list":
        await update.message.reply_text(
            get_supported_languages_text(),
            parse_mode=ParseMode.HTML
        )
        return
    
    # Установка языка
    if parsed and parsed in SUPPORTED_LANGUAGES:
        translate_settings.set_language(user_id, parsed)
        lang_name = SUPPORTED_LANGUAGES[parsed]
        
        await update.message.reply_text(
            f"✅ Перевод <b>включен</b> на <b>{lang_name}</b> (<code>{parsed}</code>)\n\n"
            f"Теперь все твиты будут переводиться на {lang_name}, если перевод доступен.",
            parse_mode=ParseMode.HTML
        )
    else:
        await update.message.reply_text(
            f"❌ Неизвестный язык: <code>{input_text}</code>\n\n"
            f"Используйте /translate list для списка поддерживаемых языков",
            parse_mode=ParseMode.HTML
        )

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /settings"""
    user_id = update.effective_user.id
    
    # Перевод
    current_lang = translate_settings.get_language(user_id)
    if current_lang:
        lang_name = SUPPORTED_LANGUAGES.get(current_lang, current_lang)
        translate_status = f"✅ Включен: {lang_name} (<code>{current_lang}</code>)"
    else:
        translate_status = "❌ Выключен"
    
    settings_text = f"""
<b>⚙️ Настройки бота</b>

<b>Перевод:</b> {translate_status}

<b>Системные настройки:</b>
• Ответы в группах: {"✅ Да" if config.REPLY_IN_GROUPS else "❌ Только при упоминании"}
• Сжатие медиа: {"✅ Включено" if config.COMPRESS_MEDIA else "❌ Выключено"}
• Макс. размер медиа: {config.MAX_MEDIA_MB} МБ
• Quoted медиа: {"✅ Показывать" if config.INCLUDE_QUOTED_MEDIA else "❌ Скрывать"}

<b>Источник данных:</b>
• {config.FX_BASE_URL}

Изменить перевод: /translate
"""
    
    await update.message.reply_text(
        settings_text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )