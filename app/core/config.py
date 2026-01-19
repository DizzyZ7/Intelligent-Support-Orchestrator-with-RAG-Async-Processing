from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # API Keys
    OPENAI_API_KEY: str
    ZENDESK_API_TOKEN: str
    ZENDESK_SUBDOMAIN: str
    ZENDESK_EMAIL: str

    # Infrastructure
    REDIS_URL: str = "redis://redis:6379/0"
    QDRANT_HOST: str = "qdrant"
    QDRANT_PORT: int = 6333
    
    # App Settings
    PROJECT_NAME: str = "Intelligent Support Orchestrator"
    DEBUG: bool = True

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
