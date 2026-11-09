"""Ensure Part-1B/ is on sys.path so `from src.x import y` works under pytest
regardless of the caller's working directory."""
import sys
from pathlib import Path

_ROOT = Path(__file__).parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))