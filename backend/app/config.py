from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://skills_hub:changeme@localhost:5432/skills_hub"
    JWT_SECRET: str = "change-this-to-a-random-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440
    STORAGE_PATH: str = "/data/skills"
    ALLOW_REGISTRATION: bool = True
    DEFAULT_ADMIN_USERNAME: str = "admin"
    DEFAULT_ADMIN_PASSWORD: str = "admin123"
    DEFAULT_ADMIN_EMAIL: str = "admin@example.com"

    model_config = {"env_file": ".env"}


settings = Settings()
