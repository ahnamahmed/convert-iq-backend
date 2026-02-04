from app.model.subscription import Subscription
from datetime import datetime


def upsert_subscription(db, user_id: int, stripe_sub):
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

    sub.price_id = price["id"]
    sub.status = stripe_sub["status"]
    sub.current_period_start = datetime.utcfromtimestamp(
        stripe_sub["current_period_start"]
    )
    sub.current_period_end = datetime.utcfromtimestamp(
        stripe_sub["current_period_end"]
    )
    sub.cancel_at_period_end = stripe_sub["cancel_at_period_end"]

    db.commit()