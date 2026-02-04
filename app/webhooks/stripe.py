import stripe
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException, status

from app.config import get_settings
from app.db import SessionLocal
from app.model.user import User
from app.model.subscription import Subscription

settings = get_settings()

stripe.api_key = settings.stripe_secret_key

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe signature",
        )

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=settings.stripe_webhook_secret,
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Stripe signature",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook error",
        )

    db = SessionLocal()

    try:
        # ----------------------------
        # Checkout completed (new sub)
        # ----------------------------
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]

            if session["mode"] != "subscription":
                return {"status": "ignored"}

            user = (
                db.query(User)
                .filter(User.stripe_customer_id == session["customer"])
                .first()
            )

            if not user:
                return {"status": "user_not_found"}

            stripe_sub = stripe.Subscription.retrieve(
                session["subscription"]
            )

            _upsert_subscription(db, user.id, stripe_sub)

        # ------------------------------------
        # Subscription updated / renewed
        # ------------------------------------
        elif event["type"] == "customer.subscription.updated":
            stripe_sub = event["data"]["object"]

            user = (
                db.query(User)
                .filter(User.stripe_customer_id == stripe_sub["customer"])
                .first()
            )

            if user:
                _upsert_subscription(db, user.id, stripe_sub)

        # ----------------------------
        # Subscription cancelled
        # ----------------------------
        elif event["type"] == "customer.subscription.deleted":
            stripe_sub = event["data"]["object"]

            sub = (
                db.query(Subscription)
                .filter(
                    Subscription.stripe_subscription_id == stripe_sub["id"]
                )
                .first()
            )

            if sub:
                sub.status = "canceled"
                db.commit()

        # ----------------------------
        # Payment failed (optional)
        # ----------------------------
        elif event["type"] == "invoice.payment_failed":
            invoice = event["data"]["object"]
            stripe_sub_id = invoice.get("subscription")

            if stripe_sub_id:
                sub = (
                    db.query(Subscription)
                    .filter(
                        Subscription.stripe_subscription_id
                        == stripe_sub_id
                    )
                    .first()
                )

                if sub:
                    sub.status = "past_due"
                    db.commit()

    finally:
        db.close()

    return {"status": "success"}


# ------------------------------------------------
# Helper: create or update subscription record
# ------------------------------------------------
def _upsert_subscription(db, user_id: int, stripe_sub):
    price = stripe_sub["items"]["data"][0]["price"]

    sub = (
        db.query(Subscription)
        .filter(
            Subscription.stripe_subscription_id == stripe_sub["id"]
        )
        .first()
    )

    if not sub:
        sub = Subscription(
            user_id=user_id,
            stripe_customer_id=stripe_sub["customer"],
            stripe_subscription_id=stripe_sub["id"],
        )
        db.add(sub)

    sub.stripe.price_id = price["id"]
    sub.status = stripe_sub["status"]
    sub.current_period_start = datetime.utcfromtimestamp(
        stripe_sub["current_period_start"]
    )
    sub.current_period_end = datetime.utcfromtimestamp(
        stripe_sub["current_period_end"]
    )
    sub.cancel_at_period_end = stripe_sub["cancel_at_period_end"]

    db.commit()