# Sheep Counter

Проект для детекции объектов на изображениях с помощью YOLO и FastAPI.

## Структура проекта

```
sheep-counter/
├── main.py            # FastAPI сервер
├── worker.py          # Фоновый обработчик задач
├── model.py           # Загрузка YOLO модели
├── job_queue.py       # Работа с JSON-очередью
├── static/            # Обработанные изображения
├── uploads/           # Загруженные оригиналы
├── jobs.json          # Очередь задач
└── requirements.txt   # Зависимости
```

## Установка и запуск

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Подготовка модели YOLO

- Скачайте файл с весами модели (например, `yolov11n.pt`) и положите его в корень проекта.
- В файле `model.py` укажите путь к модели:

```python
MODEL_PATH = 'yolov11n.pt'  # Или другой путь к вашей модели
```

### 3. Запуск сервера

```bash
uvicorn main:app --reload
```

### 4. Запуск воркера

```bash
python worker.py
```

## Запуск через Docker

### 1. Сборка образа

```bash
docker build -t sheep-counter .
```

### 2. Запуск контейнера

```bash
docker run -p 8000:8000 sheep-counter
```

## Тестирование через curl

### 1. Загрузка изображения

```bash
curl -X POST "http://localhost:8000/job" \
  -H "accept: application/json" \
  -F "file=@example.png"
```

### 2. Получение статуса задачи

```bash
curl "http://localhost:8000/job?id=<job_id>"
```

### 3. Просмотр обработанного изображения

```
http://localhost:8000/static/<job_id>.jpg
```

## Примечания

- Убедитесь, что файл с весами модели (`*.pt`) находится в корне проекта.
- Веса можно скачать на сайте [Ultralitics](https://docs.ultralytics.com/models/yolo11/#performance-metrics)
