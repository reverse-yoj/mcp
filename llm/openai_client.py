import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

from openai import OpenAI
from .base import LLMClient

class OpenAIClient(LLMClient):
    """Concrete LLMClient using OpenAI's Python SDK."""

    def __init__(self, api_key: Optional[str] = None):
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set for OpenAIClient")
        self.client = OpenAI(api_key=api_key)

    def chat_completion(self, *, model: str, messages: List[Dict[str, str]], temperature: float = 0.5, response_format: Optional[Dict[str, Any]] = None):
        """Perform a chat completion request.

        Args:
            model: Model identifier (e.g., "gpt-4o-mini").
            messages: List of message dictionaries as required by OpenAI.
            temperature: Sampling temperature.
            response_format: Optional dict specifying response format, e.g., {"type": "json_object"}.
        Returns:
            OpenAI ChatCompletion response object.
        """
        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if response_format:
            kwargs["response_format"] = response_format
        return self.client.chat.completions.create(**kwargs)
