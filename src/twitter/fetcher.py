import httpx
import logging
from typing import Optional
from src.config import config

logger = logging.getLogger(__name__)

async def fetch_tweet_data(tweet_id: str, username: str, lang_code: Optional[str] = None) -> Optional[dict]:
    """Получает данные твита через FxTwitter API"""
    
    # FxTwitter предоставляет API endpoint
    api_url = f"{config.FX_BASE_URL}/api/status/{tweet_id}"
    
    logger.info(f"Запрос API твита: {api_url}")
    
    timeout = httpx.Timeout(30.0, connect=10.0)
    
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        try:
            headers = {
                'User-Agent': 'TelegramBot/1.0',
                'Accept': 'application/json'
            }
            
            if lang_code:
                headers['Accept-Language'] = lang_code
            
            response = await client.get(api_url, headers=headers)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    logger.debug(f"Получены данные: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                    return data
                except Exception as e:
                    logger.error(f"Ошибка парсинга JSON: {e}")
                    return None
            elif response.status_code == 404:
                logger.warning(f"Твит не найден: {api_url}")
                return None
            elif response.status_code in [403, 401]:
                logger.warning(f"Твит недоступен: {api_url}")
                return None
            else:
                logger.error(f"Ошибка HTTP {response.status_code}: {api_url}")
                return None
                
        except httpx.TimeoutException:
            logger.error(f"Таймаут при запросе: {api_url}")
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении твита: {e}")
            return None

async def fetch_tweet_html(tweet_id: str, username: str, lang_code: Optional[str] = None) -> Optional[str]:
    """Получает HTML страницы твита через FxTwitter/FixupX (fallback)"""
    
    base_url = f"{config.FX_BASE_URL}/{username}/status/{tweet_id}"
    if lang_code:
        url = f"{base_url}/{lang_code}"
    else:
        url = base_url
    
    logger.info(f"Запрос HTML твита: {url}")
    
    timeout = httpx.Timeout(30.0, connect=10.0)
    
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        try:
            response = await client.get(url, headers={
                'User-Agent': 'TelegramBot/1.0 (compatible; +https://t.me/your_bot)'
            })
            
            if response.status_code == 200:
                return response.text
            elif response.status_code == 404:
                logger.warning(f"Твит не найден: {url}")
                return None
            elif response.status_code in [403, 401]:
                logger.warning(f"Твит недоступен (приватный/18+): {url}")
                return None
            else:
                logger.error(f"Ошибка HTTP {response.status_code}: {url}")
                return None
                
        except httpx.TimeoutException:
            logger.error(f"Таймаут при запросе: {url}")
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении твита: {e}")
            return None

async def download_media(url: str) -> Optional[bytes]:
    """Скачивает медиа файл"""
    timeout = httpx.Timeout(60.0, connect=10.0)
    
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        try:
            response = await client.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if response.status_code == 200:
                return response.content
            else:
                logger.error(f"Ошибка загрузки медиа {response.status_code}: {url}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при загрузке медиа: {e}")
            return None