# InFrench

Plateforme de doublage video automatique. Traduit et double vos videos anglaises en francais en quelques clics.

## Fonctionnalites

- **Transcription automatique** : Extraction du texte audio avec timestamps (Whisper)
- **Traduction intelligente** : Traduction EN→FR contextuelle (Mistral)
- **Synthese vocale** : Generation audio francais naturel (Qwen3-TTS)
- **Synchronisation** : Audio francais synchronise avec les timestamps originaux
- **Video finale** : Export de la video avec l'audio francais integre

## Architecture

```
infrench_v2/
├── frontend/              # Interface utilisateur (Next.js)
├── backend_principal/     # Authentification (NestJS + Prisma)
└── backend_specialise/    # Pipeline de doublage (FastAPI)
```

### Frontend (Next.js 15 + React 19)
- Interface moderne avec dashboard
- Upload de videos
- Suivi de progression en temps reel
- Telechargement de la video doublee

### Backend Principal (NestJS)
- Authentification avec Better-Auth
- Gestion des utilisateurs
- Sessions securisees avec cookies HTTP-only
- Base de donnees PostgreSQL via Prisma

### Backend Specialise (FastAPI)
- Pipeline de traitement video complet
- APIs DeepInfra (Whisper, Mistral, Qwen3-TTS)
- Assemblage audio avec FFmpeg
- Generation de la video finale

## Tech Stack

| Composant | Technologies |
|-----------|--------------|
| Frontend | Next.js 15, React 19, TailwindCSS, Framer Motion |
| Backend Auth | NestJS, Prisma, Better-Auth, PostgreSQL |
| Backend Video | FastAPI, Python 3.11+, httpx |
| APIs IA | DeepInfra (Whisper, Mistral, Qwen3-TTS) |
| Audio/Video | FFmpeg |

## Installation

### Prerequis

- Node.js 18+
- Python 3.11+
- pnpm
- FFmpeg installe et dans le PATH
- PostgreSQL (pour l'authentification)
- Cle API DeepInfra

### 1. Cloner le projet

```bash
git clone <repo-url>
cd infrench_v2
```

### 2. Configuration environnement

Creer un fichier `.env` a la racine :

```env
DEEPINFRA_API_KEY=votre_cle_api_deepinfra
WHISPER_MODEL_URL=https://api.deepinfra.com/v1/openai/audio/transcriptions
MISTRAL_MODEL_ID=mistralai/Mistral-Small-3.2-24B-Instruct-2506
CHAT_MODEL_URL=https://api.deepinfra.com/v1/openai/chat/completions
TTS_DEFAULT_VOICE=Vivian
```

### 3. Installation Frontend

```bash
cd frontend
pnpm install
```

### 4. Installation Backend Principal (Auth)

```bash
cd backend_principal
pnpm install

# Configurer la base de donnees dans prisma/schema.prisma
npx prisma generate
npx prisma db push
```

### 5. Installation Backend Specialise (Video)

```bash
cd backend_specialise
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

## Lancement

### Mode Developpement

Ouvrir 3 terminaux :

**Terminal 1 - Frontend :**
```bash
cd frontend
pnpm dev
```
→ http://localhost:3000

**Terminal 2 - Backend Auth :**
```bash
cd backend_principal
pnpm start:dev
```
→ http://localhost:3001

**Terminal 3 - Backend Video :**
```bash
cd backend_specialise
source venv/bin/activate
uvicorn main:app --reload --port 8000
```
→ http://localhost:8000

## Authentification

### Desactiver l'authentification (Mode Dev)

Dans `frontend/src/lib/auth-client.ts`, ligne 6 :

```typescript
const AUTH_DISABLED = true;
```

Cela permet d'acceder au dashboard sans login avec un utilisateur fictif "Dev User".

### Activer l'authentification (Production)

Dans `frontend/src/lib/auth-client.ts`, ligne 6 :

```typescript
const AUTH_DISABLED = false;
```

Assurez-vous que :
1. PostgreSQL est en cours d'execution
2. Le backend_principal est lance sur le port 3001
3. La base de donnees est initialisee (`npx prisma db push`)

## Utilisation

1. Acceder a http://localhost:3000
2. Se connecter (ou acceder directement au dashboard si auth desactivee)
3. Aller sur le Dashboard
4. Uploader une video en anglais
5. Attendre le traitement (transcription → traduction → TTS → assemblage)
6. Telecharger la video doublee en francais

## API Endpoints

### Backend Specialise (port 8000)

| Endpoint | Methode | Description |
|----------|---------|-------------|
| `/` | GET | Health check |
| `/transcribe` | POST | Transcription audio → texte avec timestamps |
| `/translate` | POST | Traduction EN→FR des segments |
| `/tts/start` | POST | Demarre la generation TTS (async) |
| `/tts/status/{job_id}` | GET | Statut du job TTS |
| `/full-pipeline` | POST | Pipeline complet (video → video doublee) |
| `/static/audio/*` | GET | Fichiers audio generes |
| `/static/video/*` | GET | Videos doublees |

### Backend Principal (port 3001)

| Endpoint | Methode | Description |
|----------|---------|-------------|
| `/auth/register` | POST | Inscription |
| `/auth/login` | POST | Connexion |
| `/auth/profile` | GET | Profil utilisateur |
| `/auth/logout` | POST | Deconnexion |

## Voix TTS Disponibles

Le modele Qwen3-TTS supporte plusieurs voix :

- **Vivian** (defaut) - Voix feminine
- **Serena** - Voix feminine
- **Dylan** - Voix masculine
- **Eric** - Voix masculine
- **Ryan** - Voix masculine
- **Aiden** - Voix masculine
- **Uncle_Fu** - Voix masculine mature
- **Ono_Anna** - Voix feminine
- **Sohee** - Voix feminine

Changer la voix par defaut dans `.env` :
```env
TTS_DEFAULT_VOICE=Dylan
```

## Structure des fichiers cles

```
backend_specialise/
├── main.py                 # API FastAPI + pipeline complet
├── config.py               # Configuration (API keys, paths)
├── job_manager.py          # Gestion des jobs async
├── services/
│   ├── transcription.py    # Service Whisper
│   ├── translation.py      # Service Mistral
│   ├── tts.py              # Service Qwen3-TTS
│   └── audio.py            # Assemblage FFmpeg + video
└── static/
    ├── audio/              # Fichiers audio generes
    └── video/              # Videos doublees
```

## Troubleshooting

### FFmpeg non trouve
Installer FFmpeg et l'ajouter au PATH :
- Windows : `choco install ffmpeg` ou telecharger depuis ffmpeg.org
- Mac : `brew install ffmpeg`
- Linux : `sudo apt install ffmpeg`

### Erreur API DeepInfra
Verifier que la cle API est valide dans `.env`

### Port deja utilise
Changer le port dans la commande de lancement :
```bash
uvicorn main:app --reload --port 8001
```

## Licence

MIT
