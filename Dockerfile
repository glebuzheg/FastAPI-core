# Dockerfile
FROM python:3.12-slim

# Установка uv
RUN pip install uv

# Установка рабочей директории
WORKDIR /app

# Копирование файлов зависимостей
COPY pyproject.toml .

# Установка зависимостей через uv
RUN uv pip install --system -e .

# Копирование исходного кода
COPY ./app ./app

# Команда для запуска приложения
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]