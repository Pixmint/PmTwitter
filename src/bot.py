import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from src.config import config
from src.handlers.commands import start, status
from src.handlers.callbacks import handle_callback_query
from src.handlers.messages import handle_message
from src.media.cleanup import cleanup_temp_files
from src.utils.rate_limit import rate_limiter

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, config.LOG_LEVEL)
)
logger = logging.getLogger(__name__)

async def cleanup_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Периодическая очистка временных файлов и rate limiter"""
    logger.info("Запуск периодической очистки...")
    cleanup_temp_files(max_age_seconds=3600)
    rate_limiter.cleanup_old_entries(max_age=3600)
    logger.info("Периодическая очистка завершена")

async def post_init(application: Application) -> None:
    """Инициализация после запуска бота"""
    logger.info("Очистка временных файлов при старте...")
    cleanup_temp_files()
    logger.info("Бот запущен и готов к работе")

def main():
    """Запуск бота"""
    application = Application.builder().token(config.BOT_TOKEN).post_init(post_init).build()
    
    # Команды (только /start и /status)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))
    
    # Обработчик callback запросов от inline кнопок
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    
    # Обработчик сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Периодическая очистка (каждый час)
    application.job_queue.run_repeating(
        cleanup_job,
        interval=3600,  # 1 час
        first=60  # Первый запуск через минуту
    )
    
    # Запуск
    if config.MODE == "polling":
        logger.info("Запуск в режиме polling")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    else:
        logger.warning("Webhook режим пока не реализован, используется polling")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()