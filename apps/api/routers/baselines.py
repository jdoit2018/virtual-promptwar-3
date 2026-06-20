"""
apps/api/routers/baselines.py
Baseline footprint endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.database import get_db
from core.firebase import get_current_user
from models.db_models import Baseline, User
from models.schemas import BaselineCreate, BaselineResponse
from services.baseline_service import calculate_baseline_values

router = APIRouter()


@router.post('', response_model=BaselineResponse)
async def create_baseline(
    payload: BaselineCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Submits onboarding quiz answers, calculates baseline carbon footprint,
    and stores it as the active baseline for the user (automatically retiring the old one).
    """
    # Calculate baseline values
    results = calculate_baseline_values(payload.quiz_responses)

    # Create new baseline record
    baseline = Baseline(
        user_id=current_user.id,
        total_co2e=results["total_co2e"],
        housing_co2e=results["housing_co2e"],
        transport_co2e=results["transport_co2e"],
        diet_co2e=results["diet_co2e"],
        consumption_co2e=results["consumption_co2e"],
        quiz_responses=payload.quiz_responses.model_dump(),
        is_current=True
    )
    db.add(baseline)
    await db.commit()
    await db.refresh(baseline)

    return baseline


@router.get('/current', response_model=BaselineResponse)
async def get_current_baseline(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns the user's currently active baseline, or 404 if they haven't completed onboarding.
    """
    stmt = select(Baseline).where(
        Baseline.user_id == current_user.id,
        Baseline.is_current == True
    )
    result = await db.execute(stmt)
    baseline = result.scalars().first()

    if not baseline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active baseline found. Please complete the onboarding quiz."
        )

    return baseline
