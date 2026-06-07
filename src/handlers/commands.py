"""Обработчики команд бота (минимальный набор)."""

import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from src.handlers.menus import (
    get_main_menu_keyboard,
    get_main_menu_text,
    get_settings_keyboard,
    get_settings_text,
)
from src.twitter.translate import translate_settings

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start - показывает главное меню."""
    if update.message is None or update.effective_user is None:
        logger.warning("Команда /start без message/effective_user")
        return

    await update.message.reply_text(
        text=get_main_menu_text(),
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu_keyboard(),
        disable_web_page_preview=True,
    )
    logger.info("Команда /start от пользователя %s", update.effective_user.id)


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /status - показывает настройки и статус."""
    if update.message is None or update.effective_user is None:
        logger.warning("Команда /status без message/effective_user")
        return

    user_id = update.effective_user.id
    current_lang = translate_settings.get_language(user_id)

    await update.message.reply_text(
        text=get_settings_text(current_lang),
        parse_mode=ParseMode.HTML,
        reply_markup=get_settings_keyboard(),
        disable_web_page_preview=True,
    )
    logger.info("Команда /status от пользователя %s", user_id)
