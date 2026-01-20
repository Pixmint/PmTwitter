from telegram import Message


def get_thread_id(message: Message | None) -> int | None:
    if not message:
        return None
    return getattr(message, "message_thread_id", None)
