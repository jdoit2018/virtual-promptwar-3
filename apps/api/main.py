"""
apps/api/main.py
FastAPI application entry point for the Carbon Footprint Awareness Platform.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.database import init_db
from routers import auth, baselines, challenges, goals, internal, logs, notifications, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup → yield → shutdown."""
    await init_db()
    yield


app = FastAPI(
    title="Carbon Footprint Platform API",
    description="Backend API for the Carbon Footprint Awareness Platform",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ─────────────────────────────────────────────────────
app.include_router(auth.router,          prefix="/api/auth",          tags=["Auth"])
app.include_router(users.router,         prefix="/api/users",         tags=["Users"])
app.include_router(baselines.router,     prefix="/api/baselines",     tags=["Baselines"])
app.include_router(logs.router,          prefix="/api/logs",          tags=["Logs"])
app.include_router(goals.router,         prefix="/api/goals",         tags=["Goals"])
app.include_router(challenges.router,    prefix="/api/challenges",    tags=["Challenges"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(internal.router,      prefix="/api/internal",      tags=["Internal"])


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "version": "0.1.0"}
