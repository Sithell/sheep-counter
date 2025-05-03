from ultralytics import YOLO
from functools import lru_cache

MODEL_PATH = 'models/yolo11n.pt'  # Можно заменить на нужную модель

@lru_cache(maxsize=1)
def get_model():
    return YOLO(MODEL_PATH)
