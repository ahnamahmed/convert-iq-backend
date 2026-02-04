import stripe
from fastapi import APIRouter, Depends
from app.config import get_settings
from app.auth.deps import get_current_user
from app.model.user import User

settings = get_settings()
stripe.api_key = settings.stripe_secret_key

router = APIRouter(prefix="/billing", tags=["Billing"])


@router.post("/checkout")
def create_checkout_session(
    current_user: User = Depends(get_current_user),
):
    session = stripe.checkout.Session.create(
        mode="subscription",
        customer=current_user.stripe_customer_id,
        line_items=[
            {
                "price": "price_starter_monthly",  # or Growth
                "quantity": 1,
            }
        ],
        success_url=f"{settings.frontend_url}/success",
        cancel_url=f"{settings.frontend_url}/billing",
        metadata={
            "user_id": str(current_user.id),
        },
    )

    return {"url": session.url}