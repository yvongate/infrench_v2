"""
Gestionnaire de tâches TTS en arrière-plan
Permet de générer l'audio de manière asynchrone sans bloquer le frontend

TODO Production:
- Migrer vers Redis pour persistance entre redémarrages
- Ajouter un système de nettoyage automatique des vieux jobs
- Implémenter des limites de rate par utilisateur
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
    error: Optional[str] = None
    progress: int = 0  # 0-100
    total_segments: int = 0
    processed_segments: int = 0

# Stockage en mémoire (simple pour MVP)
# TODO Production: Migrer vers Redis
jobs: Dict[str, TTSJob] = {}

def create_job(total_segments: int) -> str:
    """Crée un nouveau job TTS et retourne son ID"""
    job_id = str(uuid.uuid4())
    jobs[job_id] = TTSJob(
        job_id=job_id,
        status=JobStatus.PENDING,
        total_segments=total_segments
    )
    return job_id

def get_job(job_id: str) -> Optional[TTSJob]:
    """Récupère un job par son ID"""
    return jobs.get(job_id)

def update_job_progress(job_id: str, processed_segments: int):
    """Met à jour la progression d'un job"""
    job = jobs.get(job_id)
    if job:
        job.processed_segments = processed_segments
        if job.total_segments > 0:
            job.progress = int((processed_segments / job.total_segments) * 100)

def complete_job(job_id: str, audio_url: str):
    """Marque un job comme terminé"""
    job = jobs.get(job_id)
    if job:
        job.status = JobStatus.COMPLETED
        job.audio_url = audio_url
        job.progress = 100

def fail_job(job_id: str, error: str):
    """Marque un job comme échoué"""
    job = jobs.get(job_id)
    if job:
        job.status = JobStatus.FAILED
        job.error = error

def cleanup_old_jobs(max_age_hours: int = 1):
    """Nettoie les jobs terminés de plus de X heures"""
    # TODO: Implémenter le nettoyage automatique
    pass
