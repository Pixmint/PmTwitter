"""Модуль для создания меню и клавиатур бота"""
from typing import Optional
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from src.twitter.translate import SUPPORTED_LANGUAGES
from src.config import config


# ==================== Эмодзи флагов для языков ====================
LANGUAGE_FLAGS = {
    "ru": "🇷🇺",
    "en": "🇬🇧",
    "uk": "🇺🇦",
    "es": "🇪🇸",
    "fr": "🇫🇷",
    "de": "🇩🇪",
    "it": "🇮🇹",
    "pt": "🇵🇹",
    "ja": "🇯🇵",
    "ko": "🇰🇷",
    "zh": "🇨🇳",
    "ar": "🇸🇦",
    "tr": "🇹🇷",
    "pl": "🇵🇱",
    "nl": "🇳🇱",
}


# ==================== Callback Data ====================
# Формат: action:param или просто action

CALLBACK_MAIN_MENU = "main_menu"
CALLBACK_HELP = "help"
CALLBACK_SETTINGS = "settings"
CALLBACK_TRANSLATE = "translate"
CALLBACK_TRANSLATE_OFF = "translate:off"
CALLBACK_TRANSLATE_LANG = "translate:"  # + язык код (ru, en, etc)


# ==================== Главное меню ====================

def get_main_menu_text() -> str:
    """Текст главного меню"""
    return """<b>👋 Привет! Я бот для просмотра твитов из X/Twitter.</b>

Просто отправьте мне ссылку на твит, и я покажу его содержимое красиво оформленным с:
• Текстом и медиа
• Статистикой (лайки, репосты, просмотры)
• Цитируемыми твитами
• Опросами с прогресс-барами
• Переводом (если включен)

Выберите действие:"""


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура главного меню"""
    keyboard = [
        [
            InlineKeyboardButton("🌐 Перевод", callback_data=CALLBACK_TRANSLATE),
            InlineKeyboardButton("📊 Статус", callback_data=CALLBACK_SETTINGS),
        ],
        [
            InlineKeyboardButton("❓ Помощь", callback_data=CALLBACK_HELP),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


# ==================== Меню помощи ====================

def get_help_text() -> str:
    """Текст помощи"""
    return """<b>📖 Справка по использованию бота</b>

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

<b>Работа в группах:</b>
• В супергруппах с топиками (темами) бот отвечает в тот же топик
• В обычных группах бот отвечает при упоминании или если включен REPLY_IN_GROUPS

<b>Защита:</b>
• Rate limiting: не более 1 запроса в 5 секунд на пользователя
• Whitelist по ID (если настроен администратором)

<b>Команды:</b>
/start — главное меню
/status — показать настройки"""


def get_help_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура меню помощи"""
    keyboard = [
        [InlineKeyboardButton("⬅️ Назад", callback_data=CALLBACK_MAIN_MENU)],
    ]
    return InlineKeyboardMarkup(keyboard)


# ==================== Меню настроек перевода ====================

def get_translate_menu_text(current_lang: Optional[str] = None) -> str:
    """Текст меню перевода"""
    if current_lang:
        lang_name = SUPPORTED_LANGUAGES.get(current_lang, current_lang)
        status = f"✅ <b>Перевод включен:</b> {lang_name} (<code>{current_lang}</code>)"
    else:
        status = "❌ <b>Перевод выключен</b>"
    
    text = f"""<b>🌐 Настройка перевода</b>

{status}

Выберите язык для перевода твитов или выключите перевод:"""
    
    return text


def get_translate_keyboard(current_lang: Optional[str] = None) -> InlineKeyboardMarkup:
    """Клавиатура меню перевода с выбором языков"""
    
    # Популярные языки в первую очередь
    priority_langs = ["ru", "en", "uk", "es", "de", "fr"]
    other_langs = [code for code in SUPPORTED_LANGUAGES.keys() if code not in priority_langs]
    
    keyboard = []
    
    # Добавляем популярные языки по 2 в ряд
    for i in range(0, len(priority_langs), 2):
        row = []
        for code in priority_langs[i:i+2]:
            flag = LANGUAGE_FLAGS.get(code, "")
            name = SUPPORTED_LANGUAGES[code]
            # Добавляем ✅ к текущему языку
            button_text = f"✅ {flag} {name}" if code == current_lang else f"{flag} {name}"
            row.append(InlineKeyboardButton(button_text, callback_data=f"{CALLBACK_TRANSLATE_LANG}{code}"))
        keyboard.append(row)
    
    # Добавляем остальные языки по 2 в ряд
    for i in range(0, len(other_langs), 2):
        row = []
        for code in other_langs[i:i+2]:
            flag = LANGUAGE_FLAGS.get(code, "")
            name = SUPPORTED_LANGUAGES[code]
            button_text = f"✅ {flag} {name}" if code == current_lang else f"{flag} {name}"
            row.append(InlineKeyboardButton(button_text, callback_data=f"{CALLBACK_TRANSLATE_LANG}{code}"))
        keyboard.append(row)
    
    # Кнопки управления
    keyboard.append([
        InlineKeyboardButton("❌ Выключить" if current_lang else "⚙️ Уже выключен", 
                           callback_data=CALLBACK_TRANSLATE_OFF)
    ])
    keyboard.append([
        InlineKeyboardButton("⬅️ Назад", callback_data=CALLBACK_MAIN_MENU)
    ])
    
    return InlineKeyboardMarkup(keyboard)


# ==================== Меню статуса/настроек ====================

def get_settings_text(current_lang: Optional[str] = None) -> str:
    """Текст меню настроек/статуса"""
    
    # Перевод
    if current_lang:
        lang_name = SUPPORTED_LANGUAGES.get(current_lang, current_lang)
        translate_status = f"✅ Включен: {lang_name} (<code>{current_lang}</code>)"
    else:
        translate_status = "❌ Выключен"
    
    text = f"""<b>⚙️ Настройки бота</b>

<b>Перевод:</b> {translate_status}

<b>Системные настройки:</b>
• Ответы в группах: {"✅ Да" if config.REPLY_IN_GROUPS else "❌ Только при упоминании"}
• Ответ реплаем: {"✅ Да" if config.REPLY_TO_MESSAGE else "❌ Нет"}
• Подпись над медиа: {"✅ Да" if config.CAPTION_ABOVE_MEDIA else "❌ Нет (под медиа)"}
• Сжатие медиа: {"✅ Включено" if config.COMPRESS_MEDIA else "❌ Выключено"}
• Макс. размер медиа: {config.MAX_MEDIA_MB} МБ
• Quoted медиа: {"✅ Показывать" if config.INCLUDE_QUOTED_MEDIA else "❌ Скрывать"}

<b>Источник данных:</b>
• {config.FX_BASE_URL}
"""
    
    return text


def get_settings_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура меню настроек"""
    keyboard = [
        [
            InlineKeyboardButton("🌐 Изменить перевод", callback_data=CALLBACK_TRANSLATE),
        ],
        [
            InlineKeyboardButton("⬅️ Назад", callback_data=CALLBACK_MAIN_MENU)
        ],
    ]
    return InlineKeyboardMarkup(keyboard)
