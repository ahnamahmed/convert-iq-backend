from pydantic import BaseModel, Field
from typing import Optional, List


# =========================
# Main request (FULL CHAIN)
# =========================
class ProductInfoRequest(BaseModel):
    product_info: str = Field(
        ...,
        description="Product URL or raw product details"
    )
    user_id: Optional[str] = Field(
        None,
        description="Optional user identifier (can also be sent via header)"
    )


# =========================
# Prompt 1 only
# =========================
class Prompt1OnlyRequest(BaseModel):
    product_info: str = Field(
        ...,
        description="Product URL or raw product details"
    )
    user_id: Optional[str] = Field(
        None,
        description="Optional user identifier"
    )


# =========================
# Error responses (optional)
# =========================
class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


class RateLimitResponse(BaseModel):
    error: str = "Rate limit exceeded"
    remaining_requests: int
    reset_in_seconds: int