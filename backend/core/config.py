from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # Application
    PROJECT_NAME: str = "Meeting Minutes AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "sqlite:///./meeting_minutes.db"
    REDIS_URL: str = "redis://localhost:6379"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    # AI Services
    OPENAI_API_KEY: str = ""
    HUGGINGFACE_API_TOKEN: str = ""
    PYANNOTE_ACCESS_TOKEN: str = ""
    
    # File Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 500000000  # 500MB
    SUPPORTED_FORMATS: List[str] = ["wav", "mp3", "flac", "m4a", "ogg", "webm"]
    
    # Audio Processing
    DEFAULT_SAMPLE_RATE: int = 16000
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()