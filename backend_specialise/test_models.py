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

if __name__ == "__main__":
    asyncio.run(main())
