import httpx
import asyncio
import os
import base64
import json
import subprocess
from dotenv import load_dotenv

load_dotenv()

DEEPINFRA_API_KEY = os.getenv("DEEPINFRA_API_KEY")

async def test_model(model_id, payload):
    url = f"https://api.deepinfra.com/v1/inference/{model_id}"
    headers = {
        "Authorization": f"Bearer {DEEPINFRA_API_KEY}",
        "Content-Type": "application/json"
    }
    
    print(f"\nTesting model: {model_id}...")
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(url, headers=headers, json=payload)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if "audio" in data:
                    b64_string = str(data["audio"])
                    print(f"B64 String start: {b64_string[:100]}")
                    
                    # Remove potential data URI prefix
                    if "," in b64_string:
                        b64_string = b64_string.split(",")[-1]
                        print("Stripped prefix from B64 string.")
                    
                    padding = len(b64_string) % 4
                    if padding:
                        b64_string += "=" * (4 - padding)
                    
                    audio_bytes = base64.b64decode(b64_string)
                    print(f"Audio received: {len(audio_bytes)} bytes")
                    
                    temp_input = f"temp_in_{model_id.split('/')[-1]}.raw"
                    output_mp3 = f"test_{model_id.split('/')[-1]}.mp3"
                    
                    with open(temp_input, "wb") as f:
                        f.write(audio_bytes)
                    
                    print(f"Converting to {output_mp3}...")
                    # Higgs est du PCM brut 24kHz, Chatterbox est du WAV
                    if "Higgs" in model_id:
                        cmd = ["ffmpeg", "-y", "-f", "s16le", "-ar", "24000", "-ac", "1", "-i", temp_input, output_mp3]
                    else:
                        cmd = ["ffmpeg", "-y", "-i", temp_input, "-acodec", "libmp3lame", output_mp3]
                    
                    try:
                        res = subprocess.run(cmd, capture_output=True, text=True)
                        if res.returncode == 0:
                            print(f"Success! Final audio: {output_mp3}")
                            if os.path.exists(temp_input): os.remove(temp_input)
                        else:
                            print(f"FFmpeg Error: {res.stderr}")
                            print(f"Kept raw file as {temp_input}")
                    except Exception as fe:
                        print(f"Subprocess Exception: {str(fe)}")
                    
                    return True
                else:
                    print(f"No 'audio' field in response keys: {list(data.keys())}")
            else:
                print(f"Error: {response.text[:500]}")
        except Exception as e:
            print(f"Exception: {str(e)}")
    return False

async def main():
    if not DEEPINFRA_API_KEY:
        print("Error: DEEPINFRA_API_KEY not found in .env")
        return

    test_text_fr = """Maître Corbeau, sur un arbre perché,
Tenait en son bec un fromage.
Maître Renard, par l'odeur alléché,
Lui tint à peu près ce langage :
Et bonjour, Monsieur du Corbeau.
Que vous êtes joli ! que vous me semblez beau !
Sans mentir, si votre ramage
Se rapporte à votre plumage,
Vous êtes le Phénix des hôtes de ces bois.
À ces mots, le Corbeau ne se sent pas de joie ;
Et pour montrer sa belle voix,
Il ouvre un large bec, laisse tomber sa proie.
Le Renard s'en saisit, et dit : Mon bon Monsieur,
Apprenez que tout flatteur
Vit aux dépens de celui qui l'écoute.
Cette leçon vaut bien un fromage, sans doute.
Le Corbeau honteux et confus
Jura, mais un peu tard, qu'on ne l'y prendrait plus."""
    ref_audio_path = "reference_voice.wav"

    # 1. Test Higgs Audio (Clonage + Accent FR)
    higgs_payload = {
        "input": test_text_fr,
        "language": "fr",
    }
    if os.path.exists(ref_audio_path):
        with open(ref_audio_path, "rb") as f:
            b64_ref = base64.b64encode(f.read()).decode("utf-8")
            higgs_payload["reference_audio"] = b64_ref
            print("Attached reference voice for Higgs cloning.")

    await test_model("bosonai/HiggsAudioV2.5", higgs_payload)

    # 2. Test Zonos (Clonage + Paramètres optimisés)
    zonos_payload = {
        "text": test_text_fr,
        "language": "fr-fr",
        "speaking_rate": 1.0,
        "pitch_variation": 0.1,
        "vqscore": [0.78] * 8,
        "max_freq": 22050
    }
    
    if os.path.exists(ref_audio_path):
        with open(ref_audio_path, "rb") as f:
            b64_ref = base64.b64encode(f.read()).decode("utf-8")
            zonos_payload["audio_reference"] = b64_ref 
            print("Attached reference voice for Zonos cloning.")
            
    await test_model("Zyphra/Zonos-v0.1-transformer", zonos_payload)

async def test_gemini_tts():
    """Test Gemini TTS avec voix française de qualité (via REST API)"""
    import requests
    import base64
    
    GOOGLE_AI_API_KEY = os.getenv("GOOGLE_AI_API_KEY")
    if not GOOGLE_AI_API_KEY:
        print("Error: GOOGLE_AI_API_KEY not found in .env")
        return False
    
    # Modèle validé
    model_name = "gemini-2.5-flash-preview-tts"
    
    print("\n" + "="*60)
    print(f"Testing Gemini TTS ({model_name})")
    print("="*60)
    
    test_text_fr = """Maître Corbeau, sur un arbre perché,
Tenait en son bec un fromage.
Maître Renard, par l'odeur alléché,
Lui tint à peu près ce langage :
Et bonjour, Monsieur du Corbeau."""
    
    print(f"Texte à synthétiser: {test_text_fr[:100]}...")
    print("Génération de l'audio via REST API...")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GOOGLE_AI_API_KEY}"
    
    payload = {
        "contents": [{
            "parts": [{"text": test_text_fr}]
        }],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {
                        "voiceName": "Charon" # Voix masculine
                    }
                }
            }
        }
    }
    
    try:
        # Note: requests est synchrone, mais pour le test c'est ok. Dans services/tts.py on utilise httpx.
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        
        if response.status_code == 200:
            data = response.json()
            if "candidates" in data and len(data["candidates"]) > 0:
                parts = data["candidates"][0]["content"]["parts"]
                for part in parts:
                    if "inlineData" in part:
                        audio_data = base64.b64decode(part['inlineData']['data'])
                        print(f"Audio reçu: {len(audio_data)} bytes")
                        
                        # Sauvegarder en RAW (PCM)
                        raw_file = "test_gemini_tts.raw"
                        mp3_file = "test_gemini_tts.mp3"
                        
                        # Nettoyer avant
                        if os.path.exists(raw_file): os.remove(raw_file)
                        if os.path.exists(mp3_file): os.remove(mp3_file)
                        
                        with open(raw_file, "wb") as f:
                            f.write(audio_data)
                        
                        print(f"Audio RAW sauvegardé: {os.path.abspath(raw_file)}")
                        
                        # Conversion MP3
                        import subprocess
                        import time
                        
                        # Attendre que le système de fichiers libère le verrou
                        time.sleep(1.0)
                        
                        try:
                            print(f"Conversion en MP3 vers {os.path.abspath(mp3_file)}...")
                            
                            # Conversion PCM s16le 24kHz -> MP3
                            cmd = [
                                "ffmpeg", "-y", 
                                "-f", "s16le", "-ar", "24000", "-ac", "1", "-i", os.path.abspath(raw_file),
                                "-codec:a", "libmp3lame", "-qscale:a", "2", 
                                os.path.abspath(mp3_file)
                            ]
                            
                            process = subprocess.run(cmd, check=True, capture_output=True, text=True)
                            
                            if os.path.exists(mp3_file) and os.path.getsize(mp3_file) > 0:
                                print(f"✅ Succès! Audio MP3 sauvegardé: {mp3_file}")
                                print(f"Taille: {os.path.getsize(mp3_file)} bytes")
                                
                                # Nettoyer le RAW
                                try:
                                    os.remove(raw_file)
                                    print("Fichier RAW intermédiaire supprimé.")
                                except:
                                    pass
                            else:
                                print("❌ Erreur: Le fichier MP3 n'a pas été créé.")
                                print(process.stderr)
                                
                        except subprocess.CalledProcessError as e:
                            print(f"❌ Erreur conversion MP3 (Code {e.returncode}):")
                            print(e.stderr)
                        except Exception as e:
                            print(f"❌ Erreur conversion MP3: {e}")
                        
                        return True
            print("❌ Erreur: Pas de données audio dans la réponse")
            print(str(data)[:500])
            return False
        else:
            print(f"❌ Erreur API: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Test Gemini TTS
    asyncio.run(test_gemini_tts())
