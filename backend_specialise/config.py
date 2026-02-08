import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# API Keys
DEEPINFRA_API_KEY = os.getenv("DEEPINFRA_API_KEY")
ZYPHRA_API_KEY = os.getenv("ZYPHRA_API_KEY")

# Model URLs
WHISPER_MODEL_URL = os.getenv("WHISPER_MODEL_URL", "https://api.deepinfra.com/v1/openai/audio/transcriptions")
CHAT_MODEL_URL = os.getenv("CHAT_MODEL_URL", "https://api.deepinfra.com/v1/openai/chat/completions")
MISTRAL_MODEL_ID = os.getenv("MISTRAL_MODEL_ID", "mistralai/Mistral-Small-3.2-24B-Instruct-2506")

# TTS Config
TTS_MODEL_ID = os.getenv("TTS_MODEL_ID", "Zyphra/Zonos-v0.1-transformer")
TTS_MODEL_URL = os.getenv("TTS_MODEL_URL", "https://api.deepinfra.com/v1/inference/Zyphra/Zonos-v0.1-transformer")

# Paths
BASE_DIR = Path(__file__).parent
AUDIO_OUTPUT_DIR = BASE_DIR / "static" / "audio"
AUDIO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

REFERENCE_VOICE_PATH = BASE_DIR / "reference_voice_compress.wav"
