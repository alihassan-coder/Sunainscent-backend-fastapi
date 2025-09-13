import os
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    mongodb_url: str = os.getenv("MONGODB_URL", "")
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_expiration_time: int = int(os.getenv("JWT_EXPIRATION_TIME", 1440))  # minutes
    api_v1_str: str = os.getenv("API_V1_STR", "/api/v1")
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()