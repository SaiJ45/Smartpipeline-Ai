from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables via .env file."""
    
    # Environment variables
    DATABASE_URL: str
    PINECONE_API_KEY: str
    PINECONE_INDEX: str
    GROQ_API_KEY: str
    JWT_SECRET: str
    MLFLOW_TRACKING_URI: str
    
    # Regular class attributes
    CHUNK_SIZE: int = 10000
    PINECONE_SAMPLE_SIZE: int = 100000
    
    class Config:
        """Pydantic config for loading .env file."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    The settings are loaded from the .env file only once,
    then cached for subsequent calls using lru_cache.
    
    Returns:
        Settings: Cached settings instance
    """
    return Settings()
