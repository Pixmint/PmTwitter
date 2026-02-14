"""Обработчики команд бота (минимальный набор)"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from src.handlers.menus import (
    get_main_menu_text,
    get_main_menu_keyboard,
    get_settings_text,
    get_settings_keyboard,
)
from src.twitter.translate import translate_settings

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start - показывает главное меню"""
    await update.message.reply_text(
        text=get_main_menu_text(),
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu_keyboard(),
        disable_web_page_preview=True
    )
    logger.info(f"Команда /start от пользователя {update.effective_user.id}")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /status - показывает настройки и статус"""
    user_id = update.effective_user.id
    current_lang = translate_settings.get_language(user_id)
    
    await update.message.reply_text(
        text=get_settings_text(current_lang),
        parse_mode=ParseMode.HTML,
        reply_markup=get_settings_keyboard(),
        disable_web_page_preview=True
    )
    logger.info(f"Команда /status от пользователя {user_id}")
