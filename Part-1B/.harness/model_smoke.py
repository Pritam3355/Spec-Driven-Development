# import os, requests
# from dotenv import load_dotenv
# load_dotenv()
# # from src.config import get_gemini_api_key
# # key = get_gemini_api_key()
# key = os.getenv("GEMINI_API_KEY")
# model = os.environ.get('GEMINI_MODEL')

# url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}'
# r = requests.post(url, 
#                   json={'contents': [{
#                       'parts': [{'text': 'reply with the word ok'}]}]}, 
#                         timeout=30)

# print('status:', r.status_code)
# print('body:', r.text[:500])
#!/usr/bin/env python3
"""Manual diagnostic: one live parse() call against the configured model.

NOT a pytest test — it makes a real API call and prints the result.
Run from Part-1B/ either way:
    python -m .harness.model_smoke           # module invocation (uses CWD)
    python .harness/model_smoke.py           # direct (bootstrap below handles path)

Expected: intent=log_entry with extracted fields, NOT the safe envelope.
"""
import json
import pathlib
import sys

# Bootstrap: put Part-1B/ on sys.path so `from src.agent import parse` resolves
# regardless of the caller's working directory.
_ROOT = pathlib.Path(__file__).resolve().parents[1]  # Part-1B/
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.agent import parse   # noqa: E402 - import after sys.path setup

if __name__ == "__main__":
    out = parse("I meditated for 15 minutes this morning")
    print(json.dumps(out, indent=2))

    if out.get("intent") == "clarify" and "couldn't process" in str(out.get("clarification_question", "")):
        print("\n[warn] safe envelope returned — model call likely failed. Check key/model.")