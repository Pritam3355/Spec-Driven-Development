"""LLM provider interfaces and implementations for the habit logger."""

import os
import time

import requests


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


class GeminiProvider(LLMProvider):
    """Generate JSON responses using the Gemini REST API."""

    def __init__(self) -> None:
        """Configure the Gemini model from the environment."""
        self.model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")

    def generate(self, prompt: str) -> str:
        """Generate a response using Gemini's JSON output mode."""
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY environment variable is required for Gemini."
            )

        endpoint = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent"
        )
        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 512,
                "responseMimeType": "application/json",
            },
        }
        headers = {"x-goog-api-key": api_key}
        response = requests.post(
            endpoint,
            json=body,
            headers=headers,
            timeout=30,
        )
        if response.status_code == 429:
            time.sleep(3)
            response = requests.post(
                endpoint,
                json=body,
                headers=headers,
                timeout=30,
            )
        response.raise_for_status()
        response_data = response.json()
        return response_data["candidates"][0]["content"]["parts"][0]["text"]
