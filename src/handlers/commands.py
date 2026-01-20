from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from twitter.translate import language_list, normalize_lang
from utils.settings import SettingsStore


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "Привет! Я превращаю ссылки на X/Twitter в карточки в стиле FxTwitter.\n"
        "Просто пришли ссылку на твит, и я покажу автора, текст, медиа, статистику, цитату и опросы."  # noqa: E501
    )
    await update.message.reply_text(text)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "Доступные команды:\n"
        "/start — краткое описание\n"
        "/help — справка\n"
        "/translate <язык|код|off|status|list> — перевод постов по умолчанию\n"
        "/settings — показать настройки"
    )
    await update.message.reply_text(text)


async def settings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    config = context.application.bot_data["config"]
    store: SettingsStore = context.application.bot_data["settings_store"]
    user_id = update.effective_user.id
    translate = await store.get_translate(user_id, config.default_translate_lang)
    text = (
        f"Текущие настройки:\n"
        f"Перевод: {translate}\n"
        f"Ответы в группах: {'да' if config.reply_in_groups else 'нет'}\n"
        f"Сжатие медиа: {'да' if config.compress_media else 'нет'}"
    )
    await update.message.reply_text(text)


async def translate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    config = context.application.bot_data["config"]
    store: SettingsStore = context.application.bot_data["settings_store"]
    user_id = update.effective_user.id

    if not context.args:
        current = await store.get_translate(user_id, config.default_translate_lang)
        await update.message.reply_text(f"Текущий перевод: {current}")
        return

    raw = " ".join(context.args)
    normalized = normalize_lang(raw)
    if normalized is None:
        await update.message.reply_text("Не понял язык. Напишите название или код, например: /translate ru")
        return

    if normalized == "list":
        await update.message.reply_text("Поддерживаемые языки:\n" + language_list())
        return

    if normalized == "status":
        current = await store.get_translate(user_id, config.default_translate_lang)
        await update.message.reply_text(f"Текущий перевод: {current}")
        return

    await store.set_translate(user_id, normalized)
    await store.save()

    if normalized == "off":
        await update.message.reply_text("Перевод отключён")
    else:
        await update.message.reply_text(f"Перевод включён: {normalized}")
