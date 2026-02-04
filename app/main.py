from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

# ⚙️ CONFIG
from app.config import get_settings

# 🗄 DATABASE
from app.db import engine, Base

# 🔐 AUTH
from app.auth.deps import get_current_user
from app.model.user import User

# 🔁 ROUTERS
from app.auth.routes import router as auth_router
from app.routes.users import router as users_router
from app.webhooks.stripe import router as stripe_webhook_router

# 🧠 CORE LOGIC
from app.chain import runPromptChain
from app.rate_limiter import check_rate_limit

# 📦 SCHEMAS
from app.models import ProductInfoRequest, Prompt1OnlyRequest

settings = get_settings()

# =========================
# LIFESPAN (replaces on_event)
# =========================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 🔵 STARTUP
    Base.metadata.create_all(bind=engine)
    print("🚀 API started")

    yield

    # 🔴 SHUTDOWN
    print("🛑 API shutdown")


# =========================
# APP INIT
# =========================
app = FastAPI(
    title="Convert IQ - Advanced CRO optimization",
    description="Generate high-converting product page using url",
    version="1.0.0",
    lifespan=lifespan,
)

# =========================
# CORS
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# ROUTERS
# =========================
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(stripe_webhook_router)

# =========================
# HEALTH / ROOT
# =========================
@app.get("/")
async def root():
    return {
        "message": "Convert IQ API",
        "version": "1.0.0",
        "auth": "JWT",
        "endpoints": {
            "login": "/auth/login",
            "register": "/auth/register",
            "me": "/users/me",
            "generate_full": "/api/generate",
            "generate_prompt1_only": "/api/generate/prompt1",
            "stripe_webhook": "/webhooks/stripe",
        },
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}

# =========================
# FULL CHAIN (AUTH REQUIRED)
# =========================
@app.post("/api/generate")
async def generate_full_chain(
    request: ProductInfoRequest,
    current_user: User = Depends(get_current_user),
):
    user_id = str(current_user.id)

    allowed, remaining = check_rate_limit(user_id)
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "remaining_requests": 0,
                "reset_in_seconds": settings.rate_limit_window_seconds,
            },
        )

    try:
        result = await runPromptChain(
            user_id=user_id,
            product_info=request.product_info,
            run_prompt1=True,
            run_prompt2=True,
            run_prompt3=True,
            run_prompt4=True,
        )

        result["rate_limit"] = {"remaining_requests": remaining}
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =========================
# PROMPT 1 ONLY (AUTH REQUIRED)
# =========================
@app.post("/api/generate/prompt1")
async def generate_prompt1_only(
    request: Prompt1OnlyRequest,
    current_user: User = Depends(get_current_user),
):
    user_id = str(current_user.id)

    allowed, remaining = check_rate_limit(user_id)
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "remaining_requests": 0,
                "reset_in_seconds": settings.rate_limit_window_seconds,
            },
        )

    try:
        result = await runPromptChain(
            user_id=user_id,
            product_info=request.product_info,
            run_prompt1=True,
            run_prompt2=False,
            run_prompt3=False,
            run_prompt4=False,
        )

        result["rate_limit"] = {"remaining_requests": remaining}
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))