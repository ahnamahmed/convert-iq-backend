from datetime import datetime, timezone
from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.plans import PLAN_CONFIG, FREE_PLAN
from app.model.subscription import Subscription


ACTIVE_STATUSES = {"active", "trialing"}


def get_active_subscriptions(db: Session, user_id: int) -> List[Subscription]:
    """Return all currently active subscriptions for a user."""
    return (
        db.query(Subscription)
        .filter(
            Subscription.user_id == user_id,
            Subscription.status.in_(ACTIVE_STATUSES),
            Subscription.current_period_end > datetime.now(timezone.utc),
        )
        .all()
    )


def resolve_user_plan(subscriptions: List[Subscription]) -> dict:
    """
    Resolve the effective plan for a user.
    Highest tier always wins.
    """
    if not subscriptions:
        return FREE_PLAN

    price_ids = {s.price_id for s in subscriptions}

    # Highest → lowest priority
    if "price_growth_monthly" in price_ids:
        return PLAN_CONFIG["price_growth_monthly"]

    if "price_starter_monthly" in price_ids:
        return PLAN_CONFIG["price_starter_monthly"]

    return FREE_PLAN


# ----------------------------
# Feature guards
# ----------------------------

def require_csv_access(plan: dict):
    if not plan["limits"].get("csv_export", False):
        raise HTTPException(
            status_code=403,
            detail="Upgrade your plan to export CSV",
        )


def require_cro_audit(plan: dict):
    if not plan["limits"].get("cro_audit", False):
        raise HTTPException(
            status_code=403,
            detail="Upgrade your plan to access CRO audits",
        )