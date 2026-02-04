from openai import OpenAI
from typing import Dict, Any
from config import get_settings

settings = get_settings()
client = OpenAI(api_key=settings.openai_api_key)


def prompt1_product_clarity(product_info: str) -> Dict[str, Any]:
    """
    PROMPT 1 — PRODUCT CLARITY & POSITIONING (MVP FOUNDATION)
    Extracts clear, conversion-focused insights for product page copy.
    """
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

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a senior eCommerce strategist focused on conversion clarity."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.6
    )

    analysis_text = response.choices[0].message.content

    return {
        "raw_clarity": analysis_text,
        "product_info": product_info
    }


def prompt2_conversion_description(product_clarity: Dict[str, Any], product_info: str) -> Dict[str, Any]:
    """
    PROMPT 2 — CONVERSION-OPTIMIZED PRODUCT DESCRIPTION (MVP CORE)
    Writes Amazon-style, high-converting product copy.
    """
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
2. Short opener (2–3 lines explaining who this is for and why it matters)
3. Benefit-driven bullet points (5–7 bullets)
   - Each bullet should connect a feature to a real buyer outcome
4. "Who this is for" section
5. "Who this is NOT for" section (builds trust)
6. Objection handling (answer top 3 buyer doubts clearly)
7. Social proof placeholder (DO NOT invent reviews)
8. Clear, simple call-to-action

STYLE RULES:
- No buzzwords
- No emojis
- No AI mention
- No marketing fluff
- Confident, direct, human tone
- Short sentences
- Easy to scan

Write as if this will be pasted directly into a Shopify or Amazon product page.

Product Clarity:
{clarity_text}

Original Product Information:
{product_info}
"""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an expert eCommerce copywriter who specializes in Amazon-style conversion writing."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.75
    )

    description = response.choices[0].message.content

    return {
        "description": description,
        "product_clarity": product_clarity
    }


def prompt3_product_audit(product_info: str, optimized_description: Dict[str, Any]) -> Dict[str, Any]:
    """
    PROMPT 3 — PRODUCT PAGE AUDIT (AUTHORITY BUILDER)
    Provides a short, blunt product page audit as a CRO expert.
    """
    description_text = optimized_description.get("description", "")
    
    prompt = f"""Act as a CRO expert.

Based on the original product information and the optimized description below, provide a short, blunt product page audit.

Output EXACTLY 5 bullet points covering:
1. What is unclear or confusing
2. What is missing that hurts conversion
3. What is weakening trust
4. What should be moved higher on the page
5. One high-impact improvement to test first

Tone:
- Honest
- Direct
- Professional
- No sugarcoating

Do NOT repeat the optimized copy.

Original Product Information:
{product_info}

Optimized Description:
{description_text}"""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a Conversion Rate Optimization (CRO) expert. Be direct and honest in your feedback."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5
    )
    
    audit = response.choices[0].message.content
    
    return {
        "audit": audit,
        "optimized_description": optimized_description
    }


def prompt4_ad_hooks_and_test(
    product_info: str,
    optimized_description: Dict[str, Any],
    audit: Dict[str, Any]
) -> Dict[str, Any]:
    """
    PROMPT 4 — AD HOOKS + A/B TEST IDEA
    Generates ad hooks and A/B test recommendations.
    """
    description_text = optimized_description.get("description", "")
    audit_text = audit.get("audit", "")
    
    prompt = f"""Using the optimized product description and audit insights below, generate the following:

SECTION A — Ad Hooks
- 5 short scroll-stopping hooks (1 line each)
- 3 ad angles:
  - Problem-aware
  - Desire-driven
  - Proof/credibility-based

SECTION B — A/B Test Recommendation
- ONE clear A/B test suggestion
- Explain WHY this test could increase conversion
- Keep explanation under 3 lines

Rules:
- No emojis
- No hype
- Write for Facebook / Instagram ads

Optimized Description:
{description_text}

Audit Insights:
{audit_text}

Original Product Information:
{product_info}"""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an expert in Facebook and Instagram ad copywriting and A/B testing."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.8
    )
    
    ad_hooks_and_test = response.choices[0].message.content
    
    return {
        "ad_hooks_and_test": ad_hooks_and_test,
        "audit": audit
    }

