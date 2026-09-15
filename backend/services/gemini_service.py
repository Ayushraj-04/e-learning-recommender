import logging
import os
import re

from google import genai

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def _clean_prerequisites(items):
    """Normalize model output and keep only short, useful prerequisite labels."""
    cleaned = []
    for item in items:
        value = re.sub(r"^[\-\*\d\.\)\s]+", "", str(item)).strip()
        value = re.sub(r"\s+", " ", value)
        if value and value not in cleaned:
            cleaned.append(value[:80])
    return cleaned[:3]


def generate_prerequisites(topic: str):
    """Generate exactly three prerequisites; fall back safely if the model is unavailable."""
    fallback = ["Basic computer knowledge", "Problem-solving fundamentals", "Topic fundamentals"]

    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY is not configured; using fallback prerequisites.")
        return fallback

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        prompt = f"""
You are generating learning prerequisites for the topic: "{topic}".
Return ONLY valid JSON in this exact shape:
{{"prerequisites":["item 1","item 2","item 3"]}}
Rules:
- Exactly 3 items.
- Each item should be a concise prerequisite, not an explanation.
- Do not include markdown or additional keys.
"""
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        text = (response.text or "").strip()

        # Robustly isolate a JSON object even if the model adds code fences.
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("Gemini returned no JSON object.")

        import json
        payload = json.loads(match.group(0))
        prerequisites = _clean_prerequisites(payload.get("prerequisites", []))

        if len(prerequisites) != 3:
            raise ValueError("Gemini did not return exactly three prerequisites.")

        return prerequisites

    except Exception:
        logger.exception("Prerequisite generation failed; using safe fallback.")
        return fallback
