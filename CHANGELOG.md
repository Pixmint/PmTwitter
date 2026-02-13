# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-02-14

### Added
- ✨ Основной функционал бота
- 🖼️ Поддержка фото и видео (встроенно)
- 📊 Статистика твитов (лайки, репосты, просмотры)
- 💬 Цитируемые твиты с blockquote
- 📝 Опросы с прогресс-барами
- 🌐 Система перевода (15 языков)
- 💬 Комментарии пользователя как blockquote
- ⚡ Rate limiting (пользователь + чат)
- 🔒 Whitelist защита
- 🗂️ Поддержка топиков в супергруппах
- 🗑️ Автоудаление исходных сообщений в группах
- 🗜️ Сжатие медиа (Pillow + ffmpeg)

### Commands
- `/start` - Приветствие и список функций
- `/help` - Подробная справка
- `/translate` - Управление переводом
- `/settings` - Текущие настройки

### Technical
- Docker compose с security hardening
- Non-root пользователь
- Модульная архитектура (handlers, twitter, media, utils)
- Dataclass конфигурация
- HTML форматирование с escaping
- Логирование по всему коду
- Тесты (pytest)

### Supported URLs
- x.com/user/status/ID
- twitter.com/user/status/ID
- fxtwitter.com/user/status/ID
- fixupx.com/user/status/ID

### Configuration
18 параметров через .env:
- Безопасность: TELEGRAM_USER_IDS, RATE_LIMIT_*
- Группы: REPLY_IN_GROUPS, REMOVE_MESSAGE_IN_GROUPS
- Медиа: COMPRESS_MEDIA, MAX_MEDIA_MB, CAPTION_ABOVE_MEDIA
- Источник: FX_BASE_URL
- Перевод: DEFAULT_TRANSLATE_LANG
- Отладка: LOG_LEVEL, DUMP_TWEET_HTML

## [0.1.0] - Initial Development

### Added
- Базовая структура проекта
- HTML парсинг через BeautifulSoup
- FxTwitter интеграция

---

## Типы изменений
- `Added` - Новый функционал
- `Changed` - Изменения в существующем функционале
- `Deprecated` - Функционал, который будет удалён
- `Removed` - Удалённый функционал
- `Fixed` - Исправления багов
- `Security` - Исправления уязвимостей
