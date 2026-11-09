import os, requests
from dotenv import load_dotenv
load_dotenv()
# from src.config import get_gemini_api_key
# key = get_gemini_api_key()
key = os.getenv("GEMINI_API_KEY")
model = os.environ.get('GEMINI_MODEL')

url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}'
r = requests.post(url, 
                  json={'contents': [{
                      'parts': [{'text': 'reply with the word ok'}]}]}, 
                        timeout=30)

print('status:', r.status_code)
print('body:', r.text[:500])