"""Ensure the project root is on sys.path so `from src.x import y` works
regardless of where pytest is invoked from."""
import sys
from pathlib import Path

_ROOT = Path(__file__).parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))