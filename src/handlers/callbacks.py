"""Обработчики callback запросов от inline кнопок."""

import logging

from telegram import CallbackQuery, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from src.handlers.menus import (
    CALLBACK_HELP,
    CALLBACK_MAIN_MENU,
    CALLBACK_SETTINGS,
    CALLBACK_TRANSLATE,
    CALLBACK_TRANSLATE_LANG,
    CALLBACK_TRANSLATE_OFF,
    get_help_keyboard,
    get_help_text,
    get_main_menu_keyboard,
    get_main_menu_text,
    get_settings_keyboard,
    get_settings_text,
    get_translate_keyboard,
    get_translate_menu_text,
)
from src.twitter.translate import SUPPORTED_LANGUAGES, translate_settings

logger = logging.getLogger(__name__)


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Главный обработчик всех callback запросов."""
    query = update.callback_query
    user = update.effective_user
    if query is None or user is None:
        logger.warning("Callback update без query/effective_user")
        return

    await query.answer()

    user_id = user.id
    callback_data = query.data or ""

    logger.info("Callback от юзера %s: %s", user_id, callback_data)

    if callback_data == CALLBACK_MAIN_MENU:
        await show_main_menu(query)
    elif callback_data == CALLBACK_HELP:
        await show_help(query)
    elif callback_data == CALLBACK_SETTINGS:
        await show_settings(query, user_id)
    elif callback_data == CALLBACK_TRANSLATE:
        await show_translate_menu(query, user_id)
    elif callback_data == CALLBACK_TRANSLATE_OFF:
        await handle_translate_off(query, user_id)
    elif callback_data.startswith(CALLBACK_TRANSLATE_LANG):
        lang_code = callback_data[len(CALLBACK_TRANSLATE_LANG) :]
        await handle_translate_set_language(query, user_id, lang_code)
    else:
        logger.warning("Неизвестный callback: %s", callback_data)
        await query.answer("⚠️ Неизвестная команда", show_alert=True)


async def show_main_menu(query: CallbackQuery) -> None:
    """Показать главное меню."""
    await query.edit_message_text(
        text=get_main_menu_text(),
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu_keyboard(),
        disable_web_page_preview=True,
    )


async def show_help(query: CallbackQuery) -> None:
    """Показать помощь."""
    await query.edit_message_text(
        text=get_help_text(),
        parse_mode=ParseMode.HTML,
        reply_markup=get_help_keyboard(),
        disable_web_page_preview=True,
    )


async def show_settings(query: CallbackQuery, user_id: int) -> None:
    """Показать настройки/статус."""
    current_lang = translate_settings.get_language(user_id)

    await query.edit_message_text(
        text=get_settings_text(current_lang),
        parse_mode=ParseMode.HTML,
        reply_markup=get_settings_keyboard(),
        disable_web_page_preview=True,
    )


async def show_translate_menu(query: CallbackQuery, user_id: int) -> None:
    """Показать меню выбора языка перевода."""
    current_lang = translate_settings.get_language(user_id)

    await query.edit_message_text(
        text=get_translate_menu_text(current_lang),
        parse_mode=ParseMode.HTML,
        reply_markup=get_translate_keyboard(current_lang),
        disable_web_page_preview=True,
    )


async def handle_translate_off(query: CallbackQuery, user_id: int) -> None:
    """Выключить перевод."""
    current_lang = translate_settings.get_language(user_id)

    if not current_lang:
        await query.answer("ℹ️ Перевод уже выключен", show_alert=False)
        return

    translate_settings.disable(user_id)
    await query.answer("✅ Перевод выключен", show_alert=False)

    await query.edit_message_text(
        text=get_translate_menu_text(None),
        parse_mode=ParseMode.HTML,
        reply_markup=get_translate_keyboard(None),
        disable_web_page_preview=True,
    )


async def handle_translate_set_language(query: CallbackQuery, user_id: int, lang_code: str) -> None:
    """Установить язык перевода."""
    if lang_code not in SUPPORTED_LANGUAGES:
        await query.answer("❌ Неизвестный язык", show_alert=True)
        return

    current_lang = translate_settings.get_language(user_id)

    if current_lang == lang_code:
        lang_name = SUPPORTED_LANGUAGES[lang_code]
        await query.answer(f"ℹ️ Уже установлен: {lang_name}", show_alert=False)
        return

    translate_settings.set_language(user_id, lang_code)
    lang_name = SUPPORTED_LANGUAGES[lang_code]
    await query.answer(f"✅ Установлен: {lang_name}", show_alert=False)

    await query.edit_message_text(
        text=get_translate_menu_text(lang_code),
        parse_mode=ParseMode.HTML,
        reply_markup=get_translate_keyboard(lang_code),
        disable_web_page_preview=True,
    )
