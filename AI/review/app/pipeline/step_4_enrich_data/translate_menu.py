from typing import List, Dict
from google import genai


def translate_to_en(
    texts: List[str],
    *,
    api_key: str,
) -> Dict[str, str]:

    client = genai.Client(api_key=api_key)

    prompt = f"""
Translate the following Korean food-related terms into natural English.
Return JSON mapping.

{texts}
"""

    res = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt,
    )

    return res.text  # → JSON string
