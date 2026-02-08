
import os
import time
import subprocess
import shutil

time.sleep(2)

wav_file = "test_gemini_tts.wav"
temp_wav = "audio.wav"
mp3_file = "test_gemini_tts.mp3"

if os.path.exists(wav_file):
    try:
        # Copier vers un nom simple
        shutil.copy(wav_file, temp_wav)
        print(f"Copied {wav_file} to {temp_wav}")
        
        # Vérifier header
        with open(temp_wav, "rb") as f:
            header = f.read(4)
            print(f"Header: {header}")
            
        # Conversion
        cmd = ["ffmpeg", "-y", "-i", temp_wav, "-c:a", "libmp3lame", "-q:a", "2", mp3_file]
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Conversion success!")
            if os.path.exists(mp3_file):
                print(f"Created {mp3_file} ({os.path.getsize(mp3_file)} bytes)")
        else:
            print("Conversion failed!")
            print(result.stderr)
            
    except Exception as e:
        print(f"Error: {e}")
else:
    print(f"{wav_file} not found")
