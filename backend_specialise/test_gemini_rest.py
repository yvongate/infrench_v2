
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_AI_API_KEY")
if not API_KEY:
    print("API Key not found")
    exit(1)

# URLs to test
base_url = "https://generativelanguage.googleapis.com/v1beta/models"

# 1. Test generateContent with audio response modality (Gemini 2.5 Flash)
def test_generate_content_audio():
    # Liste des modèles à tester
    models_to_test = [
        "gemini-2.5-flash-preview-tts", 
        "gemini-2.5-flash"
    ]
    
    for model_name in models_to_test:
        print(f"\n--- Testing Model: {model_name} ---")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={API_KEY}"
        
        headers = {"Content-Type": "application/json"}
        # Important: API REST utilise camelCase !
        payload = {
            "contents": [{
                "parts": [{"text": "Bonjour, ceci est un test de synthèse vocale Gemini."}]
            }],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {
                        "prebuiltVoiceConfig": {
                            "voiceName": "Charon"
                        }
                    }
                }
            }
        }
        
        print(f"POST {url}")
        try:
            response = requests.post(url, headers=headers, json=payload)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Success!")
                data = response.json()
                # Inspect response for audio data
                if "candidates" in data and len(data["candidates"]) > 0:
                    parts = data["candidates"][0]["content"]["parts"]
                    for part in parts:
                        if "inlineData" in part:
                            audio_len = len(part['inlineData']['data'])
                            print(f"🎵 Audio data received: {audio_len} chars")
                            
                            # Sauvegarder pour vérifier
                            import base64
                            audio_bytes = base64.b64decode(part['inlineData']['data'])
                            filename = f"test_{model_name}.wav"
                            with open(filename, "wb") as f:
                                f.write(audio_bytes)
                            print(f"Saved to {filename}")
                            return True
                print("No audio data found in response.")
            else:
                print(f"❌ Error: {response.text}")
        except Exception as e:
            print(f"Exception: {e}")
            
    return False

# 2. Test generate_speech endpoint (if it exists separate from generateContent)
# Usually it's mapped to models like 'tts-1' or similar, but for Gemini it's multimodal.

def list_models_rest():
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
    try:
        response = requests.get(url)
        print(f"Listing models: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if "models" in data:
                with open("models_clean.txt", "w", encoding="utf-8") as f:
                    for m in data["models"]:
                        if "flash" in m["name"] or "gemini" in m["name"]:
                            f.write(f"{m['name']} ({m.get('supportedGenerationMethods', [])})\n")
                print("Models written to models_clean.txt")
            else:
                print("No models found in response.")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    print("--- Test REST API Gemini TTS ---")
    list_models_rest()
    test_generate_content_audio()
