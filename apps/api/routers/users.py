"""
apps/api/routers/users.py
User profile management router.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from core.database import get_db
from core.firebase import get_current_user
from models.db_models import User, Baseline, DailyLog, UserChallenge
from models.schemas import UserResponse

router = APIRouter()


@router.get('/me', response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns the authenticated caller's user record.
    """
    return current_user


@router.post('/me/export')
async def export_user_data(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Compiles all user baseline, logs, and challenges history into a JSON archive (GDPR compliance).
    """
    # 1. Fetch baselines
    stmt_baselines = select(Baseline).where(Baseline.user_id == current_user.id)
    res_baselines = await db.execute(stmt_baselines)
    baselines = res_baselines.scalars().all()

    # 2. Fetch daily logs
    stmt_logs = select(DailyLog).where(DailyLog.user_id == current_user.id)
    res_logs = await db.execute(stmt_logs)
    logs = res_logs.scalars().all()

    # 3. Fetch user challenges
    stmt_challenges = select(UserChallenge).where(UserChallenge.user_id == current_user.id)
    res_challenges = await db.execute(stmt_challenges)
    challenges = res_challenges.scalars().all()

    # Compile the archive package
    archive = {
        "profile": {
            "id": str(current_user.id),
            "email": current_user.email,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "username": current_user.username,
            "region_code": current_user.region_code,
            "current_streak": current_user.current_streak,
            "highest_streak": current_user.highest_streak,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None
        },
        "baselines": [
            {
                "id": str(b.id),
                "total_co2e": float(b.total_co2e),
                "housing_co2e": float(b.housing_co2e) if b.housing_co2e is not None else None,
                "transport_co2e": float(b.transport_co2e) if b.transport_co2e is not None else None,
                "diet_co2e": float(b.diet_co2e) if b.diet_co2e is not None else None,
                "consumption_co2e": float(b.consumption_co2e) if b.consumption_co2e is not None else None,
                "quiz_responses": b.quiz_responses,
                "is_current": b.is_current,
                "created_at": b.created_at.isoformat() if b.created_at else None
            }
            for b in baselines
        ],
        "daily_logs": [
            {
                "id": str(l.id),
                "log_date": l.log_date.isoformat() if l.log_date else None,
                "category": l.category,
                "activity_type": l.activity_type,
                "quantity": float(l.quantity),
                "total_co2e": float(l.total_co2e) if l.total_co2e is not None else None,
                "is_estimated": l.is_estimated,
                "metadata": l.log_metadata,
                "created_at": l.created_at.isoformat() if l.created_at else None
            }
            for l in logs
        ],
        "user_challenges": [
            {
                "id": str(uc.id),
                "challenge_id": str(uc.challenge_id),
                "status": uc.status,
                "progress": uc.progress,
                "started_at": uc.started_at.isoformat() if uc.started_at else None,
                "completed_at": uc.completed_at.isoformat() if uc.completed_at else None,
                "failed_at": uc.failed_at.isoformat() if uc.failed_at else None
            }
            for uc in challenges
        ]
    }

    return archive


@router.delete('/me')
async def delete_user(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft deletes the user record (setting deleted_at timestamp) as per GDPR right to erasure.
    """
    current_user.deleted_at = datetime.utcnow()
    await db.commit()
    return {"status": "success", "message": "User soft-deleted successfully"}
