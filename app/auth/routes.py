from datetime import timedelta
import stripe

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db import get_db
from app.model.user import User
from app.schemas.user import UserCreate
from app.auth.jwt import (
    hash_password,
    verify_password,
    create_access_token,
)
from app.config import get_settings

settings = get_settings()
stripe.api_key = settings.stripe_secret_key

router = APIRouter(prefix="/auth", tags=["Auth"])


# ====================
# Register (JSON)
# ====================
@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    user: UserCreate,
    db: Session = Depends(get_db),
):
    # 1️⃣ Check existing user
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists",
        )

    # 2️⃣ Create Stripe customer safely
    stripe_customer_id = None
    try:
        customer = stripe.Customer.create(
            email=user.email,
            metadata={"source": "auth_register"},
        )
        stripe_customer_id = customer.id
    except Exception as e:
        # IMPORTANT: Stripe must NOT block signup
        print("Stripe customer creation failed:", str(e))

    # 3️⃣ Create user
    new_user = User(
        email=user.email,
        hashed_password=hash_password(user.password),
        stripe_customer_id=stripe_customer_id,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User created successfully"}


# ====================
# Login (OAuth2 Password Flow)
# ====================
@router.post("/login", status_code=status.HTTP_200_OK)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    # OAuth2 uses "username" → treat as email
    user = db.query(User).filter(
        User.email == form_data.username
    ).first()

    if not user or not verify_password(
        form_data.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(
            minutes=settings.access_token_expire_minutes
        ),
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }