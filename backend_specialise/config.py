import os
from pathlib import Path
from dotenv import load_dotenv

# Charger le .env (local ou racine du projet)
BASE_DIR = Path(__file__).parent
ROOT_DIR = BASE_DIR.parent
load_dotenv(BASE_DIR / ".env")  # .env local (production)
load_dotenv(ROOT_DIR / ".env")  # .env racine (dev)

# API Keys
DEEPINFRA_API_KEY = os.getenv("DEEPINFRA_API_KEY")

# Model URLs
WHISPER_MODEL_URL = os.getenv("WHISPER_MODEL_URL", "https://api.deepinfra.com/v1/openai/audio/transcriptions")
CHAT_MODEL_URL = os.getenv("CHAT_MODEL_URL", "https://api.deepinfra.com/v1/openai/chat/completions")
MISTRAL_MODEL_ID = os.getenv("MISTRAL_MODEL_ID", "mistralai/Mistral-Small-3.2-24B-Instruct-2506")

# TTS Config - Qwen3-TTS
TTS_MODEL_URL = "https://api.deepinfra.com/v1/inference/Qwen/Qwen3-TTS"
TTS_DEFAULT_VOICE = os.getenv("TTS_DEFAULT_VOICE", "Vivian")
TTS_VOICES = ["Vivian", "Serena", "Uncle_Fu", "Dylan", "Eric", "Ryan", "Aiden", "Ono_Anna", "Sohee"]

# Paths
BASE_DIR = Path(__file__).parent
AUDIO_OUTPUT_DIR = BASE_DIR / "static" / "audio"
AUDIO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# CORS
_origins_raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
ALLOWED_ORIGINS = [origin.strip() for origin in _origins_raw.split(",") if origin.strip()]

# Upload limits
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "500"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_VIDEO_TYPES = ["video/mp4", "video/mpeg", "video/quicktime", "video/x-msvideo", "video/webm"]
ALLOWED_VIDEO_EXTENSIONS = [".mp4", ".mpeg", ".mpg", ".mov", ".avi", ".webm"]

# Rate limiting
RATE_LIMIT_UPLOADS = os.getenv("RATE_LIMIT_UPLOADS", "10/hour")

# Cleanup
TEMP_FILE_MAX_AGE_HOURS = int(os.getenv("TEMP_FILE_MAX_AGE_HOURS", "24"))
