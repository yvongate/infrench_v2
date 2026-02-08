import httpx
from config import CHAT_MODEL_URL, MISTRAL_MODEL_ID, DEEPINFRA_API_KEY
from utils.helpers import log_debug

async def translate_adaptive(segments: list) -> str:
    """Traduit les segments en français de manière adaptative et concise"""
    if not segments:
        return ""

    segments_lines = []
    for s in segments:
        start = s.get('start', 0.0)
        end = s.get('end', 0.0)
        text = s.get('text', '').strip()
        segments_lines.append(f"[{start:.2f}s - {end:.2f}s] {text}")
    
    segments_text = "\n".join(segments_lines)
    log_debug(f"Envoi de {len(segments)} segments à Mistral")

    prompt = f"""Tu es un traducteur et adaptateur de sous-titres expert.
Ta mission est de traduire ces segments anglais en français.

RÈGLE ABSOLUE : conserve CHAQUE segment individuel. NE LES FUSIONNE JAMAIS.
Le nombre de segments traduits doit être ÉGAL au nombre de segments fournis.

CONSIGNES :
1. ADAPTATION DURÉE : Le français est 20% plus long. Reformule pour que le texte soit court et rapide à prononcer.
2. FORMAT : Réponds UNIQUEMENT avec la liste au format : [start - end] Texte
3. CONCISION : Supprime les répétitions et les mots inutiles.

SEGMENTS À TRADUIRE :
{segments_text}

RÉPONSE :"""

    async with httpx.AsyncClient(timeout=180.0) as client:
        payload = {
            "model": MISTRAL_MODEL_ID,
            "messages": [
                {"role": "system", "content": "Traducteur expert. Garde le format [start - end] pour chaque ligne."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1
        }
        headers = {"Authorization": f"Bearer {DEEPINFRA_API_KEY}"}
        
        try:
            response = await client.post(CHAT_MODEL_URL, json=payload, headers=headers)
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"].strip()
                log_debug(f"Mistral a répondu ({len(content)} chars)")
                return content
            else:
                log_debug(f"Erreur Mistral: {response.text}")
                return ""
        except Exception as e:
            log_debug(f"Exception Mistral: {str(e)}")
            return ""
    
    return ""
