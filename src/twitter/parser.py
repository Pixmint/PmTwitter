import json
import re
import logging
from datetime import datetime
from typing import Optional
from bs4 import BeautifulSoup
from src.twitter.models import Tweet, TweetStats, MediaItem, QuotedTweet, Poll, PollOption

logger = logging.getLogger(__name__)

def parse_number(text: Optional[str]) -> Optional[int]:
    """Парсит число из текста (поддерживает K, M)"""
    if not text:
        return None
    
    text = text.strip().upper().replace(',', '').replace(' ', '')
    
    multipliers = {'K': 1000, 'M': 1000000, 'B': 1000000000}
    
    for suffix, mult in multipliers.items():
        if suffix in text:
            try:
                num = float(text.replace(suffix, ''))
                return int(num * mult)
            except ValueError:
                return None
    
    try:
        return int(text)
    except ValueError:
        return None

def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Парсит дату из различных форматов"""
    if not date_str:
        return None
    
    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
        "%d.%m.%Y %H:%M",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None

def extract_json_ld(soup: BeautifulSoup) -> Optional[dict]:
    """Извлекает JSON-LD данные из HTML"""
    script = soup.find('script', type='application/ld+json')
    if script and script.string:
        try:
            return json.loads(script.string)
        except json.JSONDecodeError:
            pass
    return None

def extract_og_meta(soup: BeautifulSoup, property_name: str) -> Optional[str]:
    """Извлекает Open Graph meta теги"""
    tag = soup.find('meta', property=property_name)
    if tag and tag.get('content'):
        return tag['content']
    return None

def parse_poll_from_html(soup: BeautifulSoup) -> Optional[Poll]:
    """Парсит опрос из HTML"""
    # Ищем элементы опроса
    poll_question = soup.find('div', class_=re.compile('poll-question|poll-title'))
    poll_options = soup.find_all('div', class_=re.compile('poll-option|poll-choice'))
    
    if not poll_question or not poll_options:
        return None
    
    question = poll_question.get_text(strip=True)
    options = []
    total_votes = 0
    
    for option_div in poll_options:
        text = option_div.find(class_=re.compile('option-text|choice-text'))
        percent = option_div.find(class_=re.compile('option-percent|choice-percent'))
        votes = option_div.find(class_=re.compile('option-votes|choice-votes'))
        
        if text:
            option_text = text.get_text(strip=True)
            option_percent = 0.0
            option_votes = 0
            
            if percent:
                percent_text = percent.get_text(strip=True).replace('%', '')
                try:
                    option_percent = float(percent_text)
                except ValueError:
                    pass
            
            if votes:
                option_votes = parse_number(votes.get_text(strip=True)) or 0
                total_votes += option_votes
            
            options.append(PollOption(text=option_text, votes=option_votes, percent=option_percent))
    
    # Статус опроса
    status_elem = soup.find(class_=re.compile('poll-status|poll-state'))
    is_ended = False
    time_left = None
    
    if status_elem:
        status_text = status_elem.get_text(strip=True).lower()
        is_ended = 'ended' in status_text or 'завершён' in status_text or 'closed' in status_text
        if not is_ended and ('left' in status_text or 'осталось' in status_text):
            time_left = status_text
    
    if options:
        return Poll(
            question=question,
            options=options,
            total_votes=total_votes,
            is_ended=is_ended,
            time_left=time_left
        )
    
    return None

def parse_tweet_html(html: str, original_url: str) -> Optional[Tweet]:
    """Парсит HTML страницы твита"""
    soup = BeautifulSoup(html, 'lxml')
    
    # Пробуем JSON-LD
    json_ld = extract_json_ld(soup)
    
    # Извлекаем базовые данные
    display_name = extract_og_meta(soup, 'og:title') or extract_og_meta(soup, 'twitter:title') or "Неизвестно"
    
    # Username из URL или meta
    username_match = re.search(r'@(\w+)', display_name)
    username = username_match.group(1) if username_match else extract_og_meta(soup, 'twitter:site')
    if username and username.startswith('@'):
        username = username[1:]
    
    # Текст твита
    text = extract_og_meta(soup, 'og:description') or extract_og_meta(soup, 'twitter:description') or ""
    
    # Дата
    date_str = extract_og_meta(soup, 'article:published_time')
    date = parse_date(date_str) if date_str else datetime.now()
    
    # Медиа
    media = []
    
    # Видео
    video_url = extract_og_meta(soup, 'og:video') or extract_og_meta(soup, 'twitter:player:stream')
    if video_url:
        media.append(MediaItem(type='video', url=video_url))
    
    # Фото
    image_url = extract_og_meta(soup, 'og:image') or extract_og_meta(soup, 'twitter:image')
    if image_url and not video_url:  # Не добавляем превью видео как фото
        media.append(MediaItem(type='photo', url=image_url))
    
    # Дополнительные фото из meta
    for img_tag in soup.find_all('meta', property=re.compile('twitter:image:')):
        img_url = img_tag.get('content')
        if img_url and img_url not in [m.url for m in media]:
            media.append(MediaItem(type='photo', url=img_url))
    
    # Статистика - парсим из текста или элементов
    stats = TweetStats()
    
    stats_text = soup.find(class_=re.compile('stats|statistics|tweet-stats'))
    if stats_text:
        stats_str = stats_text.get_text()
        
        replies_match = re.search(r'(\d+[KMB]?)\s*(?:replies|ответ|комм)', stats_str, re.I)
        if replies_match:
            stats.replies = parse_number(replies_match.group(1))
        
        reposts_match = re.search(r'(\d+[KMB]?)\s*(?:repost|retweet|репост)', stats_str, re.I)
        if reposts_match:
            stats.reposts = parse_number(reposts_match.group(1))
        
        likes_match = re.search(r'(\d+[KMB]?)\s*(?:like|лайк)', stats_str, re.I)
        if likes_match:
            stats.likes = parse_number(likes_match.group(1))
        
        views_match = re.search(r'(\d+[KMB]?)\s*(?:view|просмотр)', stats_str, re.I)
        if views_match:
            stats.views = parse_number(views_match.group(1))
    
    # Опрос
    poll = parse_poll_from_html(soup)
    
    # Quoted tweet (упрощённо)
    quoted = None
    quoted_div = soup.find(class_=re.compile('quoted-tweet|quote'))
    if quoted_div:
        quoted_author = quoted_div.find(class_=re.compile('author|name'))
        quoted_text_elem = quoted_div.find(class_=re.compile('text|content'))
        
        if quoted_author and quoted_text_elem:
            quoted_name = quoted_author.get_text(strip=True)
            quoted_text = quoted_text_elem.get_text(strip=True)
            quoted = QuotedTweet(
                display_name=quoted_name,
                username=quoted_name.split('@')[-1] if '@' in quoted_name else quoted_name,
                url=original_url,
                text=quoted_text
            )
    
    # Перевод (если есть в HTML)
    translated_text = None
    source_language = None
    
    translation_div = soup.find(class_=re.compile('translation|translated'))
    if translation_div:
        translated_text = translation_div.get_text(strip=True)
        
        lang_elem = soup.find(class_=re.compile('source-lang|original-lang'))
        if lang_elem:
            source_language = lang_elem.get_text(strip=True)
    
    return Tweet(
        display_name=display_name.split('(@')[0].strip() if '(@' in display_name else display_name,
        username=username or "unknown",
        url=original_url,
        text=text,
        date=date,
        media=media,
        quoted_tweet=quoted,
        stats=stats,
        poll=poll,
        translated_text=translated_text,
        source_language=source_language
    )