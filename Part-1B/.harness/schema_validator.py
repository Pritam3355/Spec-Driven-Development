"""Layer 1 — structural validation."""
import json, pathlib
from jsonschema import Draft7Validator

SCHEMA = json.loads((pathlib.Path(__file__).resolve().parents[1]
                     / "evals" / "schema.json").read_text())

def validate_schema(output: dict) -> list[str]:
    v = Draft7Validator(SCHEMA)
    return [f"{'/'.join(map(str, e.path)) or '<root>'}: {e.message}"
            for e in v.iter_errors(output)]
