
import os
import requests
import base64
from dotenv import load_dotenv

load_dotenv()
GOOGLE_AI_API_KEY = os.getenv("GOOGLE_AI_API_KEY")

def test_mp3_generation():
    model_name = "gemini-2.5-flash-preview-tts"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GOOGLE_AI_API_KEY}"
    
    print(f"Testing MP3 generation with {model_name}...")
    
    # Tentative 1: audioEncoding dans video/voice config? 
    # La doc n'est pas explicite sur audioEncoding dans generationConfig pour generateContent multimodal,
    # mais c'est standard dans Text-to-Speech API. Pour Gemini, c'est peut-être différent.
    # Essayons de demander explicitement MP3 si possible, sinon on convertira.
    
    # Tentative avec paramètre explicite
    payload = {
        "contents": [{
            "parts": [{"text": "Ceci est un test pour vérifier si je peux générer un fichier MP3 directement."}]
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
                        header = audio_data[:4]
                        print(f"Header reçu: {header}")
                        
                        # Sauvegarder pour analyse
                        filename = "test_audio_output.bin"
                        with open(filename, "wb") as f:
                            f.write(audio_data)
                        print(f"Fichier sauvegardé: {filename}")
                        
                        # Analyse avec ffprobe
                        import subprocess
                        try:
                            result = subprocess.run(["ffprobe", filename], capture_output=True, text=True)
                            print("\n--- ffprobe ---")
                            print(result.stderr) # ffprobe écrit souvent sur stderr
                        except Exception as e:
                            print(f"ffprobe error: {e}")
                            
                        return True
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")
    return False

if __name__ == "__main__":
    test_mp3_generation()
