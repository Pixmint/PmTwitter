import httpx
import logging
from typing import Optional
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from src.config import config

logger = logging.getLogger(__name__)

RETRY_STATUS_CODES = set(config.RETRY_STATUS_CODES)


def _is_retry_status(status_code: int) -> bool:
    return status_code in RETRY_STATUS_CODES or 500 <= status_code < 600


@retry(
    reraise=True,
    stop=stop_after_attempt(config.RETRY_MAX_ATTEMPTS),
    wait=wait_exponential(
        multiplier=config.RETRY_WAIT_MULTIPLIER,
        min=config.RETRY_WAIT_MIN,
        max=config.RETRY_WAIT_MAX,
    ),
    retry=retry_if_exception_type((
        httpx.TimeoutException,
        httpx.RequestError,
        httpx.HTTPStatusError,
    )),
    before_sleep=before_sleep_log(logger, logging.WARNING),
)
async def _get_with_retry(client: httpx.AsyncClient, url: str, headers: dict) -> httpx.Response:
    response = await client.get(url, headers=headers)
    if _is_retry_status(response.status_code):
        raise httpx.HTTPStatusError(
            f"Retryable HTTP {response.status_code}",
            request=response.request,
            response=response,
        )
    return response

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
            
            response = await _get_with_retry(client, api_url, headers)
            
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
        except httpx.HTTPStatusError as e:
            status = e.response.status_code if e.response else "unknown"
            logger.error(f"Ошибка HTTP {status}: {api_url}")
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
            response = await _get_with_retry(client, url, {
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
        except httpx.HTTPStatusError as e:
            status = e.response.status_code if e.response else "unknown"
            logger.error(f"Ошибка HTTP {status}: {url}")
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении твита: {e}")
            return None

async def download_media(url: str) -> Optional[bytes]:
    """Скачивает медиа файл"""
    timeout = httpx.Timeout(60.0, connect=10.0)
    
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        try:
            response = await _get_with_retry(client, url, {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if response.status_code == 200:
                return response.content
            else:
                logger.error(f"Ошибка загрузки медиа {response.status_code}: {url}")
                return None
                
        except httpx.HTTPStatusError as e:
            status = e.response.status_code if e.response else "unknown"
            logger.error(f"Ошибка загрузки медиа {status}: {url}")
            return None
        except Exception as e:
            logger.error(f"Ошибка при загрузке медиа: {e}")
            return None