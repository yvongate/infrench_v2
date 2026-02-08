from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import httpx
import os
import asyncio
import tempfile
import shutil
import uuid
from pathlib import Path

# Imports locaux (Services et Utils)
from config import DEEPINFRA_API_KEY, WHISPER_MODEL_URL, AUDIO_OUTPUT_DIR
from utils.helpers import log_debug, format_to_srt, parse_translated_segments
from services.translation import translate_adaptive
from services.tts import generate_segment_audio
from services.audio import process_and_combine_audio

app = FastAPI(title="InFrench Backend Spécialisé")

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montage des fichiers statiques pour l'audio
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return {"message": "Backend Spécialisé - API de transcription et traduction vidéo (Version Modulaire)"}

@app.post("/api/transcribe")
async def transcribe_video(video: UploadFile = File(...)):
    """
    Endpoint complet : Transcription -> Traduction -> Synthèse Audio (TTS)
    """
    if not video:
        raise HTTPException(status_code=400, detail="Aucun fichier vidéo fourni")
    
    temp_file_path = None
    # Utiliser un répertoire temporaire système pour éviter que Uvicorn --reload ne détecte de changements
    segments_dir_raw = tempfile.mkdtemp(prefix="infrench_segments_")
    segments_dir = Path(segments_dir_raw)
    
    try:
        filename = video.filename or "video.mp4"
        suffix = Path(filename).suffix or ".mp4"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, mode='wb') as temp_file:
            content = await video.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # 1. Whisper (Speech-to-Text)
        log_debug(f"Lancement Transcription Whisper pour {filename}...")
        async with httpx.AsyncClient(timeout=300.0) as client:
            with open(temp_file_path, "rb") as f:
                files = {"file": (filename, f, video.content_type)}
                data = {"model": "openai/whisper-large-v3-turbo", "response_format": "verbose_json"}
                headers = {"Authorization": f"Bearer {DEEPINFRA_API_KEY}"}
                response = await client.post(WHISPER_MODEL_URL, files=files, data=data, headers=headers)
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=f"Whisper Error: {response.text}")
        
        result_whisper = response.json()
        segments_en = result_whisper.get("segments", [])
        
        # 2. Mistral (Traduction Adaptative)
        log_debug("Lancement Traduction Mistral...")
        srt_translated_raw = await translate_adaptive(segments_en)
        translated_segments = parse_translated_segments(srt_translated_raw)
        
        if not translated_segments:
            log_debug("Erreur : Aucun segment traduit n'a pu être parsé.")
            return JSONResponse(status_code=500, content={"success": False, "error": "Traduction échouée"})
        
        # 3. Créer un job TTS en arrière-plan
        from job_manager import create_job, JobStatus
        job_id = create_job(total_segments=len(translated_segments))
        
        # Lancer la génération TTS en arrière-plan (non-bloquant)
        asyncio.create_task(
            process_tts_background(
                job_id, 
                translated_segments, 
                segments_en,
                str(segments_dir)
            )
        )
        
        log_debug(f"Job TTS créé: {job_id} - Retour immédiat au frontend")

        return JSONResponse(content={
            "success": True,
            "srt_original": format_to_srt(segments_en),
            "srt_translated": srt_translated_raw,
            "audio_url": "",  # Sera disponible plus tard via polling
            "filename": filename,
            "job_id": job_id,  # Nouveau: ID pour suivre la progression
            "message": "Sous-titres prêts. Audio en cours de génération..."
        })
    
    except Exception as e:
        log_debug(f"Erreur critique dans le pipeline : {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Nettoyage
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        if segments_dir.exists():
            shutil.rmtree(segments_dir)

async def process_tts_background(job_id: str, translated_segments: list, segments_en: list, segments_dir: str):
    """
    Génère l'audio TTS en arrière-plan sans bloquer le frontend
    Met à jour la progression du job au fur et à mesure
    """
    from job_manager import update_job_progress, complete_job, fail_job, JobStatus, get_job
    
    try:
        job = get_job(job_id)
        if not job:
            log_debug(f"Job {job_id} introuvable")
            return
        
        job.status = JobStatus.PROCESSING
        log_debug(f"[Job {job_id}] Démarrage génération TTS pour {len(translated_segments)} segments")
        
        # Créer le répertoire de segments
        segments_path = Path(segments_dir)
        segments_path.mkdir(parents=True, exist_ok=True)
        
        # Générer chaque segment audio
        audio_files = []
        for i, seg in enumerate(translated_segments):
            try:
                log_debug(f"[Job {job_id}] Génération segment {i+1}/{len(translated_segments)}")
                audio_file = await generate_segment_audio(seg["text"], str(i), segments_dir)
                audio_files.append(audio_file)
                
                # Mettre à jour la progression
                update_job_progress(job_id, i + 1)
                
            except Exception as seg_err:
                log_debug(f"[Job {job_id}] Erreur segment {i}: {str(seg_err)}")
                audio_files.append("")  # Segment vide en cas d'erreur
        
        # Assembler l'audio final
        if any(audio_files):
            total_dur = float(segments_en[-1]['end']) if segments_en else 10.0
            log_debug(f"[Job {job_id}] Assemblage audio final (durée: {total_dur}s)")
            audio_url = process_and_combine_audio(translated_segments, audio_files, total_dur)
            
            complete_job(job_id, audio_url)
            log_debug(f"[Job {job_id}] ✅ Terminé - Audio: {audio_url}")
        else:
            fail_job(job_id, "Aucun segment audio n'a pu être généré")
            log_debug(f"[Job {job_id}] ❌ Échec - Aucun audio généré")
        
        # Nettoyage du répertoire de segments
        if segments_path.exists():
            shutil.rmtree(segments_path)
            
    except Exception as e:
        fail_job(job_id, str(e))
        log_debug(f"[Job {job_id}] ❌ Erreur critique: {str(e)}")

@app.get("/api/audio-status/{job_id}")
async def get_audio_status(job_id: str):
    """
    Endpoint de polling pour vérifier le statut de génération audio
    Le frontend appelle cet endpoint toutes les 2 secondes
    """
    from job_manager import get_job
    
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job introuvable")
    
    return {
        "job_id": job.job_id,
        "status": job.status.value,
        "progress": job.progress,
        "total_segments": job.total_segments,
        "processed_segments": job.processed_segments,
        "audio_url": job.audio_url,
        "error": job.error
    }

@app.get("/api/audio/{job_id}")
async def get_audio_file(job_id: str):
    """
    Retourne l'URL de l'audio une fois la génération terminée
    """
    from job_manager import get_job, JobStatus
    
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job introuvable")
    
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Audio pas encore prêt")
    
    if not job.audio_url:
        raise HTTPException(status_code=500, detail="Erreur: audio_url manquant")
    
    return {"audio_url": job.audio_url}

@app.get("/health")
async def health_check():
    return {
        "status": "ok", 
        "service": "backend_specialise", 
        "audio_dir": str(AUDIO_OUTPUT_DIR),
        "api_key_configured": bool(DEEPINFRA_API_KEY)
    }
