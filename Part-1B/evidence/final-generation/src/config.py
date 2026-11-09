"""Environment configuration helpers for the habit logger."""

import os
from collections.abc import MutableMapping
from pathlib import Path


def load_dotenv(
    path: Path,
    env: MutableMapping[str, str] | None = None,
) -> int:
    """Load non-empty key-value pairs without overriding existing variables."""
    target = os.environ if env is None else env
    loaded = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", maxsplit=1)
        key = key.strip()
        value = value.strip()
        if (
            not key
            or not value
            or key in target
        ):
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        if value:
            target[key] = value
            loaded += 1
    return loaded


def _find_dotenv(start: Path | None = None) -> Path | None:
    """Find the nearest .env file starting from the source directory."""
    directory = Path(__file__).resolve().parent if start is None else start
    for candidate_directory in (directory, *directory.parents):
        candidate = candidate_directory / ".env"
        if candidate.is_file():
            return candidate
    return None


def get_groq_api_key(
    env: MutableMapping[str, str] | None = None,
) -> str:
    """Get the Groq key from the environment or the nearest .env file."""
    target = os.environ if env is None else env
    api_key = target.get("GROQ_API_KEY", "").strip()
    if api_key:
        return api_key

    dotenv_path = _find_dotenv()
    if dotenv_path is not None:
        load_dotenv(dotenv_path, target)
        api_key = target.get("GROQ_API_KEY", "").strip()
        if api_key:
            return api_key

    raise RuntimeError("GROQ_API_KEY is not set in the environment or .env file.")
