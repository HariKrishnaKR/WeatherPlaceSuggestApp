import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

key = os.getenv('GEMINI_API_KEY')
if not key:
    print('GEMINI_API_KEY not set. Please add it to .env or environment variables.')
    raise SystemExit(1)

genai.configure(api_key=key)

print('Listing available models from Gemini API...')
try:
    models = genai.list_models()
    # models can be list of objects/dicts; print readable info
    for m in models:
        try:
            if isinstance(m, dict):
                print(f"- {m.get('name') or m.get('model')}  (details: {m})")
            else:
                # object - print attributes we can
                name = getattr(m, 'name', None) or getattr(m, 'model', None)
                print(f"- {name}  (obj: {m})")
        except Exception:
            print('-', m)
except Exception as e:
    print('Error listing models:', e)
    raise
