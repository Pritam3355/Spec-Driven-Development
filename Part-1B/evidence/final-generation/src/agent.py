"""Natural-language habit parsing pipeline."""

import json
import re

from src import guardrails
from src.prompts import SYSTEM_PROMPT, build_user_prompt
from src.provider import GroqProvider, LLMProvider

_CODE_FENCE_PATTERN = re.compile(
    r"\A```(?:json)?[ \t]*\r?\n?(.*?)\r?\n?```[ \t]*\Z",
    re.IGNORECASE | re.DOTALL,
)


def parse(text: str, provider: LLMProvider | None = None) -> dict[str, object]:
    """Parse free text into a safe structured habit intent."""
    try:
        selected_provider = provider if provider is not None else GroqProvider()
        user_prompt = build_user_prompt(text)
        prompt = f"{SYSTEM_PROMPT}\n\n{user_prompt}"
        raw = selected_provider.generate(prompt)
        if not raw or not raw.strip():
            return guardrails.safe_envelope(
                "I couldn't extract a habit entry. Could you clarify?"
            )

        model_output = raw.strip()
        fenced_output = _CODE_FENCE_PATTERN.fullmatch(model_output)
        if fenced_output is not None:
            model_output = fenced_output.group(1).strip()

        parsed_output = json.loads(model_output)
        if not isinstance(parsed_output, dict):
            return guardrails.safe_envelope(
                "I couldn't understand that response. Could you clarify?"
            )
        return guardrails.apply(parsed_output, raw, text)
    except Exception:  # noqa: BLE001 - GR-2 requires a safe fallback for any failure.
        return guardrails.safe_envelope(
            "I couldn't process that request. Could you clarify?"
        )
