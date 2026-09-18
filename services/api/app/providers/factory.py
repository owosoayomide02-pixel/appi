from app.config import settings
from app.providers.base import ModelProvider
from app.providers.heuristic import HeuristicProvider
from app.providers.openai_compatible import AnthropicProvider, OpenAICompatibleProvider, last_error


def get_provider() -> ModelProvider:
    name = settings.resolved_ai_provider
    key = settings.resolved_ai_key
    if name in {"openai", "openai_compatible"} and key:
        base = settings.ai_base_url or "https://api.openai.com/v1"
        return OpenAICompatibleProvider(key, base_url=base, model=settings.ai_model)
    if name == "anthropic" and key:
        return AnthropicProvider(key, model=settings.ai_model)
    return HeuristicProvider()


def provider_status() -> dict[str, str | bool | None]:
    provider = get_provider()
    model = settings.ai_model or None
    if provider.name == "openai" and not model:
        model = "gpt-4o-mini"
    if provider.name == "anthropic" and not model:
        model = "claude-sonnet-4-20250514"
    return {
        "ai_provider": provider.name,
        "ai_configured": bool(settings.resolved_ai_key) and provider.name != "heuristic",
        "ai_model": model if provider.name != "heuristic" else None,
        "ai_last_error": last_error,
    }
