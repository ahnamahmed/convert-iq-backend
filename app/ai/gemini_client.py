from typing import List, Dict
from google import genai
from app.config import get_settings

# =========================
# Load settings
# =========================
settings = get_settings()

if not settings.gemini_api_key:
    raise RuntimeError(
        "GEMINI_API_KEY is missing. Add it to backend/.env"
    )

# =========================
# Gemini client
# =========================
client = genai.Client(
    api_key=settings.gemini_api_key
)

MODEL_NAME = "gemini-3-flash"


# =========================
# Shared Gemini caller
# =========================
async def call_gemini(
    messages: List[Dict[str, str]],
    temperature: float = 0.7,
) -> str:
    """
    messages format (OpenAI-compatible):
    [
        {"role": "system", "content": "..."},
        {"role": "user", "content": "..."}
    ]
    """

    # Combine messages into a single prompt (Gemini prefers this)
    prompt_parts: List[str] = []

    for msg in messages:
        role = msg["role"]
        content = msg["content"]

        if role == "system":
            prompt_parts.append(f"System:\n{content}")
        elif role == "user":
            prompt_parts.append(f"User:\n{content}")

    prompt = "\n\n".join(prompt_parts)

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        generation_config={
            "temperature": temperature,
            "max_output_tokens": 2048,
        },
    )

    if not response.text:
        raise RuntimeError("Gemini returned empty content")

    return response.text.strip()