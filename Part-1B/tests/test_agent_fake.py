"""Plumbing tests — no network, uses FakeProvider (and a mocked Groq call)."""
from src.agent import parse
from src.provider import FakeProvider

_VALID = ('{"intent":"log_entry","habit_name":"x","quantity":null,"unit":null,'
          '"date":"2026-01-01","needs_clarification":false,"clarification_question":null}')

def test_empty_input_safe_envelope():
    out = parse("", provider=FakeProvider(""))
    assert out["intent"] in {"clarify", "unknown"}
    assert out["needs_clarification"] is True

def test_malformed_json_safe_envelope():
    out = parse("hi", provider=FakeProvider("not json"))
    assert out["needs_clarification"] is True
    assert out["clarification_question"]

def test_destructive_guardrail():
    out = parse("delete all habits", provider=FakeProvider(_VALID))
    assert out["intent"] == "clarify"

_PII_ECHO = ('{"intent":"clarify","habit_name":null,"quantity":null,"unit":null,'
             '"date":null,"needs_clarification":true,'
             '"clarification_question":"Noted: 123-45-6789. What should I log?"}')


def test_pii_guardrail():
    """GR-1/INV-5: PII echoed by the model into any field must be redacted."""
    out = parse("my ssn is 123-45-6789", provider=FakeProvider(_PII_ECHO))
    assert "123-45-6789" not in str(out)
    assert out["clarification_question"]  # INV-1 still holds after masking


def test_groq_provider_request_shape(monkeypatch):
    """GroqProvider builds the OpenAI-compatible call and parses the reply."""
    import src.provider as provider_module

    class _FakeResponse:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": '{"ok": true}'}}]}

    captured = {}

    def fake_post(url, json=None, headers=None, timeout=None):
        captured["url"] = url
        captured["body"] = json
        captured["headers"] = headers
        return _FakeResponse()

    monkeypatch.setattr(provider_module.requests, "post", fake_post)
    monkeypatch.setattr(provider_module, "get_groq_api_key", lambda: "test-key")
    out = provider_module.GroqProvider().generate("hi")
    assert out == '{"ok": true}'
    assert captured["url"] == "https://api.groq.com/openai/v1/chat/completions"
    assert captured["headers"]["Authorization"].startswith("Bearer ")
    assert captured["body"]["messages"][0]["content"] == "hi"
    assert captured["body"]["response_format"] == {"type": "json_object"}
