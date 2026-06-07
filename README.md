# 🐦 PMTwitter Bot

Telegram бот для просмотра твитов из X/Twitter с красивым оформлением, медиа и переводом.

![Python](https://img.shields.io/badge/python-3.12-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Docker](https://img.shields.io/badge/docker-ready-brightgreen)
![CI](https://img.shields.io/github/actions/workflow/status/Pixmint/PmTwitter/lint-and-test.yml?branch=develop&label=CI)

## ✨ Возможности

### Основные
- 🖼️ **Медиа**: Фото и видео встроенно (не файлом)
- 📊 **Статистика**: Лайки, репосты, комментарии, просмотры
- 💬 **Цитаты**: Quoted tweets с blockquote оформлением
- 📝 **Опросы**: С прогресс-барами и статистикой
- 🌐 **Перевод**: 15 языков (автоматический через FxTwitter)
- 💬 **Комментарии**: Текст перед ссылкой сохраняется как цитата
- 🎛️ **Интерактивный UI**: Управление с помощью кнопок

### Дополнительные
- ⚡ **Rate limiting**: Защита от спама с автоочисткой (настраиваемая)
- 🔒 **Whitelist**: Ограничение доступа по ID пользователей
- 🗂️ **Топики**: Поддержка супергрупп с топиками
- 🗑️ **Автоудаление**: Исходное сообщение в группах (опционально)
- 🗜️ **Сжатие**: Автоматическое сжатие фото (Pillow) и видео (ffmpeg)
- 🎨 **Форматирование**: HTML с ссылками на профили
- 🔄 **Retry логика**: Автоматические повторы HTTP запросов
- 🧹 **Автоочистка**: Периодическое удаление временных файлов и старых записей

## 📦 Установка

### Docker (рекомендуется)

```bash
# Клонировать репозиторий
git clone https://github.com/Pixmint/PmTwitter.git
cd PmTwitter

# Создать .env файл
cp .env.example .env
nano .env  # Добавить BOT_TOKEN

# Запустить
docker compose up -d

# Просмотр логов
docker compose logs -f pmt-bot
```

### Вручную

```bash
# Python 3.12+
pip install -r requirements.txt

# ffmpeg для сжатия видео (опционально)
sudo apt install ffmpeg

# Экспорт токена
export BOT_TOKEN="your_token_here"

# Запуск (.env теперь загружается автоматически)
python -m src.bot
```

## ⚙️ Конфигурация

Все настройки через `.env` файл:

### Обязательные
```env
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz  # Токен от @BotFather
```

### Опциональные
```env
# Режим работы
MODE=polling  # polling или webhook (webhook в разработке)

# Безопасность
TELEGRAM_USER_IDS=12345,67890  # Whitelist (пусто = все)
RATE_LIMIT_SECONDS=5           # Задержка между запросами (пользователь)
RATE_LIMIT_CHAT_SECONDS=3      # Задержка между запросами (чат)

# Поведение в группах
REPLY_IN_GROUPS=1              # 1 = отвечать всегда, 0 = только при @mention
REMOVE_MESSAGE_IN_GROUPS=1     # 1 = удалять исходное сообщение
REPLY_TO_MESSAGE=0             # 1 = отвечать реплаем, 0 = обычное сообщение

# Медиа
COMPRESS_MEDIA=1               # 1 = сжимать, 0 = отправлять как есть
MAX_MEDIA_MB=20                # Макс размер медиа в МБ
CAPTION_ABOVE_MEDIA=1          # 1 = подпись сверху, 0 = снизу
INCLUDE_QUOTED_MEDIA=0         # 1 = показывать медиа из quoted tweets

# Источник данных
FX_BASE_URL=https://fxtwitter.com  # Альтернативный фронтенд

# Перевод
DEFAULT_TRANSLATE_LANG=off     # off, ru, en, es, fr, de, it, pt, ja, ko, zh и т.д.
TRANSLATE_SETTINGS_PATH=/app/data/translate_settings.json  # Постоянное хранилище настроек

# Отладка
LOG_LEVEL=INFO                 # DEBUG, INFO, WARNING, ERROR
DUMP_TWEET_HTML=0              # 1 = сохранять HTML в /tmp для отладки

# Retry логика HTTP
RETRY_MAX_ATTEMPTS=3            # Максимум попыток (включая первую)
RETRY_WAIT_MIN=0.5              # Минимальная задержка (сек)
RETRY_WAIT_MAX=4.0              # Максимальная задержка (сек)
RETRY_WAIT_MULTIPLIER=0.5       # Множитель для экспоненциальной задержки
RETRY_STATUS_CODES=408,429      # Повтор на 408, 429 и все 5xx
```

## 📱 Использование

### Команды

- `/start` — Начало работы с интерактивным меню
- `/status` — Информация о текущих настройках

### Примеры

```
# Просто отправить ссылку
https://x.com/elonmusk/status/123456789

# С комментарием
Посмотрите на это! https://x.com/user/status/123

# Несколько ссылок
https://x.com/user1/status/111
https://x.com/user2/status/222
```

### Поддерживаемые ссылки

- `x.com/user/status/123...`
- `twitter.com/user/status/123...`
- `fxtwitter.com/user/status/123...`
- `fixupx.com/user/status/123...`

## 🏗️ Архитектура

```
src/
├── bot.py              # Точка входа, инициализация
├── config.py           # Конфигурация через .env
├── handlers/
│   ├── commands.py     # /start, /help, /translate, /status
│   ├── messages.py     # Обработка ссылок на твиты
│   └── callbacks.py    # Обработка callback кнопок
├── twitter/
│   ├── fetcher.py      # HTTP клиент с retry логикой
│   ├── parser.py       # HTML парсинг (BeautifulSoup)
│   ├── normalize.py    # URL нормализация
│   ├── translate.py    # Настройки перевода
│   └── models.py       # Dataclasses (Tweet, Stats...)
├── media/
│   ├── download.py     # Скачивание медиа
│   ├── compress.py     # Сжатие (Pillow, ffmpeg)
│   └── cleanup.py      # Очистка временных файлов
└── utils/
    ├── rate_limit.py   # Rate limiting с автоочисткой
    └── text_format.py  # HTML форматирование
```

## 🧪 Тестирование

```bash
# Установить pytest
pip install pytest pytest-cov

# Запустить тесты
pytest tests/ -v

# С покрытием
pytest tests/ --cov=src --cov-report=html

# Только быстрые тесты
pytest tests/ -v -m "not slow"
```

### Continuous Integration

Проект использует GitHub Actions для автоматической проверки кода:
- **Flake8** — Проверка стиля кода
- **Black** — Форматирование кода
- **Pytest** — Запуск unit-тестов

Workflow запускается автоматически при каждом push и pull request.

## 🔒 Безопасность

- ✅ Non-root пользователь в Docker
- ✅ Read-only filesystem + tmpfs для `/tmp` и volume для `/app/data`
- ✅ Drop всех capabilities
- ✅ No new privileges
- ✅ Whitelist по Telegram ID
- ✅ Rate limiting с автоочисткой
- ✅ HTML escaping для user input
- ✅ Автоматическое закрытие файловых дескрипторов
- ✅ Периодическая очистка временных данных

## 📊 Логирование

```bash
# Docker logs
docker compose logs -f pmt-bot

# Grep для ошибок
docker compose logs pmt-bot | grep ERROR

# Последние 100 строк
docker compose logs pmt-bot --tail=100
```

Уровни логирования:
- `DEBUG` — Детальная отладка (HTML дампы, парсинг)
- `INFO` — Обычная работа (запросы, команды)
- `WARNING` — Предупреждения (недоступные твиты)
- `ERROR` — Ошибки (парсинг, сеть)

## 🐛 Известные проблемы

1. **Webhook не реализован** — Только polling режим
2. **Настройки перевода теряются** — Хранятся в `/tmp`, нужна БД
3. **Приватные твиты** — Недоступны (требуют авторизации)
4. **18+ контент** — Требует авторизацию в Twitter

## 🛠️ Разработка

### Структура веток
- `main` — Стабильная версия (production)
- `develop` — Разработка (latest features)
- `feature/*` — Новые функции

### Код-стайл
```bash
# Black formatter
black src/

# Flake8 linter
flake8 src/

# Type checking (опционально)
mypy src/
```

### Добавление новой функции

1. Создать ветку: `git checkout -b feature/my-feature`
2. Написать код
3. Добавить тесты в `tests/`
4. Запустить линтеры: `black src/ && flake8 src/`
5. Убедиться что тесты проходят: `pytest tests/ -v`
6. Обновить `CHANGELOG.md`
7. Создать PR в `develop`

## 📝 TODO

### Критические
- [ ] Использование FxTwitter API вместо HTML парсинга
- [x] Закрытие файловых дескрипторов в media group
- [x] Периодическая очистка rate_limiter
- [x] Retry логика для HTTP запросов

### Важные
- [ ] Кэширование твитов (TTLCache)
- [ ] SQLite для настроек перевода
- [ ] Graceful shutdown
- [ ] Улучшенная обработка ошибок перевода

### Желательные
- [ ] Webhook поддержка
- [ ] Метрики и статистика
- [ ] Админ команды
- [ ] Thread/Reply Chain поддержка
- [ ] Альтернативные фронтенды (vxtwitter)
- [ ] Поддержка кастомных кнопок в настройках

## 📈 Changelog

См. [CHANGELOG.md](CHANGELOG.md) для полной истории изменений.

### Последние изменения (v1.1.0)
- ✅ Интерактивный UI с кнопками
- ✅ Автоматические повторы HTTP запросов
- ✅ CI/CD pipeline с GitHub Actions
- ✅ Улучшенное форматирование переводов
- ✅ Автоочистка rate limiter и временных файлов
- ✅ Исправлена утечка файловых дескрипторов
- ✅ Команда /status с информацией о боте

## 🤝 Вклад

Контрибьюты приветствуются! См. [CONTRIBUTING.md](CONTRIBUTING.md).

### Как помочь проекту
- 🐛 Сообщайте о багах в [Issues](https://github.com/Pixmint/PmTwitter/issues)
- 💡 Предлагайте новые функции
- 📝 Улучшайте документацию
- 🧪 Пишите тесты
- 🔧 Присылайте Pull Requests

## 📄 Лицензия

MIT License - см. [LICENSE](LICENSE)

## 🙏 Благодарности

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) — Telegram Bot API
- [FxTwitter](https://github.com/FixTweet/FxTwitter) — Twitter frontend
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) — HTML парсинг
- [Pillow](https://python-pillow.org/) — Обработка изображений
- [ffmpeg](https://ffmpeg.org/) — Обработка видео

## 📮 Контакты

- Issues: [GitHub Issues](https://github.com/Pixmint/PmTwitter/issues)
- Discussions: [GitHub Discussions](https://github.com/Pixmint/PmTwitter/discussions)

---

Made with ❤️ by [VFPixDev](https://github.com/VFPixDev)