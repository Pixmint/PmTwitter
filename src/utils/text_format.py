from datetime import datetime
from src.twitter.models import Tweet, Poll
from html import escape

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

def format_tweet_card(tweet: Tweet, include_translation: bool = False) -> str:
    """Форматирует карточку твита"""
    date_str, time_str = format_date(tweet.date)
    
    # Первая строка: автор, username, дата
    lines = [
        f'{escape(tweet.display_name)} (<a href="{tweet.url}">@{escape(tweet.username)}</a>) — {date_str}, {time_str}\n'
    ]
    
    # Перевод (если есть)
    if include_translation and tweet.translated_text:
        if tweet.source_language:
            lines.append(f'<i>Переведено с {escape(tweet.source_language)}</i>\n')
        lines.append(escape(tweet.translated_text) + "\n")
        
        # Оригинал ниже
        if tweet.text:
            lines.append(f'<i>Оригинал:</i>')
            lines.append(escape(tweet.text) + "\n")
    else:
        # Только оригинальный текст
        if tweet.text:
            lines.append(escape(tweet.text) + "\n")
    
    # Quoted tweet
    if tweet.quoted_tweet:
        q = tweet.quoted_tweet
        q_date_str = ""
        if q.date:
            q_date, q_time = format_date(q.date)
            q_date_str = f" — {q_date}, {q_time}"
        
        lines.append(
            f'\n<b>Цитата {escape(q.display_name)} (<a href="{q.url}">@{escape(q.username)}</a>){q_date_str}:</b>'
        )
        
        # Quoted текст с вертикальной чертой
        for line in q.text.split('\n'):
            lines.append(f"│ {escape(line)}")
        lines.append("")
    
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
    
    # Нижняя строка - ссылка на оригинал
    lines.append(f'\n<i>Оригинал: <a href="{tweet.url}">открыть пост</a></i>')
    
    return "\n".join(lines)

def shorten_text_for_caption(text: str, max_length: int = 1024) -> tuple[str, bool]:
    """Укорачивает текст для caption, возвращает (текст, был_обрезан)"""
    if len(text) <= max_length:
        return text, False
    
    # Обрезаем с многоточием
    return text[:max_length - 3] + "...", True