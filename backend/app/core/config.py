from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost/aicareercoach"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # LLM
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"

    # Upstash QStash
    qstash_url: str = ""
    qstash_token: str = ""
    qstash_current_signing_key: str = ""
    qstash_next_signing_key: str = ""

    # Cloudinary
    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""

    # Auth — shared secret with NextAuth frontend
    nextauth_secret: str = "changeme"

    # Backend
    backend_cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001"

    # Environment
    environment: str = "development"

    @property
    def cors_origins_list(self) -> list[str]:
        if not self.backend_cors_origins:
            return ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"]
        return [o.strip() for o in self.backend_cors_origins.split(",") if o.strip()]

settings = Settings()
