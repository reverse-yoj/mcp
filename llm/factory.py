import json
import os
from pathlib import Path

from .base import LLMClient
from .openai_client import OpenAIClient

CONFIG_PATH = Path(__file__).with_name('llm_config.json')

def _load_config() -> dict:
    """Load LLM configuration from JSON file.

    Returns:
        dict: Configuration dictionary.
    """
    if not CONFIG_PATH.is_file():
        raise FileNotFoundError(f"LLM configuration file not found at {CONFIG_PATH}")
    with CONFIG_PATH.open('r', encoding='utf-8') as f:
        return json.load(f)

def get_llm_client() -> LLMClient:
    """Factory function returning a configured LLM client.

    The function reads ``llm_config.json`` to determine which provider to use.
    Currently supports ``openai`` provider. Additional providers can be added
    by extending the ``if`` block and implementing a concrete ``LLMClient``
    subclass.

    Returns:
        LLMClient: An instance of a concrete LLM client.
    """
    cfg = _load_config()
    provider = cfg.get('provider', 'openai').lower()
    if provider == 'openai':
        api_key = os.getenv(cfg.get('api_key_env', 'OPENAI_API_KEY'))
        if not api_key:
            # No API key; indicate that LLM client is unavailable.
            return None
        return OpenAIClient(api_key=api_key)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
