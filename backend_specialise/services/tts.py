import os
import httpx
import base64
import asyncio
import re
import subprocess
from config import DEEPINFRA_API_KEY, TTS_MODEL_URL, REFERENCE_VOICE_PATH
from utils.helpers import log_debug

# Sémaphore pour limiter les requêtes parallèles
# Zonos ne supporte pas bien les requêtes parallèles - forcer séquentiel comme dans test_models
tts_semaphore = asyncio.Semaphore(1)
_tts_client = None

async def get_tts_client():
    global _tts_client
    if _tts_client is None or _tts_client.is_closed:
        _tts_client = httpx.AsyncClient(timeout=120.0, limits=httpx.Limits(max_connections=10, max_keepalive_connections=5))
    return _tts_client

def get_reference_audio_b64():
    if os.path.exists(REFERENCE_VOICE_PATH):
        with open(REFERENCE_VOICE_PATH, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return None

REFERENCE_AUDIO_B64 = get_reference_audio_b64()

# --- GEMINI TTS IMPLEMENTATION (REST API) ---
async def generate_segment_audio_gemini(text: str, index: str, temp_dir: str) -> str:
    """
    Génère l'audio avec Gemini TTS (via REST API pour éviter les problèmes de SDK).
    Utilise le modèle gemini-2.5-flash-preview-tts validé.
    """
    GOOGLE_AI_API_KEY = os.getenv("GOOGLE_AI_API_KEY")
    if not GOOGLE_AI_API_KEY:
        log_debug("Gemini API Key missing")
        return ""
        
    output_path = os.path.join(temp_dir, f"segment_{index}.wav")
    model_name = "gemini-2.5-flash-preview-tts"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GOOGLE_AI_API_KEY}"
    
    payload = {
        "contents": [{
            "parts": [{"text": text}]
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
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
            
            if response.status_code == 200:
                data = response.json()
                if "candidates" in data and len(data["candidates"]) > 0:
                    parts = data["candidates"][0]["content"]["parts"]
                    for part in parts:
                        if "inlineData" in part:
                            audio_bytes = base64.b64decode(part['inlineData']['data'])
                            
                            # Sauvegarder en RAW data (PCM)
                            # Gemini retourne du Linear16 (PCM s16le) souvent à 24kHz pour tts
                            raw_path = output_path.replace(".mp3", ".raw")
                            with open(raw_path, "wb") as f:
                                f.write(audio_bytes)
                            
                            # Convertir PCM -> MP3
                            # Paramètres supposés: s16le, 24000Hz, mono
                            try:
                                subprocess.run([
                                    "ffmpeg", "-y", 
                                    "-f", "s16le", "-ar", "24000", "-ac", "1", "-i", raw_path,
                                    "-codec:a", "libmp3lame", "-qscale:a", "2", 
                                    output_path
                                ], check=True, capture_output=True)
                                
                                # Nettoyer le RAW
                                if os.path.exists(raw_path):
                                    os.remove(raw_path)
                                    
                                return output_path
                            except Exception as conv_err:
                                log_debug(f"FFmpeg conversion error: {conv_err}")
                                # En cas d'échec, renommer .raw en .wav en ajoutant un header minimal serait mieux
                                # Mais retournons le raw renommé .wav pour l'instant (jouable par certains lecteurs raw)
                                fallback_wav = output_path.replace(".mp3", ".wav")
                                if os.path.exists(raw_path):
                                    os.rename(raw_path, fallback_wav)
                                return fallback_wav

                log_debug(f"Gemini TTS: No audio data in response: {str(data)[:200]}")
            else:
                log_debug(f"Gemini TTS Error {response.status_code}: {response.text[:200]}")
    except Exception as e:
        log_debug(f"Gemini TTS Exception: {str(e)}")
        
    return ""

async def generate_segment_audio(text: str, index: str, temp_dir: str, depth: int = 0) -> str:
    """
    Fonction principale de génération audio.
    Utilise Gemini et gère le découpage pour les textes longs.
    """
    if not text.strip() or len(text.strip()) < 2:
        return ""

    # Découpage si texte trop long 
    if len(text) > 500 and depth < 3:
        log_debug(f"Texte long ({len(text)} chars), découpage du segment {index}")
        chunks = re.split(r'([.!?,;:])', text)
        processed_chunks = []
        if len(chunks) > 1:
            for i in range(0, len(chunks)-1, 2):
                processed_chunks.append(chunks[i] + chunks[i+1])
            if len(chunks) % 2 != 0:
                processed_chunks.append(chunks[-1])
        else:
            processed_chunks = [text]

        audio_parts = []
        for i, chunk in enumerate(processed_chunks):
            chunk = chunk.strip()
            if len(chunk) < 2: continue
            part_path = await generate_segment_audio(chunk, f"{index}_{i}", temp_dir, depth + 1)
            if part_path: audio_parts.append(part_path)
        
        if not audio_parts: return ""
        
        # Concaténation des morceaux
        combined_path = os.path.join(temp_dir, f"segment_{index}_combined.mp3")
        inputs = []
        for p in audio_parts:
            inputs.extend(["-i", p])
        
        filter_complex = "".join([f"[{i}:a]" for i in range(len(audio_parts))]) + f"concat=n={len(audio_parts)}:v=0:a=1[outa]"
        
        cmd = ["ffmpeg", "-y"] + inputs + ["-filter_complex", filter_complex, "-map", "[outa]", combined_path]
        subprocess.run(cmd, capture_output=True)
        return combined_path

    # Utilisation directe de Gemini pour le segment
    return await generate_segment_audio_gemini(text, index, temp_dir)
