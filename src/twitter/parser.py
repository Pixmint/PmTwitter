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
    
    # Debug: проверяем что пришло
    title = soup.find('title')
    logger.debug(f"HTML Title: {title.string if title else 'None'}")
    
    # Извлекаем базовые данные из Open Graph
    author_title = extract_og_meta(soup, 'og:title') or ""
    logger.debug(f"og:title: {author_title}")
    
    # Парсим имя и username
    display_name = author_title
    username = "unknown"
    
    # Пытаемся извлечь username из разных мест
    if " (@" in author_title:
        parts = author_title.split(" (@")
        display_name = parts[0].strip()
        username = parts[1].rstrip(')').strip()
    else:
        # Из URL
        username_match = re.search(r'x\.com/([^/]+)/status', original_url)
        if username_match:
            username = username_match.group(1)
    
    logger.debug(f"Parsed: name={display_name}, username={username}")
    
    # Текст твита из description
    text = extract_og_meta(soup, 'og:description') or extract_og_meta(soup, 'twitter:description') or ""
    logger.debug(f"Text length: {len(text)}")
    
    # Проверяем если это ретвит/цитата (содержит "Quoting")
    quoted = None
    if "Quoting" in text:
        logger.debug(f"Detected quoting tweet")
        # Парсим quoted tweet из текста
        # Формат: "текст" Quoting @username Quoted text
        quoting_pos = text.find("Quoting")
        
        if quoting_pos > 0:
            # Текст до Quoting это текст основного твита
            main_text = text[:quoting_pos].strip()
            
            # Текст после Quoting это информация о цитируемом твите
            quoting_text = text[quoting_pos + len("Quoting"):].strip()
            
            # Парсим Quoting текст вида: "💜🌙 𝘾𝙖𝙩𝙣𝙖𝙥✨💜 (@username) \n "quoted text" \n extra text"
            lines = quoting_text.split('\n')
            
            quoted_author = None
            quoted_content = []
            quoted_display = None
            
            logger.debug(f"Quoting text has {len(lines)} lines")
            
            if lines:
                # Первая строка содержит имя и username
                first_line = lines[0].strip()
                logger.debug(f"First line of quoted: {first_line[:50]}")
                # Ищем username в скобках
                username_match = re.search(r'@([a-zA-Z0-9_]+)', first_line)
                
                if username_match:
                    username = username_match.group(1)
                    quoted_author = username
                    quoted_display = first_line.replace(f"(@{username})", "").strip()
                    logger.debug(f"Extracted quoted author: {username}")
                else:
                    quoted_display = first_line
                    logger.debug(f"No username found in first line")
                
                # Остальные строки это quoted текст
                for line in lines[1:]:
                    line = line.strip()
                    if line and not line.startswith('http'):  # Пропускаем пустые и ссылки
                        quoted_content.append(line)
                
                logger.debug(f"Quoted content has {len(quoted_content)} lines, author={quoted_author}")
            
            if quoted_author and quoted_content:
                quoted_text = " ".join(quoted_content)
                quoted = QuotedTweet(
                    display_name=quoted_display or quoted_author,
                    username=quoted_author,
                    url=original_url,  # Используем оригинальный URL
                    text=quoted_text
                )
                logger.debug(f"Parsed quoted tweet: author={quoted_author}, text={quoted_text[:50]}")
            
            # НЕ заменяем текст - оставляем весь контент как есть, quoted будет отображён отдельно в цитате
    
    # Убираем prefix автора из текста если есть
    if display_name and text.startswith(display_name):
        text = text[len(display_name):].lstrip(': ')
    
    # Дата
    date_str = extract_og_meta(soup, 'article:published_time')
    date = parse_date(date_str) if date_str else datetime.now()
    
    # Медиа
    media = []
    
    # Видео
    video_url = extract_og_meta(soup, 'og:video') or extract_og_meta(soup, 'twitter:player:stream')
    if video_url and not video_url.startswith('blob:'):
        logger.debug(f"Found video: {video_url}")
        media.append(MediaItem(type='video', url=video_url))
    
    # Фото (может быть мозаика или отдельное изображение)
    image_url = extract_og_meta(soup, 'og:image') or extract_og_meta(soup, 'twitter:image')
    if image_url:
        # Пропускаем если это фото профиля (profile_images в URL)
        if 'profile_images' in image_url:
            logger.debug(f"Skipping profile image: {image_url}")
            image_url = None
        # Проверяем если это мозаика fxtwitter
        elif 'mosaic.fxtwitter.com' in image_url:
            logger.debug(f"Found mosaic image: {image_url}")
            # Парсим мозаику и создаем отдельные ссылки
            # URL формата: https://mosaic.fxtwitter.com/jpeg/TWEET_ID/PHOTO_ID1/PHOTO_ID2/...
            parts = image_url.split('/')
            photo_ids = parts[5:]  # Все ID после tweet_id
            
            for photo_id in photo_ids:
                if photo_id:  # Проверяем что не пусто
                    # Создаем ссылку на оригинальное фото из Twitter
                    twitter_photo_url = f"https://pbs.twimg.com/media/{photo_id}?format=jpg&name=orig"
                    media.append(MediaItem(type='photo', url=twitter_photo_url))
                    logger.debug(f"Added photo from mosaic: {photo_id}")
        elif image_url:
            # Обычное одиночное фото
            logger.debug(f"Found image: {image_url}")
            media.append(MediaItem(type='photo', url=image_url))
        
        # Дополнительные фото (только если нет видео)
        if not video_url:
            for i in range(1, 5):
                img_url = extract_og_meta(soup, f'twitter:image:{i}') or extract_og_meta(soup, f'og:image:{i}')
                if img_url and img_url not in [m.url for m in media]:
                    logger.debug(f"Found additional image: {img_url}")
                    media.append(MediaItem(type='photo', url=img_url))
    
    logger.debug(f"Total media items: {len(media)}")
    
    # Статистика - ищем в мета тегах или структурированных данных
    stats = TweetStats()
    
    # Сначала пытаемся найти в owoembed ссылке
    oembed_link = soup.find('link', rel='alternate', type='application/json+oembed')
    logger.debug(f"oembed_link found: {oembed_link is not None}")
    
    if oembed_link:
        oembed_url = oembed_link.get('href')
        logger.debug(f"oembed_url: {oembed_url[:100] if oembed_url else 'None'}")
        
        if oembed_url:
            from urllib.parse import urlparse, parse_qs, unquote
            parsed_url = urlparse(oembed_url)
            params = parse_qs(parsed_url.query)
            logger.debug(f"params keys: {list(params.keys())}")
            
            if 'text' in params:
                stats_text = unquote(params['text'][0])
                logger.debug(f"Found stats text: {stats_text}")
                
                # Парсим текст вида: "💬 239   🔁 23.0K   ❤️ 144.8K   👁️ 1.49M"
                
                # Replies (💬)
                replies_match = re.search(r'💬\s+([\d.KMB]+)', stats_text)
                if replies_match:
                    stats.replies = parse_number(replies_match.group(1))
                    logger.debug(f"Parsed replies: {stats.replies}")
                
                # Reposts (🔁)
                reposts_match = re.search(r'🔁\s+([\d.KMB]+)', stats_text)
                if reposts_match:
                    stats.reposts = parse_number(reposts_match.group(1))
                    logger.debug(f"Parsed reposts: {stats.reposts}")
                
                # Likes (❤️)
                likes_match = re.search(r'❤️?\s+([\d.KMB]+)', stats_text)
                if likes_match:
                    stats.likes = parse_number(likes_match.group(1))
                    logger.debug(f"Parsed likes: {stats.likes}")
                
                # Views (👁️)
                views_match = re.search(r'👁️?\s+([\d.KMB]+)', stats_text)
                if views_match:
                    stats.views = parse_number(views_match.group(1))
                    logger.debug(f"Parsed views: {stats.views}")
    
    # Пытаемся найти JSON-LD если owoembed не сработал
    if stats.replies is None:
        json_ld = extract_json_ld(soup)
        if json_ld and isinstance(json_ld, dict):
            interaction = json_ld.get('interactionStatistic', [])
            if isinstance(interaction, list):
                for stat in interaction:
                    if isinstance(stat, dict):
                        stat_type = stat.get('interactionType', '')
                        value = stat.get('userInteractionCount')
                        
                        if 'Comment' in stat_type or 'Reply' in stat_type:
                            stats.replies = parse_number(str(value))
                        elif 'Share' in stat_type:
                            stats.reposts = parse_number(str(value))
                        elif 'Like' in stat_type:
                            stats.likes = parse_number(str(value))
    
    logger.debug(f"Stats: replies={stats.replies}, reposts={stats.reposts}, likes={stats.likes}, views={stats.views}")
    
    # Views из мета тега (если есть)
    views_meta = soup.find('meta', attrs={'name': 'twitter:views'})
    if views_meta:
        stats.views = parse_number(views_meta.get('content', ''))
    
    # Опрос
    poll = parse_poll_from_html(soup)
    if poll:
        logger.debug(f"Found poll with {len(poll.options)} options")
    
    # Перевод
    translated_text = None
    source_language = None
    
    translation_div = soup.find('div', class_=re.compile('translation|translated'))
    if translation_div:
        translated_text = translation_div.get_text(strip=True)
        
        lang_elem = soup.find(class_=re.compile('source-lang|original-lang'))
        if lang_elem:
            source_language = lang_elem.get_text(strip=True)
    
    return Tweet(
        display_name=display_name,
        username=username,
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