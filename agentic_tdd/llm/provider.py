"""LLM provider factory for initializing language models."""

from langchain_openai import ChatOpenAI

from ..models.config import LLMProviderConfig


def create_llm(config: LLMProviderConfig) -> ChatOpenAI:
    """Create and configure an LLM instance.

    Args:
        config: LLM provider configuration

    Returns:
        Configured ChatOpenAI instance

    Raises:
        ValueError: If provider is not supported
    """
    supported_providers = ["openai", "perplexity", "deepseek", "iflow", "custom"]
    if config.provider not in supported_providers:
        raise ValueError(
            f"Unsupported provider: {config.provider}. "
            f"Supported providers: {', '.join(supported_providers)}"
        )

    # Create ChatOpenAI instance with appropriate configuration
    # base_url is already set by the validator in LLMProviderConfig
    return ChatOpenAI(
        model=config.model,
        temperature=config.temperature,
        api_key=config.api_key,
        base_url=config.base_url,
        timeout=config.timeout,
    )
