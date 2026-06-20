"""
apps/api/core/database.py
Async SQLAlchemy engine and session factory wired to PostgreSQL via asyncpg.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from .config import settings

# Convert postgresql:// → postgresql+asyncpg:// for async driver
_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(
    _url,
    pool_size=10,
    max_overflow=20,
    echo=(settings.NODE_ENV == "development"),
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def init_db():
    """Called on app startup -- verifies DB connection (non-fatal in dev)."""
    try:
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        print("[OK] Database connection verified")
    except Exception as e:
        print(f"[WARN] Database not reachable: {e}")
        print("   -> API will start in degraded mode (DB-dependent routes will fail)")


async def get_db():
    """FastAPI dependency — yields an async DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
