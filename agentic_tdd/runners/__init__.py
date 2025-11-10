"""Language runners package."""

from .base import LanguageRunner
from .rust import RustRunner

__all__ = ["LanguageRunner", "RustRunner", "get_runner"]


_RUNNERS: dict[str, type[LanguageRunner]] = {
    "rust": RustRunner,
}


def get_runner(language: str) -> LanguageRunner:
    """Get language runner instance by name.

    Args:
        language: Language identifier (e.g., 'rust', 'python')

    Returns:
        LanguageRunner instance

    Raises:
        ValueError: If language not supported
    """
    runner_class = _RUNNERS.get(language.lower())
    if runner_class is None:
        supported = ", ".join(_RUNNERS.keys())
        raise ValueError(f"Unsupported language: {language}. Supported: {supported}")

    return runner_class()
