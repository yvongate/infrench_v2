"""
Gestionnaire de taches TTS en arriere-plan
Permet de generer l'audio et la video de maniere asynchrone sans bloquer le frontend
"""

import asyncio
from typing import Dict, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid

class JobStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class TTSJob:
    job_id: str
    status: JobStatus
    created_at: datetime = field(default_factory=datetime.now)
    audio_url: Optional[str] = None
    video_url: Optional[str] = None  # URL de la video doublee
    error: Optional[str] = None
    progress: int = 0  # 0-100
    total_segments: int = 0
    processed_segments: int = 0

# Stockage en memoire (simple pour MVP)
jobs: Dict[str, TTSJob] = {}

def create_job(total_segments: int) -> str:
    """Cree un nouveau job TTS et retourne son ID"""
    job_id = str(uuid.uuid4())
    jobs[job_id] = TTSJob(
        job_id=job_id,
        status=JobStatus.PENDING,
        total_segments=total_segments
    )
    return job_id

def get_job(job_id: str) -> Optional[TTSJob]:
    """Recupere un job par son ID"""
    return jobs.get(job_id)

def update_job_progress(job_id: str, processed_segments: int):
    """Met a jour la progression d'un job"""
    job = jobs.get(job_id)
    if job:
        job.processed_segments = processed_segments
        if job.total_segments > 0:
            job.progress = int((processed_segments / job.total_segments) * 100)

def complete_job(job_id: str, audio_url: str, video_url: str = None):
    """Marque un job comme termine"""
    job = jobs.get(job_id)
    if job:
        job.status = JobStatus.COMPLETED
        job.audio_url = audio_url
        job.video_url = video_url
        job.progress = 100

def fail_job(job_id: str, error: str):
    """Marque un job comme echoue"""
    job = jobs.get(job_id)
    if job:
        job.status = JobStatus.FAILED
        job.error = error
