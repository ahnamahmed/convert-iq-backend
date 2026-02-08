from typing import Dict, Any
from app.ai.gemini_client import call_gemini


async def prompt1_product_clarity(product_info: str) -> Dict[str, Any]:
    prompt = f"""
Analyze the product information below and extract ONLY the information needed
to write a high-converting eCommerce product page.

Output the following sections clearly and concisely:

1. What this product is (plain English, one sentence)
2. Primary target buyer (who this is for)
3. Secondary buyer (optional, if relevant)
4. Top 3 outcomes the buyer wants after purchasing
5. Top 3 fears or doubts stopping purchase
6. Top 5 features that actually matter to buyers (ignore technical fluff)
7. Proof or trust signals needed to feel confident buying (even if missing)
8. One clear positioning sentence:
   "This is for [buyer] who want [outcome] without [common pain or risk]."

Rules:
- No marketing jargon
- No emotional theory
- Write like a strategist preparing notes for a copywriter
- Be specific and practical

Product Information:
{product_info}
"""

    text = await call_gemini(
        messages=[
            {"role": "system", "content": "You are a senior eCommerce strategist focused on conversion clarity."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.6,
    )

    return {
        "raw_clarity": text,
        "product_info": product_info,
    }


async def prompt2_conversion_description(
    product_clarity: Dict[str, Any],
    product_info: str,
) -> Dict[str, Any]:
    clarity_text = product_clarity.get("raw_clarity", "")

    prompt = f"""
Using the product clarity below, write a HIGH-CONVERTING eCommerce
product description that feels like a top-performing Amazon listing.

WRITE FOR:
- Cold traffic
- Skimming readers
- Purchase confidence

STRUCTURE (FOLLOW EXACTLY):

1. Headline (clear benefit, no hype)
2. Short opener (2-3 lines explaining who this is for and why it matters)
3. Benefit-driven bullet points (5-7 bullets)
4. "Who this is for" section
5. "Who this is NOT for" section
6. Objection handling (answer top 3 buyer doubts clearly)
7. Social proof placeholder
8. Clear, simple call-to-action

STYLE RULES:
- No buzzwords
- No emojis
- No AI mention
- No marketing fluff
- Confident, direct, human tone
- Short sentences
- Easy to scan

Product Clarity:
{clarity_text}

Original Product Information:
{product_info}
"""

    text = await call_gemini(
        messages=[
            {"role": "system", "content": "You are an expert eCommerce copywriter who specializes in Amazon-style conversion writing."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.75,
    )

    return {
        "description": text,
        "product_clarity": product_clarity,
    }


async def prompt3_product_audit(
    product_info: str,
    optimized_description: Dict[str, Any],
) -> Dict[str, Any]:
    description_text = optimized_description.get("description", "")

    prompt = f"""Act as a CRO expert.

Based on the original product information and the optimized description below, provide a short, blunt product page audit.

Output EXACTLY 5 bullet points covering:
1. What is unclear or confusing
2. What is missing that hurts conversion
3. What is weakening trust
4. What should be moved higher on the page
5. One high-impact improvement to test first

Original Product Information:
{product_info}

Optimized Description:
{description_text}
"""

    text = await call_gemini(
        messages=[
            {"role": "system", "content": "You are a Conversion Rate Optimization (CRO) expert. Be direct and honest."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.5,
    )

    return {
        "audit": text,
        "optimized_description": optimized_description,
    }


async def prompt4_ad_hooks_and_test(
    product_info: str,
    optimized_description: Dict[str, Any],
    audit: Dict[str, Any],
) -> Dict[str, Any]:
    description_text = optimized_description.get("description", "")
    audit_text = audit.get("audit", "")

    prompt = f"""Using the optimized product description and audit insights below, generate the following:

SECTION A — Ad Hooks
- 5 short scroll-stopping hooks
- 3 ad angles (problem-aware, desire-driven, proof-based)

SECTION B — A/B Test Recommendation
- ONE test
- Explain WHY it could increase conversion (≤3 lines)

Optimized Description:
{description_text}

Audit Insights:
{audit_text}

Original Product Information:
{product_info}
"""

    text = await call_gemini(
        messages=[
            {"role": "system", "content": "You are an expert in Facebook and Instagram ad copywriting and A/B testing."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.8,
    )

    return {
        "ad_hooks_and_test": text,
        "audit": audit,
    }

