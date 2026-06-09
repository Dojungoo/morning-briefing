from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Provided by the coders.kr platform via coders.yaml substitution.
    database_url: str = "postgresql+asyncpg://app:app@localhost:5432/app"

    # Local-dev escape hatch: when set, an X-Coders-User-less request is
    # treated as if it came from this UUID. Lets you `curl` the API
    # without the platform gate in front. Never set in production.
    dev_fake_user: str | None = None

    # Managed LLM (coders.kr `type: llm` component). The platform injects
    # a per-tenant proxy URL + token via coders.yaml; the Anthropic key is
    # the platform's, billed per visitor. See PLATFORM.md §8. When unset
    # (local dev without the platform), the summariser falls back to a
    # deterministic local composer so the app still produces a briefing.
    anthropic_base_url: str | None = None
    anthropic_api_key: str | None = None
    llm_model: str = "claude-sonnet-4-6"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def llm_enabled(self) -> bool:
        return bool(self.anthropic_base_url and self.anthropic_api_key)


settings = Settings()
