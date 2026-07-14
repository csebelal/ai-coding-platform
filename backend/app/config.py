from pydantic_settings import BaseSettings
from typing import Optional
from datetime import timedelta

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/ai_platform"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    
    # JWT
    JWT_SECRET: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # AI Providers
    DEEPSEEK_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    
    # OAuth - GitHub
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None
    GITHUB_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/github/callback"
    
    # OAuth - Google
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"
    
    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"
    
    # App
    APP_NAME: str = "AI Coding Platform"
    DEBUG: bool = True
    
    # Cost Control
    DEFAULT_BUDGET_LIMIT: float = 0.10
    
    # Repository Storage
    REPOS_DIR: str = "/app/repos"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
