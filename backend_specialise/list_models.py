
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_AI_API_KEY")
if not api_key:
    print("API Key not found")
    exit(1)

genai.configure(api_key=api_key)

print("Listing available models:")
try:
    count = 0
    for m in genai.list_models():
        if "audio" in m.name.lower() or "speech" in m.name.lower() or "flash" in m.name.lower():
            print(m.name, flush=True)
            count += 1
    print(f"Total models found: {count}")
except Exception as e:
    print(f"Error: {e}")
