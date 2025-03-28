from .openai import OpenAIAdapter
from .anthropic import AnthropicAdapter

ADAPTER_MAP = {
    "openai": OpenAIAdapter,
    "anthropic": AnthropicAdapter
}

def get_adapter(provider: str, config: dict):
    adapter_class = ADAPTER_MAP.get(provider)
    if not adapter_class:
        raise ValueError(f"No adapter found for provider {provider}")
    return adapter_class(config)