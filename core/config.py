from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    APP_NAME: str = "StyleGAN2 API"
    DEBUG: bool = True

    # model paths
    STYLEGAN2_MODEL_PATH: str = "checkpoints/StyleGAN2-256.pkl"
    REALESRGAN_MODEL_PATH: str = "Real-ESRGAN/weights/RealESRGAN_x4plus.pth"

    # generation settings
    DEFAULT_SEED: int = 42
    DEFAULT_TRUNCATION: float = 0.5
    MAX_BATCH_SIZE: int = 64

    # API settings
    ALLOWED_HOSTS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    RATE_LIMIT_PER_MINUTE: int = 60

settings = Settings()