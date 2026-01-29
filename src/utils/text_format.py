import re
from datetime import datetime
from src.twitter.models import Tweet, Poll
from html import escape

def clean_tweet_text(text: str) -> str:
    """Очищает текст твита от HTML тегов и форматирует его"""
    if not text:
        return ""
    
    # Сначала убираем HTML теги типа <br>, <br/>
    text = re.sub(r'<br\s*/?>', '\n', text)
    
    # Теперь экранируем HTML символы
    text = escape(text)
    
    # Заменяем @mention на ссылку на профиль (после экранирования)
    def replace_mention(match):
        username = match.group(1)
        return f'<a href="https://x.com/{username}">@{username}</a>'
    
    text = re.sub(r'@([a-zA-Z0-9_]+)', replace_mention, text)
    
    return text

def format_number(num: int) -> str:
    """Форматирует число с разделителями"""
    if num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M".replace('.0M', 'M')
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K".replace('.0K', 'K')
    return str(num)

def format_date(dt: datetime) -> str:
    """Форматирует дату в формат DD.MM.YYYY, HH:MM"""
    return dt.strftime("%d.%m.%Y"), dt.strftime("%H:%M")

def create_progress_bar(percent: float, length: int = 20) -> str:
    """Создаёт прогресс-бар из символов"""
    filled = int((percent / 100) * length)
    empty = length - filled
    return "█" * filled + "░" * empty

def format_poll(poll: Poll) -> str:
    """Форматирует опрос"""
    lines = [f"<b>{escape(poll.question)}</b>\n"]
    
    for option in poll.options:
        bar = create_progress_bar(option.percent)
        votes_text = format_number(option.votes) if option.votes > 0 else ""
        
        # Форматируем как на скрине: название  процент%  прогресс-бар
        option_line = f"{escape(option.text)}  {option.percent:.0f}%  {bar}"
        if votes_text:
            option_line += f"  ({votes_text})"
        
        lines.append(f"<code>{option_line}</code>")
    
    # Итоговая информация
    total_text = format_number(poll.total_votes) if poll.total_votes > 0 else "0"
    
    if poll.is_ended:
        status = "завершён"
    elif poll.time_left:
        status = poll.time_left
    else:
        status = "идёт голосование"
    
    lines.append(f"\n{total_text} голосов · {status}")
    
    return "\n".join(lines)

def format_tweet_card(tweet: Tweet, include_translation: bool = False, user_comment: str = None) -> str:
    """Форматирует карточку твита"""
    date_str, time_str = format_date(tweet.date)
    
    # Комментарий пользователя если он есть
    lines = []
    if user_comment:
        lines.append(f"<blockquote>{escape(user_comment)}</blockquote>")
        lines.append("")
    
    # Первая строка: автор, username, дата
    lines.append(
        f'{escape(tweet.display_name)} (<a href="https://x.com/{escape(tweet.username)}">@{escape(tweet.username)}</a>) — {date_str}, {time_str}'
    )
    lines.append("")
    
    # Перевод (если есть)
    if include_translation and tweet.translated_text:
        if tweet.source_language:
            lines.append(f'<i>Переведено с {escape(tweet.source_language)}</i>')
        lines.append(escape(tweet.translated_text))
        lines.append("")
        
        # Оригинал ниже
        if tweet.text:
            lines.append(f'<i>Оригинал:</i>')
            cleaned_text = clean_tweet_text(tweet.text)
            lines.append(cleaned_text)
            lines.append("")
    else:
        # Только оригинальный текст
        if tweet.text:
            # Проверяем если есть "Quoting" - берём только текст ДО него
            text_to_display = tweet.text
            if "Quoting" in text_to_display:
                quoting_pos = text_to_display.find("Quoting")
                text_to_display = text_to_display[:quoting_pos].strip()
            
            if text_to_display:  # Отправляем только если есть текст до Quoting
                cleaned_text = clean_tweet_text(text_to_display)
                lines.append(cleaned_text)
    
    # Quoted tweet - blockquote
    if tweet.quoted_tweet:
        q = tweet.quoted_tweet
        q_date_str = ""
        if q.date:
            q_date, q_time = format_date(q.date)
            q_date_str = f" — {q_date}, {q_time}"
        
        # Blockquote для quoted
        quoted_lines = []
        quoted_lines.append(f'{escape(q.display_name)} (<a href="https://x.com/{escape(q.username)}">@{escape(q.username)}</a>){q_date_str}')
        
        # Quoted текст внутри blockquote
        cleaned_q_text = clean_tweet_text(q.text)
        quoted_lines.append(cleaned_q_text)
        
        quoted_content = '\n'.join(quoted_lines)
        lines.append(f"<blockquote>{quoted_content}</blockquote>")
    else:
        # Если нет quoted_tweet объекта, ищем "Quoting" в тексте и оформляем как blockquote
        if "Quoting" in (tweet.text or ""):
            # Находим позицию Quoting и берём текст после неё
            quoting_pos = tweet.text.find("Quoting")
            if quoting_pos >= 0:
                quoting_text = tweet.text[quoting_pos + len("Quoting"):].strip()
                if quoting_text:
                    # Очищаем текст: убираем <br>, экранируем
                    quoting_text = re.sub(r'<br\s*/?>', '\n', quoting_text)
                    quoting_text = escape(quoting_text)
                    lines.append(f"<blockquote>{quoting_text}</blockquote>")
    
    lines.append("")  # Пустая строка перед статистикой
    
    # Опрос (если есть) - ДО статистики
    if tweet.poll:
        lines.append(format_poll(tweet.poll))
        lines.append("")
    
    # Статистика
    stats = tweet.stats
    stats_parts = []
    
    if stats.replies is not None:
        stats_parts.append(f"💬 {format_number(stats.replies)}")
    else:
        stats_parts.append("💬 —")
    
    if stats.reposts is not None:
        stats_parts.append(f"🔁 {format_number(stats.reposts)}")
    else:
        stats_parts.append("🔁 —")
    
    if stats.likes is not None:
        stats_parts.append(f"❤️ {format_number(stats.likes)}")
    else:
        stats_parts.append("❤️ —")
    
    if stats.views is not None:
        stats_parts.append(f"👁 {format_number(stats.views)}")
    else:
        stats_parts.append("👁 —")
    
    lines.append("  ".join(stats_parts))
    lines.append("")
    
    # Нижняя строка - ссылка на оригинал
    lines.append(f'<i>Оригинал: <a href="{tweet.url}">открыть пост</a></i>')
    
    return "\n".join(lines)

def shorten_text_for_caption(text: str, max_length: int = 1024) -> tuple[str, bool]:
    """Укорачивает текст для caption, возвращает (текст, был_обрезан)"""
    if len(text) <= max_length:
        return text, False
    
    # Обрезаем с многоточием
    return text[:max_length - 3] + "...", True