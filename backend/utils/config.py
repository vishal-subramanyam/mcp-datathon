"""
Production configuration management.
Handles environment-specific settings and validation.
"""
import os
from typing import Optional
from pydantic import BaseModel, Field, validator
import logging

logger = logging.getLogger(__name__)


class Settings(BaseModel):
    """Application settings with validation."""
    
    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False)
    
    # Server
    port: int = Field(default=8000, env="PORT")
    host: str = Field(default="0.0.0.0")
    base_url: str = Field(default="http://localhost:8000", env="BASE_URL")
    
    # CORS
    frontend_url: str = Field(default="http://localhost:8501", env="FRONTEND_URL")
    streamlit_url: Optional[str] = Field(default=None, env="STREAMLIT_URL")
    vercel_url: Optional[str] = Field(default=None, env="VERCEL_URL")
    
    # API Keys
    openrouter_api_key: Optional[str] = Field(default=None, env="OPENROUTER_API_KEY")
    openrouter_model: str = Field(default="anthropic/claude-3.5-sonnet", env="OPENROUTER_MODEL")
    
    # Supabase
    supabase_url: Optional[str] = Field(default=None, env="SUPABASE_URL")
    supabase_key: Optional[str] = Field(default=None, env="SUPABASE_KEY")
    
    # Canvas (default/fallback)
    canvas_api_url: Optional[str] = Field(default=None, env="CANVAS_API_URL")
    canvas_api_key: Optional[str] = Field(default=None, env="CANVAS_API_KEY")
    
    # Google API
    calendar_credentials_path: str = Field(default="credentials.json", env="CALENDAR_CREDENTIALS_PATH")
    calendar_token_path: str = Field(default="calendar_token.json", env="CALENDAR_TOKEN_PATH")
    gmail_credentials_path: str = Field(default="credentials.json", env="GMAIL_CREDENTIALS_PATH")
    gmail_token_path: str = Field(default="token.json", env="GMAIL_TOKEN_PATH")
    
    # Flashcard storage
    flashcard_storage_path: str = Field(default="flashcard_data", env="FLASHCARD_STORAGE_PATH")
    
    # Request settings
    request_timeout: int = Field(default=90)
    max_request_size: int = Field(default=10485760)  # 10MB
    
    # Rate limiting
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_per_minute: int = Field(default=60)
    
    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")
    
    @validator("environment")
    def validate_environment(cls, v):
        """Validate environment setting."""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v
    
    @validator("port")
    def validate_port(cls, v):
        """Validate port number."""
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"
    
    @property
    def allowed_origins(self) -> list:
        """Get list of allowed CORS origins."""
        origins = [self.frontend_url]
        
        if self.streamlit_url:
            origins.append(self.streamlit_url)
        if self.vercel_url:
            origins.append(self.vercel_url)
        
        # In development, allow localhost variants
        if self.is_development:
            origins.extend([
                "http://localhost:8501",
                "http://127.0.0.1:8501",
                "http://localhost:3000",
                "http://127.0.0.1:3000",
            ])
        
        return list(set(origins))  # Remove duplicates
    
    def validate_required_for_production(self):
        """Validate that required settings are present for production."""
        if not self.is_production:
            return
        
        required_fields = {
            "openrouter_api_key": self.openrouter_api_key,
            "supabase_url": self.supabase_url,
            "supabase_key": self.supabase_key,
        }
        
        missing = [k for k, v in required_fields.items() if not v]
        
        if missing:
            raise ValueError(
                f"Missing required environment variables for production: {', '.join(missing)}"
            )
        
        logger.info("Production environment validation passed")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings (singleton pattern)."""
    global _settings
    
    if _settings is None:
        try:
            _settings = Settings()
            _settings.validate_required_for_production()
            logger.info(f"Settings loaded for environment: {_settings.environment}")
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            raise
    
    return _settings


def reload_settings():
    """Reload settings (useful for testing)."""
    global _settings
    _settings = None
    return get_settings()

