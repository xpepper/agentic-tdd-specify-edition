"""Configuration models for the agentic-tdd CLI tool."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, ValidationInfo, field_validator


class LLMProviderConfig(BaseModel):
    """Configuration for an OpenAI-compatible LLM provider."""

    provider: Literal["openai", "perplexity", "deepseek", "iflow", "custom"] = Field(
        description="Provider identifier"
    )

    model: str = Field(description="Model name (e.g., 'gpt-4', 'llama-2-70b-chat')")

    api_key: str = Field(description="API key for authentication")

    base_url: str | None = Field(
        default=None, description="Custom base URL (overrides provider default)"
    )

    temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="LLM temperature for code generation (low for determinism)",
    )

    timeout: int = Field(default=30, gt=0, description="Request timeout in seconds")

    @field_validator("base_url", mode="before")
    @classmethod
    def set_default_base_url(cls, v: str | None, info: ValidationInfo) -> str:
        """Set default base URL based on provider if not specified."""
        if v is not None:
            return v

        provider_urls = {
            "openai": "https://api.openai.com/v1",
            "perplexity": "https://api.perplexity.ai",
            "deepseek": "https://api.deepseek.com/v1",
            "iflow": "https://apis.iflow.cn/v1",
        }

        # Get provider from field values
        provider = info.data.get("provider")
        if not isinstance(provider, str):
            raise ValueError("Provider must be specified")

        if provider == "custom":
            raise ValueError("Custom provider requires explicit base_url")

        url = provider_urls.get(provider)
        if url is None:
            raise ValueError(f"Unknown provider: {provider}")

        return url


class ToolConfig(BaseModel):
    """Configuration for the agentic-tdd CLI tool."""

    kata_path: Path = Field(description="Path to kata description markdown file")

    work_dir: Path = Field(description="Working directory for kata implementation")

    language: str = Field(
        default="rust",
        description="Target language for implementation (e.g., 'rust', 'python')",
    )

    llm_config: LLMProviderConfig = Field(description="LLM provider configuration")

    max_cycles: int = Field(
        default=15, gt=0, description="Maximum number of TDD cycles before stopping"
    )

    max_retries: int = Field(
        default=3, gt=0, description="Maximum retry attempts per agent before escalation"
    )

    verbose: bool = Field(default=False, description="Enable verbose logging")

    command_timeout: int = Field(
        default=30, gt=0, description="Timeout for shell commands in seconds"
    )

    @field_validator("work_dir")
    @classmethod
    def validate_work_dir(cls, v: Path) -> Path:
        """Ensure work directory is absolute and writable."""
        if not v.is_absolute():
            v = v.absolute()
        v.mkdir(parents=True, exist_ok=True)
        return v
