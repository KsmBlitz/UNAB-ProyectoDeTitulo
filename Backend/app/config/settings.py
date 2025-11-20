"""
Configuration module
Centralized settings and environment variables management
"""

from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    All sensitive data should be in .env file
    """
    
    # Database Configuration
    MONGO_CONNECTION_STRING: str
    DATABASE_NAME: str
    
    # Security & JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # SMTP Email Configuration
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    FROM_EMAIL: Optional[str] = None
    
    # Alert System Configuration
    ALERT_CHECK_INTERVAL_MINUTES: int = 30
    
    # SMS Notifications (AWS SNS)
    SMS_ENABLED: bool = False
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_SNS_REGION: Optional[str] = None
    
    # Twilio WhatsApp Notifications
    TWILIO_WHATSAPP_ENABLED: bool = False
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_WHATSAPP_FROM: Optional[str] = None
    
    # Twilio WhatsApp Notifications
    TWILIO_WHATSAPP_ENABLED: bool = False
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_WHATSAPP_FROM: Optional[str] = None
    
    # AWS IoT Core Configuration
    AWS_IOT_ENDPOINT: Optional[str] = None
    AWS_REGION: Optional[str] = None
    AWS_IOT_ROOT_CA_PATH: Optional[str] = None
    AWS_IOT_CERTIFICATE_PATH: Optional[str] = None
    AWS_IOT_PRIVATE_KEY_PATH: Optional[str] = None
    AWS_IOT_TOPIC: Optional[str] = None
    AWS_IOT_CLIENT_ID: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """
    Create settings instance (cached)
    Returns the same instance on subsequent calls
    """
    return Settings()  # type: ignore


# Export settings instance
settings = get_settings()
