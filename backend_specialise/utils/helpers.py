import os
import tempfile
import logging
import re

# Configuration du logging sécurisée contre uvicorn --reload
LOG_FILE = os.path.join(tempfile.gettempdir(), 'infrench_debug.log')

# Forcer la reconfiguration même si logging.basicConfig a déjà été appelé
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    force=True # Option Python 3.8+ pour écraser la config précédente
)

def log_debug(msg):
    print(f"DEBUG: {msg}")
    try:
        logging.info(msg)
    except:
        pass

def format_time(seconds):
    """Convertit secondes en HH:MM:SS,mmm"""
    try:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"
    except:
        return "00:00:00,000"

def format_to_srt(segments: list, text_key: str = "text") -> str:
    """Convertit une liste de segments Whisper en format SRT"""
    srt_content = ""
    for i, s in enumerate(segments, 1):
        start = s.get('start', 0.0)
        end = s.get('end', 0.0)
        text = s.get(text_key, "").strip()
        srt_content += f"{i}\n{format_time(start)} --> {format_time(end)}\n{text}\n\n"
    return srt_content

def parse_translated_segments(text: str) -> list:
    """Parse le texte traduit (format [start - end] texte)"""
    segments = []
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
