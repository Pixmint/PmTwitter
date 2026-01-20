import logging

from telegram.ext import Application, CommandHandler, MessageHandler, filters

from config import load_config
from handlers.commands import start_cmd, help_cmd, translate_cmd, settings_cmd
from handlers.messages import message_handler
from media.cleanup import cleanup_temp
from utils.rate_limit import RateLimiter
from utils.settings import SettingsStore


async def _post_init(application: Application) -> None:
    application.bot_data["rate_limiter"] = RateLimiter()
    application.bot_data["settings_store"] = SettingsStore()
    await application.bot_data["settings_store"].load()
    await cleanup_temp()


async def _post_stop(application: Application) -> None:
    store = application.bot_data.get("settings_store")
    if store:
        await store.save()


def main() -> None:
    config = load_config()

    logging.basicConfig(
        level=getattr(logging, config.log_level.upper(), logging.INFO),
        format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    )

    application = Application.builder().token(config.bot_token).post_init(_post_init).post_stop(_post_stop).build()
    application.bot_data["config"] = config

    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("translate", translate_cmd))
    application.add_handler(CommandHandler("settings", settings_cmd))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    if config.mode == "polling":
        application.run_polling(close_loop=False, poll_interval=5.0)
    else:
        raise RuntimeError("Поддержан только MODE=polling в этом шаблоне")


if __name__ == "__main__":
    main()
