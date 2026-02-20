# app/ai/openrouter_client.py

import httpx
import asyncio
from typing import List, Dict
from app.config import get_settings

settings = get_settings()

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterError(Exception):
    pass


async def _call_openrouter(
    *,
    messages: List[Dict[str, str]],
    temperature: float,
    model: str,
) -> str:
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "AI SaaS App",
    }

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(OPENROUTER_URL, headers=headers, json=payload)

    if resp.status_code != 200:
        raise OpenRouterError(resp.text)

    data = resp.json()

    try:
        return data["choices"][0]["message"]["content"]
    except Exception:
        raise OpenRouterError(f"Malformed OpenRouter response: {data}")


async def generate_text_with_fallback(
    *,
    messages: List[Dict[str, str]],
    temperature: float = 0.7,
    retries_per_model: int = 2,
) -> str:
    """
    Tries primary model first, then fallback model.
    Retries each model N times before switching.
    """

    models = [
        settings.openrouter_primary_model,
        settings.openrouter_fallback_model,
    ]

    errors: list[str] = []

    for model in models:
        for attempt in range(1, retries_per_model + 1):
            try:
                return await _call_openrouter(
                    messages=messages,
                    temperature=temperature,
                    model=model,
                )
            except Exception as e:
                errors.append(f"{model} (attempt {attempt}): {e}")
                await asyncio.sleep(1)

    raise RuntimeError("All LLM attempts failed: " + " | ".join(errors))
