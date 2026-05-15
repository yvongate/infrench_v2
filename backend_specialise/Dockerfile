# InFrench Backend - Dockerfile pour Render
FROM python:3.11-slim

# Installer FFmpeg (necessaire pour le traitement audio/video)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Definir le repertoire de travail
WORKDIR /app

# Copier les requirements et installer les dependances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY . .

# Creer les dossiers necessaires
RUN mkdir -p static/audio static/video

# Exposer le port
EXPOSE 8000

# Commande de demarrage
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
