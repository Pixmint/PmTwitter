FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg libjpeg62-turbo \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 10001 appuser
WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY src /app/src
RUN mkdir -p /app/data /tmp

ENV PYTHONPATH=/app/src
USER appuser

CMD ["python", "-m", "bot"]
