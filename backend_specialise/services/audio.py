import os
import subprocess
import uuid
from config import AUDIO_OUTPUT_DIR
from utils.helpers import log_debug

def process_and_combine_audio(segments: list, audio_files: list, total_duration: float) -> str:
    """Assemble les segments audio avec FFmpeg en appliquant le time-stretching"""
    unique_id = str(uuid.uuid4())[:8]
    output_filename = f"output_{unique_id}.mp3"
    output_path = AUDIO_OUTPUT_DIR / output_filename
    
    filter_parts: list[str] = [f"aevalsrc=0:d={total_duration}[silent];"]
    inputs: list = []
    mix_nodes: list[str] = ["[silent]"]
    
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
            filter_parts.append(f"[{valid_count}:a]atempo={factor},adelay={delay_ms}|{delay_ms}[{node_name}];")
            mix_nodes.append(f"[{node_name}]")
            valid_count += 1
        except Exception as e:
            log_debug(f"Erreur proc segment {i}: {str(e)}")
            continue

    if valid_count == 0:
        return ""

    filter_complex = "".join(filter_parts) + f"{''.join(mix_nodes)}amix=inputs={valid_count + 1}:duration=longest[outa]"
    
    cmd = ["ffmpeg", "-y"] + inputs + [
        "-filter_complex", filter_complex,
        "-map", "[outa]",
        "-ar", "44100",
        "-acodec", "libmp3lame",
        str(output_path)
    ]
    
    try:
        log_debug(f"Exécution FFmpeg finale...")
        subprocess.run(cmd, check=True, capture_output=True)
        log_debug(f"Fichier final créé : {output_path}")
        return f"/static/audio/{output_filename}"
    except Exception as e:
        log_debug(f"Erreur assemblage final: {str(e)}")
        return ""
