import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from src.config import config
from src.handlers.commands import start, help_command, translate_command, settings_command
from src.handlers.messages import handle_message
from src.media.cleanup import cleanup_temp_files

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, config.LOG_LEVEL)
)
logger = logging.getLogger(__name__)

async def post_init(application: Application) -> None:
    """Инициализация после запуска бота"""
    logger.info("Очистка временных файлов при старте...")
    cleanup_temp_files()
    logger.info("Бот запущен и готов к работе")

def main():
    """Запуск бота"""
    application = Application.builder().token(config.BOT_TOKEN).post_init(post_init).build()
    
    # Команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("translate", translate_command))
    application.add_handler(CommandHandler("settings", settings_command))
    
    # Обработчик сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запуск
    if config.MODE == "polling":
        logger.info("Запуск в режиме polling")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    else:
        logger.warning("Webhook режим пока не реализован, используется polling")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()