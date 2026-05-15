import logging
import re
import asyncio
from datetime import datetime, timedelta
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import httpx
import os
import tempfile
import shutil
import uuid
import aiofiles
from pathlib import Path

from config import (
    DEEPINFRA_API_KEY, WHISPER_MODEL_URL, AUDIO_OUTPUT_DIR,
    ALLOWED_ORIGINS, MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB,
    ALLOWED_VIDEO_TYPES, ALLOWED_VIDEO_EXTENSIONS,
    RATE_LIMIT_UPLOADS, TEMP_FILE_MAX_AGE_HOURS
)
from utils.helpers import log_debug, format_to_srt, parse_translated_segments
from services.translation import translate_adaptive
from services.tts import generate_segment_audio
from services.audio import process_and_combine_audio, create_dubbed_video, get_audio_url_from_path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="InFrench Backend")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

TEMP_VIDEO_DIR = Path(tempfile.gettempdir()) / "infrench_videos"
TEMP_VIDEO_DIR.mkdir(parents=True, exist_ok=True)


def sanitize_filename(filename: str) -> str:
    safe = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    return safe[:100]


def validate_video_file(video: UploadFile) -> None:
    if not video.filename:
        raise HTTPException(status_code=400, detail="Nom de fichier manquant")
    ext = Path(video.filename).suffix.lower()
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Extension non supportee")
    if video.content_type and video.content_type not in ALLOWED_VIDEO_TYPES:
        raise HTTPException(status_code=400, detail=f"Type non supporte")


async def cleanup_old_files():
    while True:
        try:
            cutoff = datetime.now() - timedelta(hours=TEMP_FILE_MAX_AGE_HOURS)
            cleaned = 0
            for file_path in TEMP_VIDEO_DIR.glob("*"):
                try:
                    if datetime.fromtimestamp(file_path.stat().st_mtime) < cutoff:
                        if file_path.is_file():
                            file_path.unlink()
                        elif file_path.is_dir():
                            shutil.rmtree(file_path)
                        cleaned += 1
                except Exception as e:
                    logger.warning(f"Cleanup failed for {file_path}: {e}")
            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} old temporary files")
        except Exception as e:
            logger.error(f"Cleanup task error: {e}")
        await asyncio.sleep(3600)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(cleanup_old_files())
    logger.info("InFrench Backend started")


@app.get("/")
async def root():
    return {"message": "InFrench Backend - API de doublage video EN->FR"}


@app.post("/api/transcribe")
@limiter.limit(RATE_LIMIT_UPLOADS)
async def transcribe_video(request: Request, video: UploadFile = File(...)):
    if not video:
        raise HTTPException(status_code=400, detail="Aucun fichier video fourni")
    validate_video_file(video)
    temp_video_path = None
    segments_dir = None
    try:
        filename = sanitize_filename(video.filename or "video.mp4")
        suffix = Path(filename).suffix or ".mp4"
        unique_id = str(uuid.uuid4())[:8]
        temp_video_path = TEMP_VIDEO_DIR / f"original_{unique_id}{suffix}"
        total_size = 0
        async with aiofiles.open(temp_video_path, "wb") as f:
            while chunk := await video.read(8192):
                total_size += len(chunk)
                if total_size > MAX_FILE_SIZE_BYTES:
                    if temp_video_path.exists():
                        os.unlink(temp_video_path)
                    raise HTTPException(status_code=413, detail=f"Fichier trop volumineux. Max: {MAX_FILE_SIZE_MB}MB")
                await f.write(chunk)
        segments_dir = Path(tempfile.mkdtemp(prefix="infrench_segments_"))
        logger.info(f"[1/4] Transcription Whisper pour {filename}...")
        async with httpx.AsyncClient(timeout=300.0) as client:
            with open(temp_video_path, "rb") as f:
                files = {"file": (filename, f, video.content_type or "video/mp4")}
                data = {"model": "openai/whisper-large-v3-turbo", "response_format": "verbose_json", "language": "en", "prompt": "The following is a clear English speech."}
                headers = {"Authorization": f"Bearer {DEEPINFRA_API_KEY}"}
                response = await client.post(WHISPER_MODEL_URL, files=files, data=data, headers=headers)
        if response.status_code != 200:
            logger.error(f"Whisper API error: {response.status_code}")
            raise HTTPException(status_code=response.status_code, detail=f"Whisper Error: {response.text}")
        result_whisper = response.json()
        segments_en = result_whisper.get("segments", [])
        logger.info("[2/4] Traduction Mistral...")
        srt_translated_raw = await translate_adaptive(segments_en)
        translated_segments = parse_translated_segments(srt_translated_raw)
        if not translated_segments:
            return JSONResponse(status_code=500, content={"success": False, "error": "Traduction echouee"})
        from job_manager import create_job
        job_id = create_job(total_segments=len(translated_segments))
        asyncio.create_task(process_tts_and_video_background(job_id, translated_segments, segments_en, str(segments_dir), str(temp_video_path)))
        return JSONResponse(content={"success": True, "srt_original": format_to_srt(segments_en), "srt_translated": srt_translated_raw, "video_url": "", "audio_url": "", "filename": filename, "job_id": job_id, "message": "Sous-titres prets. Video en cours de generation..."})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transcription error: {type(e).__name__}: {str(e)}")
        if temp_video_path and Path(temp_video_path).exists():
            os.unlink(temp_video_path)
        if segments_dir and Path(segments_dir).exists():
            shutil.rmtree(segments_dir)
        raise HTTPException(status_code=500, detail=str(e))


async def process_tts_and_video_background(job_id, translated_segments, segments_en, segments_dir, original_video_path):
    from job_manager import update_job_progress, complete_job, fail_job, JobStatus, get_job
    try:
        job = get_job(job_id)
        if not job:
            logger.warning(f"Job {job_id} not found")
            return
        job.status = JobStatus.PROCESSING
        segments_path = Path(segments_dir)
        segments_path.mkdir(parents=True, exist_ok=True)
        audio_files = []
        for i, seg in enumerate(translated_segments):
            try:
                audio_file = await generate_segment_audio(seg["text"], str(i), segments_dir)
                audio_files.append(audio_file)
                update_job_progress(job_id, i + 1)
            except Exception as e:
                logger.error(f"TTS error for segment {i}: {type(e).__name__}: {str(e)}")
                audio_files.append("")
        if any(audio_files):
            total_dur = float(segments_en[-1]["end"]) if segments_en else 10.0
            audio_path = process_and_combine_audio(translated_segments, audio_files, total_dur)
            if audio_path:
                video_url = create_dubbed_video(original_video_path, audio_path)
                audio_url = get_audio_url_from_path(audio_path)
                complete_job(job_id, audio_url, video_url if video_url else None)
                logger.info(f"Job {job_id} completed successfully")
            else:
                fail_job(job_id, "Echec assemblage audio")
                logger.error(f"Job {job_id} failed: audio assembly")
        else:
            fail_job(job_id, "Aucun segment audio genere")
            logger.error(f"Job {job_id} failed: no audio segments")
    except Exception as e:
        logger.error(f"Job {job_id} error: {type(e).__name__}: {str(e)}")
        fail_job(job_id, str(e))
    finally:
        try:
            if Path(segments_dir).exists():
                shutil.rmtree(segments_dir)
            if Path(original_video_path).exists():
                os.unlink(original_video_path)
        except Exception as e:
            logger.warning(f"Cleanup error for job {job_id}: {e}")


@app.get("/api/status/{job_id}")
async def get_job_status(job_id: str):
    from job_manager import get_job
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job introuvable")
    return {"job_id": job.job_id, "status": job.status.value, "progress": job.progress, "total_segments": job.total_segments, "processed_segments": job.processed_segments, "audio_url": job.audio_url, "video_url": job.video_url, "error": job.error}


@app.get("/api/audio-status/{job_id}")
async def get_audio_status(job_id: str):
    return await get_job_status(job_id)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "infrench_backend", "features": ["transcription", "translation", "tts", "video_dubbing"], "tts_model": "Qwen3-TTS"}
