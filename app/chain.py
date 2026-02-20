from typing import Dict, Any, Optional, List, TypedDict
from app.config import get_settings
from app.cache import cache_prompt1_output, get_cached_prompt1_output
from app.ai.openrouter_client import generate_text_with_fallback
import re

settings = get_settings()

# =========================
# Safety check (OpenRouter)
# =========================
if not settings.openrouter_api_key:
    raise RuntimeError(
        "OPENROUTER_API_KEY is missing. Make sure it exists in backend/.env"
    )

class PromptChainResult(TypedDict, total=False):
    title: str
    bullets: List[str]
    description: str
    audit: str
    ad_hooks_and_test: str


async def runPromptChain(
    user_id: str,
    product_info: str,
    run_prompt1: bool = True,
    run_prompt2: bool = True,
    run_prompt3: bool = True,
    run_prompt4: bool = True,
) -> PromptChainResult:
    """
    Executes a chained AI pipeline.
    Prompt 1 output is cached.
    Prompts 2-4 depend on previous steps.
    """

    # -------------------------
    # Shared AI caller (OpenRouter)
    # DO NOT RENAME — no refactor
    # -------------------------
    async def call_openai(
        messages: List[Dict[str, str]],
        temperature: float,
    ) -> str:
        return await generate_text_with_fallback(
            messages=messages,
            temperature=temperature,
        )

    async def prompt1(product_info: str) -> Dict[str, Any]:
        prompt = f"""
Analyze the product information below and extract:

1. Product type
2. Target customer persona
3. Primary problem solved
4. Top 3 emotional triggers
5. Likely objections
6. Price sensitivity (low / medium / high)
7. One-sentence core value proposition

Product information:
{product_info}

Return structured sections.
"""
        analysis = await call_openai(
            [
                {"role": "system", "content": "You are an expert eCommerce product analyst."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.6,
        )

        return {"raw_analysis": analysis, "product_info": product_info}

    async def prompt2(p1: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
Using the product understanding below, write a HIGH-CONVERTING product description.

RULES:
- Conversion-focused
- No buzzwords
- Skimmable
- Shopify-ready

STRUCTURE:
1. Hook headline
2. Emotional opener
3. Feature → Benefit bullets (min 5)
4. Objection handling
5. Social proof placeholder
6. Clear CTA

Product Understanding:
{p1["raw_analysis"]}

Original Product Info:
{product_info}
"""
        description = await call_openai(
            [
                {"role": "system", "content": "You are a high-converting eCommerce copywriter."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.8,
        )

        return {"description": description}

    async def prompt3(description: str) -> Dict[str, Any]:
        prompt = f"""
Act as a CRO expert.

Give EXACTLY 5 bullets:
1. Confusion points
2. Missing conversion elements
3. Trust weaknesses
4. What to move higher
5. One test to run first

Original Product Info:
{product_info}

Optimized Description:
{description}
"""
        audit = await call_openai(
            [
                {"role": "system", "content": "You are a CRO expert. Be blunt."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
        )

        return {"audit": audit}

    async def prompt4(description: str, audit: str) -> Dict[str, Any]:
        prompt = f"""
Generate:

SECTION A — Ad Hooks
- 5 hooks
- 3 angles: Problem, Desire, Proof

SECTION B — A/B Test
- One test
- Why it works (≤3 lines)

Rules:
- No emojis
- Facebook/Instagram tone

Description:
{description}

Audit:
{audit}
"""
        ads = await call_openai(
            [
                {"role": "system", "content": "You are a paid ads and A/B testing expert."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.8,
        )

        return {"ad_hooks_and_test": ads}

    def parse_description(text: str) -> Dict[str, Any]:
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        title = lines[0][:100] if lines else "Product Description"

        bullets = []
        for line in lines:
            if line.startswith(("-", "•", "*")):
                clean = re.sub(r"\*\*", "", line[1:]).strip()
                if len(clean) > 10:
                    bullets.append(clean)

        return {
            "title": title,
            "bullets": bullets[:10],
            "description": text,
        }

    result: PromptChainResult = {}

    try:
        p1_data = None
        if run_prompt1:
            cached = get_cached_prompt1_output(user_id, product_info)
            p1_data = cached or await prompt1(product_info)
            if not cached:
                cache_prompt1_output(user_id, product_info, p1_data)

        p2_data = None
        if run_prompt2 and p1_data:
            p2_data = await prompt2(p1_data)
            result.update(parse_description(p2_data["description"]))

        p3_data = None
        if run_prompt3 and p2_data:
            p3_data = await prompt3(p2_data["description"])
            result["audit"] = p3_data["audit"]

        if run_prompt4 and p2_data and p3_data:
            p4_data = await prompt4(p2_data["description"], p3_data["audit"])
            result["ad_hooks_and_test"] = p4_data["ad_hooks_and_test"]

        return result

    except Exception as e:
        raise RuntimeError(f"AI chain execution failed: {e}")