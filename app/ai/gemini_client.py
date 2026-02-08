from typing import List, Dict
from google import genai
from google.genai.types import GenerationConfig
from app.config import get_settings
import asyncio

# =========================
# Load settings
# =========================
settings = get_settings()

if not settings.gemini_api_key:
    raise RuntimeError("GEMINI_API_KEY is missing. Add it to backend/.env")

# =========================
# Gemini client
# =========================
client = genai.Client(api_key=settings.gemini_api_key)

MODEL_NAME = "gemini-2.0-flash"  # ✅ stable


# =========================
# Shared Gemini caller
# =========================
async def call_gemini(
    messages: List[Dict[str, str]],
    temperature: float = 0.7,
) -> str:
    """
    messages format:
    [
        {"role": "system", "content": "..."},
        {"role": "user", "content": "..."}
    ]
    """

    # Combine messages into one prompt
    prompt_parts: list[str] = []

    for msg in messages:
        role = msg.get("role")
        content = msg.get("content", "")

        if role == "system":
            prompt_parts.append(f"System:\n{content}")
        elif role == "user":
            prompt_parts.append(f"User:\n{content}")

    prompt = "\n\n".join(prompt_parts)

    # Run blocking SDK safely inside async
    response = await asyncio.to_thread(
        client.models.generate_content,
        model=MODEL_NAME,
        contents=prompt,
        generation_config=GenerationConfig(
            temperature=temperature,
            max_output_tokens=2048,
        ),
    )

    if not response.text:
        raise RuntimeError("Gemini returned empty content")

    return response.text.strip()