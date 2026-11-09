"""Offline tests for the .env loader — no network, no real key needed."""
import pytest

from src import config


def test_load_dotenv_parses_and_ignores(tmp_path):
    p = tmp_path / ".env"
    p.write_text('# comment\nGROQ_API_KEY="abc 123"\n'
                 'GROQ_MODEL=openai/gpt-oss-20b\nBROKEN LINE\n\nEMPTY=\n',
                 encoding="utf-8")
    env = {}
    assert config.load_dotenv(p, env) == 2
    assert env["GROQ_API_KEY"] == "abc 123"
    assert env["GROQ_MODEL"] == "openai/gpt-oss-20b"
    assert "BROKEN" not in env and "EMPTY" not in env


def test_load_dotenv_never_overrides_existing(tmp_path):
    p = tmp_path / ".env"
    p.write_text("GROQ_API_KEY=from-file\n", encoding="utf-8")
    env = {"GROQ_API_KEY": "from-export"}
    config.load_dotenv(p, env)
    assert env["GROQ_API_KEY"] == "from-export"   # exported var wins


def test_get_groq_api_key_env_wins():
    assert config.get_groq_api_key({"GROQ_API_KEY": "  from-env  "}) == "from-env"


def test_get_groq_api_key_missing_raises(monkeypatch):
    monkeypatch.setattr(config, "_find_dotenv", lambda *a, **k: None)
    with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
        config.get_groq_api_key({})


def test_get_groq_api_key_from_dotenv(tmp_path, monkeypatch):
    p = tmp_path / ".env"
    p.write_text("GROQ_API_KEY=from-file\n", encoding="utf-8")
    monkeypatch.setattr(config, "_find_dotenv", lambda *a, **k: p)
    env = {}
    assert config.get_groq_api_key(env) == "from-file"
    assert env["GROQ_API_KEY"] == "from-file"     # loaded, not overwritten
