"""LLM provider interfaces and implementations for the habit logger."""

import os
import time

import requests

from src.config import get_groq_api_key


class LLMProvider:
    """Define the interface implemented by language model providers."""

    def generate(self, prompt: str) -> str:
        """Generate a text response for the given prompt."""
        raise NotImplementedError


class FakeProvider(LLMProvider):
    """Return a preset response without making network requests."""

    def __init__(self, preset: str = "") -> None:
        """Initialize the provider with a fixed response."""
        self.preset = preset

    def generate(self, prompt: str) -> str:
        """Return the preset response verbatim."""
        return self.preset


class GroqProvider(LLMProvider):
    """Generate JSON responses using Groq's OpenAI-compatible REST API."""

    def __init__(self) -> None:
        """Configure the Groq model from the environment."""
        self.model = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")
        self.endpoint = "https://api.groq.com/openai/v1/chat/completions"

    def generate(self, prompt: str) -> str:
        """Generate a response using Groq's JSON output mode."""
        api_key = get_groq_api_key()
        body = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 1024,
            "response_format": {"type": "json_object"},
        }
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.post(
            self.endpoint,
            json=body,
            headers=headers,
            timeout=30,
        )
        if response.status_code == 429:
            time.sleep(3)
            response = requests.post(
                self.endpoint,
                json=body,
                headers=headers,
                timeout=30,
            )
        response.raise_for_status()
        response_data = response.json()
        return response_data["choices"][0]["message"]["content"]
