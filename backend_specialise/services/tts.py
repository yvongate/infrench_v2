"""
Service TTS utilisant Qwen3-TTS via DeepInfra
"""
import os
import httpx
import base64
import subprocess
from config import DEEPINFRA_API_KEY, TTS_MODEL_URL, TTS_DEFAULT_VOICE
from utils.helpers import log_debug


async def generate_segment_audio(text: str, index: str, temp_dir: str, voice: str = None) -> str:
    """
    Genere l'audio pour un segment avec Qwen3-TTS.
    
    Args:
        text: Texte a synthetiser
        index: Index du segment (pour le nom de fichier)
        temp_dir: Repertoire temporaire pour les fichiers
        voice: Voix a utiliser (defaut: TTS_DEFAULT_VOICE)
    
    Returns:
        Chemin du fichier audio genere, ou "" en cas d'erreur
    """
    if not text.strip() or len(text.strip()) < 2:
        return ""
    
    if voice is None:
        voice = TTS_DEFAULT_VOICE
    
    if not DEEPINFRA_API_KEY:
        log_debug("DeepInfra API Key missing")
        return ""
    
    output_path = os.path.join(temp_dir, f"segment_{index}.mp3")
    
    headers = {
        "Authorization": f"Bearer {DEEPINFRA_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "input": text,
        "voice": voice,
        "language": "French",
        "response_format": "mp3"
    }
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            log_debug(f"TTS Qwen3: Segment {index} ({len(text)} chars) avec voix {voice}")
            response = await client.post(TTS_MODEL_URL, json=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if "audio" in data:
                    audio_b64 = data["audio"]
                    
                    # Nettoyer le base64 si necessaire
                    if "," in audio_b64:
                        audio_b64 = audio_b64.split(",")[-1]
                    
                    # Decoder et sauvegarder
                    audio_bytes = base64.b64decode(audio_b64)
                    
                    with open(output_path, "wb") as f:
                        f.write(audio_bytes)
                    
                    log_debug(f"TTS Qwen3: Segment {index} OK ({len(audio_bytes)} bytes)")
                    return output_path
                else:
                    log_debug(f"TTS Qwen3: Pas de champ 'audio' dans la reponse: {list(data.keys())}")
            else:
                log_debug(f"TTS Qwen3 Error {response.status_code}: {response.text[:200]}")
                
    except Exception as e:
        log_debug(f"TTS Qwen3 Exception: {type(e).__name__}: {str(e)}")
    
    return ""
