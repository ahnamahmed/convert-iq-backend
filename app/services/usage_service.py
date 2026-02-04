from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.model.usage import Usage


# ------------------------------------------------
# Get or create usage row for a billing period
# ------------------------------------------------
def get_or_create_usage(
    db: Session,
    user_id: int,
    period_start,
    period_end,
) -> Usage:
    usage = (
        db.query(Usage)
        .filter(
            Usage.user_id == user_id,
            Usage.period_start == period_start,
            Usage.period_end == period_end,
        )
        .first()
    )

    if usage:
        return usage

    usage = Usage(
        user_id=user_id,
        optimizations_used=0,
        period_start=period_start,
        period_end=period_end,
    )

    db.add(usage)
    db.commit()
    db.refresh(usage)

    return usage


# ------------------------------------------------
# Read usage (used count only)
# Used by /subscription/me
# ------------------------------------------------
def get_usage_for_period(
    db: Session,
    user_id: int,
    period_start,
    period_end,
):
    usage = (
        db.query(Usage)
        .filter(
            Usage.user_id == user_id,
            Usage.period_start == period_start,
            Usage.period_end == period_end,
        )
        .first()
    )

    if not usage:
        return {"used": 0}

    return {"used": usage.optimizations_used}


# ------------------------------------------------
# Increment usage (called when optimization runs)
# ------------------------------------------------
def increment_optimization_usage(
    db: Session,
    user_id: int,
    plan: dict,
    period_start,
    period_end,
):
    usage = get_or_create_usage(
        db=db,
        user_id=user_id,
        period_start=period_start,
        period_end=period_end,
    )

    limit = plan["limits"]["optimizations_per_period"]

    # Unlimited plan
    if limit != "unlimited" and usage.optimizations_used >= limit:
        raise HTTPException(
            status_code=403,
            detail="Optimization limit reached. Upgrade your plan.",
        )

    usage.optimizations_used += 1
    db.commit()
