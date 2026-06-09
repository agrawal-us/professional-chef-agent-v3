from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str = "not-set"
    llm_provider: str = "ollama"
    ollama_host: str = "http://host.docker.internal:11434"
    llm_model: str = "llama3.1:8b-instruct-q4_0"
    redis_url: str = "redis://redis:6379"
    database_url: str = "postgresql+asyncpg://chef:chef_dev@postgres:5432/chef_agent"
    environment: str = "development"
    api_version: str = "1.0.0"
    openai_budget_usd: float = 500.0
    cache_ttl_seconds: int = 259200
    similarity_threshold: float = 0.80
    max_images_per_request: int = 3
    max_image_size_mb: int = 10

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
