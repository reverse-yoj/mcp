from abc import ABC, abstractmethod

class LLMClient(ABC):
    @abstractmethod
    def chat_completion(self, *, model: str, messages: list, temperature: float = 0.5, response_format: dict | None = None):
        """Perform a chat completion request.
        Args:
            model: Identifier of the model to use.
            messages: List of message dictionaries as per OpenAI API.
            temperature: Sampling temperature.
            response_format: Optional format spec (e.g., {"type": "json_object"}).
        Returns:
            The raw response object from the underlying provider.
        """
        pass
