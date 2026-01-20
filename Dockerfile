FROM python:3.12-slim

# Устанавливаем ffmpeg для сжатия видео (опционально)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Создаём не-root пользователя
RUN useradd -m -u 1000 botuser && \
    mkdir -p /tmp && \
    chown -R botuser:botuser /tmp

WORKDIR /app

# Копируем requirements
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . .

# Переключаемся на не-root пользователя
USER botuser

# Временная директория
VOLUME ["/tmp"]

# Запуск
CMD ["python", "-m", "src.bot"]