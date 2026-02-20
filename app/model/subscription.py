from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Boolean,
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)

    # 🔗 Relations
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 🔐 Stripe identifiers
    stripe_subscription_id = Column(
        String, unique=True, index=True, nullable=False
    )
    stripe_price_id = Column(String, nullable=False)
    stripe_customer_id = Column(String, nullable=False)

    # 📦 Subscription state
    status = Column(String, nullable=False)
    # active | trialing | canceled | incomplete | past_due

    # ⏱ Billing cycle
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end = Column(Boolean, default=False)

    # 🕒 Metadata
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # 🔁 ORM relation
    user = relationship("User", back_populates="subscriptions")