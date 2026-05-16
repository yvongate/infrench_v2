import os
import subprocess
import uuid
from pathlib import Path
from config import AUDIO_OUTPUT_DIR
from utils.helpers import log_debug

# Creer un dossier pour les videos finales
VIDEO_OUTPUT_DIR = AUDIO_OUTPUT_DIR.parent / "video"
VIDEO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


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
                log_debug(f"FFPROBE echoue pour {audio}: {result.stderr}")
                continue

            duration_actual = float(result.stdout.strip())

            # Calculer le facteur de time-stretch
            factor = duration_actual / duration_target

            # Construire la chaîne atempo (supporte 0.5-2.0 par filtre)
            # Pour des facteurs extrêmes, on chaîne plusieurs filtres
            atempo_chain = []
            remaining_factor = factor

            if remaining_factor < 0.5:
                # Besoin de ralentir beaucoup (ex: 0.25 = 0.5 * 0.5)
                while remaining_factor < 0.5:
                    atempo_chain.append("atempo=0.5")
                    remaining_factor = remaining_factor / 0.5
                if 0.5 <= remaining_factor <= 2.0:
                    atempo_chain.append(f"atempo={remaining_factor:.3f}")
            elif remaining_factor > 2.0:
                # Besoin d'accélérer beaucoup (ex: 4.0 = 2.0 * 2.0)
                while remaining_factor > 2.0:
                    atempo_chain.append("atempo=2.0")
                    remaining_factor = remaining_factor / 2.0
                if 0.5 <= remaining_factor <= 2.0:
                    atempo_chain.append(f"atempo={remaining_factor:.3f}")
            else:
                atempo_chain.append(f"atempo={factor:.3f}")

            atempo_filter = ",".join(atempo_chain) if atempo_chain else "atempo=1.0"

            inputs.extend(["-i", audio])

            delay_ms = int(start * 1000)
            node_name = f"a{valid_count}"
            filter_parts.append(f"[{valid_count}:a]{atempo_filter},adelay={delay_ms}|{delay_ms}[{node_name}];")
            mix_nodes.append(f"[{node_name}]")
            valid_count += 1
        except Exception as e:
            log_debug(f"Erreur proc segment {i}: {str(e)}")
            continue

    if valid_count == 0:
        return ""

    # amix + volume boost (2.5x) pour compenser le mixage
    filter_complex = "".join(filter_parts) + f"{''.join(mix_nodes)}amix=inputs={valid_count + 1}:duration=longest,volume=2.5[outa]"

    cmd = ["ffmpeg", "-y"] + inputs + [
        "-filter_complex", filter_complex,
        "-map", "[outa]",
        "-ar", "44100",
        "-acodec", "libmp3lame",
        str(output_path)
    ]

    try:
        log_debug(f"Execution FFmpeg assemblage audio...")
        subprocess.run(cmd, check=True, capture_output=True)
        log_debug(f"Audio assemble: {output_path}")
        return str(output_path)
    except Exception as e:
        log_debug(f"Erreur assemblage audio: {str(e)}")
        return ""


def create_dubbed_video(original_video_path: str, french_audio_path: str) -> str:
    """
    Cree la video finale en remplacant l'audio original par l'audio francais.

    Args:
        original_video_path: Chemin vers la video originale
        french_audio_path: Chemin vers l'audio francais assemble

    Returns:
        URL relative de la video finale (/static/video/xxx.mp4)
    """
    if not original_video_path or not os.path.exists(original_video_path):
        log_debug(f"Video originale introuvable: {original_video_path}")
        return ""

    if not french_audio_path or not os.path.exists(french_audio_path):
        log_debug(f"Audio francais introuvable: {french_audio_path}")
        return ""

    unique_id = str(uuid.uuid4())[:8]
    output_filename = f"dubbed_{unique_id}.mp4"
    output_path = VIDEO_OUTPUT_DIR / output_filename

    # FFmpeg: remplacer l'audio de la video par l'audio francais
    # -c:v copy = copier la video sans re-encoder (rapide)
    # -map 0:v = prendre la piste video du premier fichier (video originale)
    # -map 1:a = prendre la piste audio du deuxieme fichier (audio francais)
    # -shortest = arreter quand le plus court des deux se termine
    cmd = [
        "ffmpeg", "-y",
        "-i", original_video_path,
        "-i", french_audio_path,
        "-c:v", "copy",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        str(output_path)
    ]

    try:
        log_debug(f"Creation video doublee...")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0 and output_path.exists():
            log_debug(f"Video doublee creee: {output_path}")
            return f"/static/video/{output_filename}"
        else:
            log_debug(f"Erreur FFmpeg video: {result.stderr[:500]}")
            return ""
    except Exception as e:
        log_debug(f"Exception creation video: {str(e)}")
        return ""


def get_audio_url_from_path(audio_path: str) -> str:
    """Convertit un chemin absolu en URL relative pour l'API"""
    if not audio_path:
        return ""
    filename = Path(audio_path).name
    return f"/static/audio/{filename}"
