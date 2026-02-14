"""Обработчики callback запросов от inline кнопок"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from src.handlers.menus import (
    CALLBACK_MAIN_MENU,
    CALLBACK_HELP,
    CALLBACK_SETTINGS,
    CALLBACK_TRANSLATE,
    CALLBACK_TRANSLATE_OFF,
    CALLBACK_TRANSLATE_LANG,
    get_main_menu_text,
    get_main_menu_keyboard,
    get_help_text,
    get_help_keyboard,
    get_translate_menu_text,
    get_translate_keyboard,
    get_settings_text,
    get_settings_keyboard,
)
from src.twitter.translate import translate_settings, SUPPORTED_LANGUAGES

logger = logging.getLogger(__name__)


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главный обработчик всех callback запросов"""
    query = update.callback_query
    await query.answer()  # Подтверждаем получение callback
    
    user_id = update.effective_user.id
    callback_data = query.data
    
    logger.info(f"Callback от юзера {user_id}: {callback_data}")
    
    # Главное меню
    if callback_data == CALLBACK_MAIN_MENU:
        await show_main_menu(query)
    
    # Помощь
    elif callback_data == CALLBACK_HELP:
        await show_help(query)
    
    # Настройки/статус
    elif callback_data == CALLBACK_SETTINGS:
        await show_settings(query, user_id)
    
    # Меню перевода
    elif callback_data == CALLBACK_TRANSLATE:
        await show_translate_menu(query, user_id)
    
    # Выключить перевод
    elif callback_data == CALLBACK_TRANSLATE_OFF:
        await handle_translate_off(query, user_id)
    
    # Выбор языка перевода
    elif callback_data.startswith(CALLBACK_TRANSLATE_LANG):
        lang_code = callback_data[len(CALLBACK_TRANSLATE_LANG):]
        await handle_translate_set_language(query, user_id, lang_code)
    
    else:
        logger.warning(f"Неизвестный callback: {callback_data}")
        await query.answer("⚠️ Неизвестная команда", show_alert=True)


# ==================== Обработчики конкретных меню ====================

async def show_main_menu(query):
    """Показать главное меню"""
    await query.edit_message_text(
        text=get_main_menu_text(),
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu_keyboard(),
        disable_web_page_preview=True
    )


async def show_help(query):
    """Показать помощь"""
    await query.edit_message_text(
        text=get_help_text(),
        parse_mode=ParseMode.HTML,
        reply_markup=get_help_keyboard(),
        disable_web_page_preview=True
    )


async def show_settings(query, user_id: int):
    """Показать настройки/статус"""
    current_lang = translate_settings.get_language(user_id)
    
    await query.edit_message_text(
        text=get_settings_text(current_lang),
        parse_mode=ParseMode.HTML,
        reply_markup=get_settings_keyboard(),
        disable_web_page_preview=True
    )


async def show_translate_menu(query, user_id: int):
    """Показать меню выбора языка перевода"""
    current_lang = translate_settings.get_language(user_id)
    
    await query.edit_message_text(
        text=get_translate_menu_text(current_lang),
        parse_mode=ParseMode.HTML,
        reply_markup=get_translate_keyboard(current_lang),
        disable_web_page_preview=True
    )


async def handle_translate_off(query, user_id: int):
    """Выключить перевод"""
    current_lang = translate_settings.get_language(user_id)
    
    if not current_lang:
        # Уже выключен
        await query.answer("ℹ️ Перевод уже выключен", show_alert=False)
        return
    
    translate_settings.disable(user_id)
    await query.answer("✅ Перевод выключен", show_alert=False)
    
    # Обновляем меню
    await query.edit_message_text(
        text=get_translate_menu_text(None),
        parse_mode=ParseMode.HTML,
        reply_markup=get_translate_keyboard(None),
        disable_web_page_preview=True
    )


async def handle_translate_set_language(query, user_id: int, lang_code: str):
    """Установить язык перевода"""
    if lang_code not in SUPPORTED_LANGUAGES:
        await query.answer("❌ Неизвестный язык", show_alert=True)
        return
    
    current_lang = translate_settings.get_language(user_id)
    
    # Если выбрали уже активный язык
    if current_lang == lang_code:
        lang_name = SUPPORTED_LANGUAGES[lang_code]
        await query.answer(f"ℹ️ Уже установлен: {lang_name}", show_alert=False)
        return
    
    # Устанавливаем новый язык
    translate_settings.set_language(user_id, lang_code)
    lang_name = SUPPORTED_LANGUAGES[lang_code]
    await query.answer(f"✅ Установлен: {lang_name}", show_alert=False)
    
    # Обновляем меню
    await query.edit_message_text(
        text=get_translate_menu_text(lang_code),
        parse_mode=ParseMode.HTML,
        reply_markup=get_translate_keyboard(lang_code),
        disable_web_page_preview=True
    )
