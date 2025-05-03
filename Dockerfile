FROM python:3.9-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY main.py worker.py model.py job_queue.py ./

# Создание папок для файлов
RUN mkdir -p uploads static

# Создание пустого файла очереди
RUN echo '[]' > jobs.json

# Запуск сервера и воркера
CMD ["sh", "-c", "python worker.py & uvicorn main:app --host 0.0.0.0 --port 8000"] 