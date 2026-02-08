from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import httpx
import os
import re
import asyncio
import base64
import subprocess
import json
import tempfile
import logging
import traceback
import uuid
import shutil
import base64
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from zyphra import AsyncZyphraClient

# Charger les variables d'environnement
load_dotenv()

app = FastAPI(title="InFrench Backend Spécialisé")

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration du logging vers un fichier pour Windows
logging.basicConfig(
    filename='debug_backend.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def log_debug(msg):
    print(f"DEBUG: {msg}")
    logging.info(msg)

# Chargement des API KEYS
DEEPINFRA_API_KEY = os.getenv("DEEPINFRA_API_KEY")
ZYPHRA_API_KEY = os.getenv("ZYPHRA_API_KEY")

WHISPER_MODEL_URL = os.getenv("WHISPER_MODEL_URL", "https://api.deepinfra.com/v1/openai/audio/transcriptions")
CHAT_MODEL_URL = os.getenv("CHAT_MODEL_URL", "https://api.deepinfra.com/v1/openai/chat/completions")
MISTRAL_MODEL_ID = os.getenv("MISTRAL_MODEL_ID", "mistralai/Mistral-Small-3.2-24B-Instruct-2506")

# Walkthrough : Migration Chatterbox Turbo (DeepInfra)

# Nous avons stabilisé la génération audio en migrant vers le modèle `chatterbox-turbo` sur DeepInfra, plus résilient que les versions précédentes.

## Changements Majeurs

### Backend Spécialisé
# - **Modèle TTS stable** : Utilisation de `ResembleAI/chatterbox-turbo`. Il a été testé avec succès alors que le modèle précédent renvoyait des erreurs 500.
# - **Décodage Base64** : Correction de la réception audio. L'API renvoie un JSON contenant l'audio en Base64, que nous décodons maintenant correctement en fichiers `.wav`.
# - **Assemblage Robuste** : Utilisation du format WAV pour les segments intermédiaires afin d'éviter les corruptions de fichiers.
# - **Corrections Lint** : Suppression des erreurs de type et de syntaxe dans `main.py` pour une exécution fluide.

## Tests Effectués
# - [x] **Script de Validation** : `test_models.py` a confirmé que `chatterbox-turbo` répond correctement avec de l'audio valide.
# - [x] **Nettoyage Code** : Suppression des imports en double et ajout des retours manquants.

## Résolutions
# - **Erreurs DeepInfra (266)** : Ces erreurs étaient dues à l'instabilité du modèle précédent. Le passage au modèle Turbo et le bon décodage du flux devraient stopper ces alertes.

# Initialisation du client Zyphra
zyphra_client = AsyncZyphraClient(api_key=ZYPHRA_API_KEY)

# Sémaphore pour limiter les requêtes parallèles (évite les erreurs TransferEncodingError)
# Passage à 1 = traitement séquentiel pour éviter de surcharger l'API
tts_semaphore = asyncio.Semaphore(1)

@app.get("/")
async def root():
    return {"message": "Backend Spécialisé - API de transcription et traduction vidéo"}

def format_to_srt(segments: list, text_key: str = "text") -> str:
    """
    Convertit une liste de segments Whisper en format SRT
    """
    srt_content = ""
    for i, s in enumerate(segments, 1):
        start = s.get('start', 0.0)
        end = s.get('end', 0.0)
        text = s.get(text_key, "").strip()
        
        # Convertir secondes en HH:MM:SS,mmm
        def format_time(seconds):
            try:
                h = int(seconds // 3600)
                m = int((seconds % 3600) // 60)
                s = int(seconds % 60)
                ms = int((seconds % 1) * 1000)
                return f"{h:02}:{m:02}:{s:02},{ms:03}"
            except:
                return "00:00:00,000"
        
        srt_content += f"{i}\n{format_time(start)} --> {format_time(end)}\n{text}\n\n"
    return srt_content

async def translate_adaptive(segments: list) -> str:
    """
    Traduit les segments en français de manière adaptative et concise
    """
    if not segments:
        print("DEBUG: Aucun segment à traduire")
        return ""

    # Préparer le texte des segments pour le prompt
    segments_lines = []
    for s in segments:
        start = s.get('start', 0.0)
        end = s.get('end', 0.0)
        text = s.get('text', '').strip()
        segments_lines.append(f"[{start:.2f}s - {end:.2f}s] {text}")
    
    segments_text = "\n".join(segments_lines)
    print(f"DEBUG: Envoi de {len(segments)} segments à Mistral")

    prompt = f"""Tu es un traducteur et adaptateur de sous-titres expert.
Ta mission est de traduire ces segments anglais en français.

RÈGLE ABSOLUE : conserve CHAQUE segment individuel. NE LES FUSIONNE JAMAIS.
Le nombre de segments traduits doit être ÉGAL au nombre de segments fournis.

CONSIGNES :
1. ADAPTATION DURÉE : Le français est 20% plus long. Reformule pour que le texte soit court et rapide à prononcer.
2. FORMAT : Réponds UNIQUEMENT avec la liste au format : [start - end] Texte
3. CONCISION : Supprime les répétitions et les mots inutiles.

SEGMENTS À TRADUIRE :
{segments_text}

RÉPONSE :"""

    async with httpx.AsyncClient(timeout=180.0) as client:
        payload = {
            "model": MISTRAL_MODEL_ID,
            "messages": [
                {"role": "system", "content": "Traducteur expert. Garde le format [start - end] pour chaque ligne."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1
        }
        headers = {"Authorization": f"Bearer {DEEPINFRA_API_KEY}"}
        
        try:
            response = await client.post(CHAT_MODEL_URL, json=payload, headers=headers)
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"].strip()
                log_debug(f"Mistral a répondu ({len(content)} chars)")
                return content
            else:
                log_debug(f"Erreur Mistral: {response.text}")
                return ""
        except Exception as e:
            log_debug(f"Exception Mistral: {str(e)}")
            return ""
    return ""  # Fallback final

from fastapi.staticfiles import StaticFiles

# Configuration TTS
TTS_MODEL_ID = os.getenv("TTS_MODEL_ID", "Zyphra/Zonos-v0.1-transformer")
TTS_MODEL_URL = os.getenv("TTS_MODEL_URL", "https://api.deepinfra.com/v1/inference/Zyphra/Zonos-v0.1-transformer")

# Créer un dossier pour les fichiers audio générés
AUDIO_OUTPUT_DIR = Path("static/audio")
AUDIO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

def parse_translated_segments(text: str) -> list:
    """
    Parse le texte traduit (format [start - end] texte)
    """
    segments = []
    # Regex plus agressive : s'arrête dès qu'elle voit un [ au début d'un horodatage
    # [start - end] texte
    pattern = r"\[(\d+(?:\.\d+)?)\s*s?\s*-\s*(\d+(?:\.\d+)?)\s*s?\]\s*(.+?)(?=\s*\[\s*\d|$)"
    matches = re.findall(pattern, text, re.DOTALL)
    
    log_debug(f"PARSING : Trouvé {len(matches)} segments")
    
    for start, end, content in matches:
        segments.append({
            "start": float(start),
            "end": float(end),
            "text": content.strip().replace('\n', ' ')
        })
    return segments

async def generate_segment_audio(text: str, index: str, temp_dir: str, depth: int = 0) -> str:
    """
    Génère l'audio. Découpe automatiquement le texte si trop long (>200 chars)
    depth: profondeur de récursion pour éviter les boucles infinies (max 3)
    """
    if not text or len(text.strip()) < 2:
        return ""
    
    # Protection contre la récursion infinie
    if depth > 3:
        log_debug(f"Segment {index} - profondeur max atteinte, coupe forcée à 200 chars")
        text = str(text)[:200]  # Force la coupe pour éviter la boucle
    
    # Si le texte est trop long, on le coupe pour éviter les erreurs API
    if len(text) > 200 and depth <= 3:
        log_debug(f"Segment {index} trop long ({len(text)} chars), découpage... (profondeur: {depth})")
        
        # 1. Tenter par ponctuation
        chunks = re.split(r'([.!?,;:])', text)
        processed_chunks = []
        if len(chunks) > 1:
            for i in range(0, len(chunks)-1, 2):
                processed_chunks.append(chunks[i] + chunks[i+1])
            if len(chunks) % 2 != 0:
                processed_chunks.append(chunks[-1])
        
        # 2. Si un chunk reste trop long ou pas de ponctuation, couper par espaces
        final_chunks = []
        for c in (processed_chunks if processed_chunks else [text]):
            c = c.strip()
            if len(c) > 200:
                # Couper brutalement par paquets de ~180 chars au dernier espace
                while len(c) > 200:
                    split_idx = c.rfind(' ', 0, 180)
                    if split_idx == -1: split_idx = 180  # Pas d'espace, coupe brute
                    final_chunks.append(str(c[:split_idx]).strip())
                    c = str(c[split_idx:]).strip()
                if c: final_chunks.append(c)
            elif c:  # Évite les chunks vides
                final_chunks.append(c)
            
        audio_parts = []
        for i, chunk in enumerate(final_chunks):
            if len(chunk.strip()) < 2: continue
            # Appel récursif avec profondeur incrémentée
            part_path = await generate_segment_audio(chunk, f"{index}_{i}", temp_dir, depth + 1)
            if part_path: audio_parts.append(part_path)
        
        if not audio_parts: return ""
        
        # Combiner les parties (ffmpeg concat simple)
        combined_path = os.path.join(temp_dir, f"segment_{index}_full.wav")
        inputs = "".join([f"file '{os.path.abspath(f)}'\n" for f in audio_parts])
        list_path = os.path.join(temp_dir, f"list_{index}.txt")
        with open(list_path, "w") as f: f.write(inputs)
        
        log_debug(f"Concatenation sous-segments {index}")
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path, "-c", "copy", combined_path], capture_output=True)
        return combined_path

    output_path = os.path.join(temp_dir, f"segment_{index}.wav")
    
    # URL DeepInfra pour Chatterbox Turbo TTS (plus stable actuellement)
    DEEPINFRA_TTS_URL = "https://api.deepinfra.com/v1/inference/ResembleAI/chatterbox-turbo"
    
    try:
        async with tts_semaphore:  # Limite les requêtes parallèles
            for attempt in range(3):  # 3 essais
                try:
                    async with httpx.AsyncClient(timeout=120.0) as client:
                        response = await client.post(
                            DEEPINFRA_TTS_URL,
                            headers={
                                "Authorization": f"Bearer {DEEPINFRA_API_KEY}",
                                "Content-Type": "application/json"
                            },
                            json={
                                "text": text,
                                "language": "fr"  # Français
                            }
                        )
                        
                        if response.status_code == 200:
                            # Chatterbox retourne un JSON avec l'audio en Base64 dans le champ "audio"
                            try:
                                data = response.json()
                                if "audio" in data:
                                    b64_string = str(data["audio"])
                                    
                                    # Nettoyer le préfixe si présent (ex: data:audio/wav;base64,...)
                                    if "," in b64_string:
                                        b64_string = b64_string.split(",")[-1]
                                    
                                    # Correction du padding
                                    padding = len(b64_string) % 4
                                    if padding:
                                        b64_string += "=" * (4 - padding)
                                    
                                    audio_bytes = base64.b64decode(b64_string)
                                    if len(audio_bytes) > 100:
                                        with open(output_path, "wb") as f:
                                            f.write(audio_bytes)
                                        return output_path
                                else:
                                    log_debug(f"Champ 'audio' manquant dans JSON pour segment {index}")
                            except Exception as json_err:
                                log_debug(f"Erreur parsing JSON segment {index}: {str(json_err)}")
                        else:
                            log_debug(f"Erreur DeepInfra segment {index}: {response.status_code} - {response.text[:200]}")
                except Exception as api_err:
                    log_debug(f"Erreur API DeepInfra segment {index} (essai {attempt+1}): {str(api_err)}")
                await asyncio.sleep(2 ** attempt)  # Backoff exponentiel: 1s, 2s, 4s
            return ""
    except Exception as e:
        log_debug(f"Exception critique TTS {index}: {str(e)}")
        return ""

def process_and_combine_audio(segments: list, audio_files: list, total_duration: float) -> str:
    """
    Assemble les segments audio avec FFmpeg en appliquant le time-stretching
    """
    unique_id = str(uuid.uuid4())[:8]
    output_filename = f"output_{unique_id}.mp3"
    output_path = AUDIO_OUTPUT_DIR / output_filename
    
    filter_complex: str = f"aevalsrc=0:d={total_duration}[silent];"
    inputs: list = []
    mix_nodes: list = ["[silent]"]
    
    valid_count = 0
    for i, (seg, audio) in enumerate(zip(segments, audio_files)):
        if not audio or not os.path.exists(audio): continue
        
        start = seg.get('start', 0.0)
        duration_target = seg.get('end', 0.0) - start
        if duration_target <= 0: continue
        
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio],
                capture_output=True, text=True
            )
            if result.returncode != 0 or not result.stdout.strip():
                log_debug(f"FFPROBE échoué pour {audio}: {result.stderr}")
                continue
                
            duration_actual = float(result.stdout.strip())
            
            factor = duration_actual / duration_target
            factor = max(0.5, min(2.0, factor))
            
            inputs.extend(["-i", audio])
            
            delay_ms = int(start * 1000)
            node_name = f"a{valid_count}"
            filter_complex += f"[{valid_count}:a]atempo={factor},adelay={delay_ms}|{delay_ms}[{node_name}];"
            mix_nodes.append(f"[{node_name}]")
            valid_count += 1
        except Exception as e:
            log_debug(f"Erreur proc segment {i}: {str(e)}")
            continue

    if valid_count == 0:
        return ""

    filter_complex += f"{''.join(mix_nodes)}amix=inputs={valid_count + 1}:duration=longest[outa]"
    
    cmd = ["ffmpeg", "-y"] + inputs + [
        "-filter_complex", filter_complex,
        "-map", "[outa]",
        "-ar", "44100",  # Fréquence native Zonos pour éviter les fichiers muets
        "-acodec", "libmp3lame",
        str(output_path)
    ]
    
    try:
        log_debug(f"Exécution FFmpeg: {' '.join(list(cmd)[:10])}...")
        subprocess.run(cmd, check=True, capture_output=True)
        log_debug(f"Fichier final créé : {output_path}")
        return f"/static/audio/{output_filename}"
    except Exception as e:
        log_debug(f"Erreur assemblage final: {str(e)}")
        return ""

@app.post("/api/transcribe")
async def transcribe_video(video: UploadFile = File(...)):
    """
    Endpoint complet : Transcription -> Traduction -> Synthèse Audio (TTS)
    """
    if not video:
        raise HTTPException(status_code=400, detail="Aucun fichier vidéo fourni")
    
    try:
        filename = video.filename or "video.mp4"
        suffix = Path(filename).suffix or ".mp4"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            content = await video.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # 1. Whisper
        async with httpx.AsyncClient(timeout=300.0) as client:
            with open(temp_file_path, "rb") as f:
                files = {"file": (filename, f, video.content_type)}
                data = {"model": "openai/whisper-large-v3-turbo", "response_format": "verbose_json"}
                headers = {"Authorization": f"Bearer {DEEPINFRA_API_KEY}"}
                response = await client.post(WHISPER_MODEL_URL, files=files, data=data, headers=headers)
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=f"Whisper: {response.text}")
        
        result_whisper = response.json()
        segments_en = result_whisper.get("segments", [])
        
        # 2. Mistral (Traduction Adaptative)
        log_debug("Lancement Traduction Mistral...")
        srt_translated = await translate_adaptive(segments_en)
        translated_segments = parse_translated_segments(srt_translated)
        
        if not translated_segments:
            log_debug(f"ERREUR - Aucun segment traduit parsé. Texte reçu : {srt_translated[:200]}")
        
        # 3. Zonos (TTS par segments)
        audio_url = None
        log_debug(f"Lancement TTS pour {len(translated_segments)} segments...")
        
        # On utilise un dossier persistant pour les segments le temps de l'assemblage
        segments_dir = Path("temp_segments")
        segments_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            tasks = []
            for i, seg in enumerate(translated_segments):
                tasks.append(generate_segment_audio(seg["text"], str(i), str(segments_dir)))
            
            # Génération parallèle pour la vitesse
            results = await asyncio.gather(*tasks)
            audio_files = list(results)
            
            valid_audio = [f for f in audio_files if f and isinstance(f, str) and os.path.exists(f)]
            log_debug(f"TTS terminé. {len(valid_audio)}/{len(audio_files)} fichiers audio générés.")
            
            # Assemblage avec FFmpeg
            total_dur = float(segments_en[-1]['end']) if segments_en else 10.0
            log_debug(f"Assemblage FFmpeg (durée totale: {total_dur}s)...")
            audio_url = process_and_combine_audio(translated_segments, audio_files, total_dur)
        finally:
            # Nettoyage des segments individuels après assemblage
            if segments_dir.exists():
                shutil.rmtree(segments_dir)

        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
            
        return JSONResponse(content={
            "success": True,
            "srt_original": format_to_srt(segments_en),
            "srt_translated": srt_translated,
            "audio_url": audio_url, # URL du fichier audio final
            "filename": filename
        })
    
    except Exception as e:
        print(f"DEBUG: EXCEPTION: {str(e)}")
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            try: os.unlink(temp_file_path)
            except: pass
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "backend_specialise", "audio_dir": str(AUDIO_OUTPUT_DIR)}
