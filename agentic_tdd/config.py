"""Configuration loading and management."""

import os
from pathlib import Path
from typing import Literal

from .models.config import LLMProviderConfig, ToolConfig


def load_config_from_cli(
    kata_path: Path,
    work_dir: Path,
    language: str,
    provider: Literal["openai", "perplexity", "deepseek", "iflow", "custom"],
    model: str,
    api_key: str | None,
    base_url: str | None,
    temperature: float,
    max_cycles: int,
    max_retries: int,
    verbose: bool,
    command_timeout: int,
) -> ToolConfig:
    """Load configuration from CLI arguments.

    Args:
        kata_path: Path to kata description markdown file
        work_dir: Working directory for kata implementation
        language: Target programming language
        provider: LLM provider name
        model: LLM model name
        api_key: API key (if not provided, will try environment variable)
        base_url: Custom base URL for LLM provider
        temperature: LLM temperature setting
        max_cycles: Maximum number of TDD cycles
        max_retries: Maximum retry attempts per agent
        verbose: Enable verbose logging
        command_timeout: Timeout for shell commands

    Returns:
        ToolConfig instance

    Raises:
        ValueError: If required configuration is missing
    """
    # Resolve API key from environment if not provided
    if api_key is None:
        api_key = _get_api_key_from_env(provider)
        if api_key is None:
            raise ValueError(
                f"API key not found. Set {_get_env_var_name(provider)} environment "
                f"variable or provide --api-key flag"
            )

    # Build LLM config
    llm_config = LLMProviderConfig(
        provider=provider,
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=temperature,
    )

    # Build tool config
    return ToolConfig(
        kata_path=kata_path,
        work_dir=work_dir,
        language=language,
        llm_config=llm_config,
        max_cycles=max_cycles,
        max_retries=max_retries,
        verbose=verbose,
        command_timeout=command_timeout,
    )


def _get_api_key_from_env(
    provider: Literal["openai", "perplexity", "deepseek", "iflow", "custom"],
) -> str | None:
    """Get API key from environment variable based on provider.

    Args:
        provider: LLM provider name

    Returns:
        API key from environment variable or None if not found
    """
    env_var_name = _get_env_var_name(provider)
    return os.environ.get(env_var_name)


def _get_env_var_name(
    provider: Literal["openai", "perplexity", "deepseek", "iflow", "custom"],
) -> str:
    """Get environment variable name for provider.

    Args:
        provider: LLM provider name

    Returns:
        Environment variable name
    """
    env_vars = {
        "openai": "OPENAI_API_KEY",
        "perplexity": "PERPLEXITY_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "iflow": "IFLOW_API_KEY",
        "custom": "CUSTOM_API_KEY",
    }
    return env_vars[provider]
