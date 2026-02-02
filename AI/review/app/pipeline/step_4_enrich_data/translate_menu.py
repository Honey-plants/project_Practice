from typing import List, Dict
from google import genai
import json
import re

def translate_to_en(
        texts: List[str],
        *,
        api_key: str,
) -> Dict[str, str]:
    client = genai.Client(api_key=api_key)

    prompt = f"""
You are a professional Korean→English translator for food/travel apps.

Rules:
- Do NOT romanize (no Hangul->Latin spelling).
- If ingredient is included in the menu, MUST translate and include in menu name
- others unrelated menu name can be cut off if menu name is too long :
for example: 마무리, 추가, 인분, 
Translate the following Korean food-related terms into natural English.
Return ONLY valid JSON object that maps each Korean term to its English translation.

Terms: {json.dumps(texts, ensure_ascii=False)}
"""
    res = client.models.generate_content(
        model="models/gemini-2.0-flash-lite",
        contents=prompt,
    )
    
    raw = (res.text or "").strip()

    # Remove ```json fences if present
    raw = re.sub(r"^```json\s*|\s*```$", "", raw, flags=re.IGNORECASE).strip()

    try:
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise ValueError("Translation output is not a JSON object")
        # ensure str->str
        return {str(k): str(v) for k, v in parsed.items()}
    except Exception:
        # fallback: empty mapping (won't crash pipeline)
        return {}