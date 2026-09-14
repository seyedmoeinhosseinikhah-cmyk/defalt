from dataclasses import dataclass
from typing import Protocol

@dataclass
class AIResponse:
    text: str
    provider: str

class AIProvider(Protocol):
    def ask(self, prompt: str, context: str = '') -> AIResponse: ...

class MockProvider:
    """Safe local provider used when no external AI key is configured."""
    def ask(self, prompt: str, context: str = '') -> AIResponse:
        return AIResponse(
            text='AI provider is not configured yet. Add an API-backed provider in app/ai/provider.py.\n\nPrompt received: ' + prompt[:500],
            provider='local-mock',
        )
