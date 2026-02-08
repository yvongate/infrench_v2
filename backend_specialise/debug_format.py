
import os
import requests
import base64
from dotenv import load_dotenv

load_dotenv()
GOOGLE_AI_API_KEY = os.getenv("GOOGLE_AI_API_KEY")

def inspect_audio_format():
    model_name = "gemini-2.5-flash-preview-tts"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GOOGLE_AI_API_KEY}"
    
    print(f"Generating audio from {model_name}...")
    
    payload = {
        "contents": [{
            "parts": [{"text": "Test format audio."}]
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
    
    try:
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        if response.status_code == 200:
            data = response.json()
            if "candidates" in data and len(data["candidates"]) > 0:
                parts = data["candidates"][0]["content"]["parts"]
                for part in parts:
                    if "inlineData" in part:
                        audio_data = base64.b64decode(part['inlineData']['data'])
                        header = audio_data[:16]
                        print(f"Header HEX: {header.hex()}")
                        print(f"Header ASCII: {header}")
                        
                        filename = "debug_audio.bin"
                        with open(filename, "wb") as f:
                            f.write(audio_data)
                        print(f"Saved {len(audio_data)} bytes to {filename}")
                        return
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_audio_format()
