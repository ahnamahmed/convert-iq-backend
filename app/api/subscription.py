from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.db import get_db
from app.model.user import User
from app.model.subscription import Subscription
from app.auth.deps import get_current_user
from app.services.usage_service import get_usage_for_period
from app.core.plans import PLANS_BY_PRICE_ID

router = APIRouter(prefix="/subscription", tags=["Subscription"])

@router.get("/me")
def get_my_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1️⃣ Fetch latest active/trialing subscription
    subscription = (
        db.query(Subscription)
        .filter(
            Subscription.user_id == current_user.id,
            Subscription.status.in_(["active", "trialing", "past_due"]),
        )
        .order_by(Subscription.created_at.desc())
        .first()
    )

    # 2️⃣ No subscription → FREE user
    if not subscription:
        return {
            "has_subscription": False,
            "status": "free",
            "plan": {
                "id": "free",
                "name": "Free",
                "limits": {
                    "optimizations_per_period": 1
                },
            },
            "billing": None,
            "usage": {
                "used": 0,
                "remaining": 1,
                "resets_at": None,
            },
        }

    # 3️⃣ Resolve internal plan from Stripe price
    plan = PLANS_BY_PRICE_ID.get(subscription.stripe_price_id)

    if not plan:
        # Safety fallback — never break frontend
        plan = {
            "id": "unknown",
            "name": "Unknown",
            "limits": {
                "optimizations_per_period": 0
            },
        }

    # 4️⃣ Usage tracking (billing-period scoped)
    usage = get_usage_for_period(
        db=db,
        user_id=current_user.id,
        period_start=subscription.current_period_start,
        period_end=subscription.current_period_end,
    )

    used = usage.used
    limit = plan["limits"]["optimizations_per_period"]

    return {
        "has_subscription": True,
        "status": subscription.status,
        "plan": plan,
        "billing": {
            "renews_at": subscription.current_period_end,
            "cancel_at_period_end": subscription.cancel_at_period_end,
        },
        "usage": {
            "used": used,
            "remaining": max(limit - used, 0),
            "resets_at": subscription.current_period_end,
        },
    }
