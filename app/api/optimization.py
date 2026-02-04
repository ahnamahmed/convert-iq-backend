from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.auth.deps import get_current_user
from app.model.user import User
from app.services.subscription_service import (
    get_active_subscriptions,
    resolve_user_plan,
)
from app.services.usage_service import (
    get_current_usage,
    increment_usage,
)

router = APIRouter(prefix="/optimize", tags=["Optimization"])


@router.post("")
def run_optimization(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1️⃣ Resolve plan
    subs = get_active_subscriptions(db, current_user.id)
    plan = resolve_user_plan(subs)

    # 2️⃣ Check usage limits
    usage = get_current_usage(db, current_user.id)

    if not plan["limits"]["unlimited"]:
        if usage.optimizations_used >= plan["limits"]["optimizations"]:
            raise HTTPException(
                status_code=403,
                detail="Monthly optimization limit reached",
            )

    # 3️⃣ Run AI / business logic
    # 🔥 this is where OpenAI / Gemini / Claude goes
    result = {
        "optimized_text": "AI optimized content here"
    }

    # 4️⃣ Increment usage ONLY after success
    increment_usage(db, current_user.id)

    return {
        "result": result,
        "usage": {
            "used": usage.optimizations_used + 1,
            "limit": plan["limits"]["optimizations"],
        },
    }