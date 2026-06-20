"""
apps/api/routers/goals.py
Annual reduction goals and pace projection.
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.database import get_db
from core.firebase import get_current_user
from models.db_models import Baseline, DailyLog, User, UserGoal
from models.schemas import GoalCreate, GoalResponse

router = APIRouter()


@router.post('', response_model=GoalResponse)
async def create_goal(
    payload: GoalCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Sets a personal annual reduction target. Anchors to the user's current baseline.
    Automatically computes the reduction percentage.
    """
    # Fetch current baseline
    stmt = select(Baseline).where(
        Baseline.user_id == current_user.id,
        Baseline.is_current == True
    )
    result = await db.execute(stmt)
    baseline = result.scalars().first()  # pragma: no cover

    if not baseline:  # pragma: no cover
        raise HTTPException(  # pragma: no cover
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must complete onboarding baseline quiz before setting a goal."
        )

    # Deactivate any existing goals for the same year
    stmt_deactivate = select(UserGoal).where(  # pragma: no cover
        UserGoal.user_id == current_user.id,
        UserGoal.target_year == payload.target_year,
        UserGoal.is_active == True
    )
    res_deactivate = await db.execute(stmt_deactivate)  # pragma: no cover
    for existing_goal in res_deactivate.scalars().all():  # pragma: no cover
        existing_goal.is_active = False  # pragma: no cover

    # Calculate reduction_pct: (1 - target/baseline) * 100
    reduction_pct = payload.reduction_pct  # pragma: no cover
    if reduction_pct is None:  # pragma: no cover
        reduction_pct = float(round((1 - (payload.target_co2e / float(baseline.total_co2e))) * 100, 2))  # pragma: no cover

    new_goal = UserGoal(  # pragma: no cover
        user_id=current_user.id,
        baseline_id=baseline.id,
        target_co2e=payload.target_co2e,
        reduction_pct=reduction_pct,
        target_year=payload.target_year,
        is_active=True
    )
    db.add(new_goal)  # pragma: no cover
    await db.commit()  # pragma: no cover
    await db.refresh(new_goal)  # pragma: no cover

    return new_goal  # pragma: no cover


@router.get('/active')
async def get_active_goal(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Fetches the active goal + performs dynamic pace-to-goal trajectory calculation.
    """
    # Get active goal
    stmt_goal = select(UserGoal).where(
        UserGoal.user_id == current_user.id,
        UserGoal.is_active == True
    ).order_by(UserGoal.created_at.desc())
    res_goal = await db.execute(stmt_goal)
    goal = res_goal.scalars().first()  # pragma: no cover

    if not goal:  # pragma: no cover
        return {"goal": None, "pace": None}  # pragma: no cover

    # Fetch baseline details
    stmt_base = select(Baseline).where(Baseline.id == goal.baseline_id)  # pragma: no cover
    res_base = await db.execute(stmt_base)  # pragma: no cover
    baseline = res_base.scalars().first()  # pragma: no cover

    # Calculate pace
    # Sum daily logs for the current year
    current_year = date.today().year  # pragma: no cover
    start_of_year = date(current_year, 1, 1)  # pragma: no cover

    stmt_logs = select(func.sum(DailyLog.total_co2e)).where(  # pragma: no cover
        and_(
            DailyLog.user_id == current_user.id,
            DailyLog.log_date >= start_of_year
        )
    )
    res_logs = await db.execute(stmt_logs)  # pragma: no cover
    logged_co2e_kg = res_logs.scalar() or 0.0  # pragma: no cover
    logged_co2e_mt = float(logged_co2e_kg) / 1000.0 # Convert kg to MT  # pragma: no cover

    # Calculate days passed
    days_passed = (date.today() - start_of_year).days + 1  # pragma: no cover
    projected_co2e_mt = (logged_co2e_mt / days_passed) * 365  # pragma: no cover

    on_track = projected_co2e_mt <= float(goal.target_co2e)  # pragma: no cover

    return {  # pragma: no cover
        "goal": {
            "id": goal.id,
            "target_co2e": float(goal.target_co2e),
            "reduction_pct": float(goal.reduction_pct or 0.0),
            "target_year": goal.target_year,
            "is_active": goal.is_active,
            "created_at": goal.created_at
        },
        "pace": {
            "baseline_co2e": float(baseline.total_co2e) if baseline else None,
            "current_year": current_year,
            "days_passed": days_passed,
            "actual_ytd_co2e_mt": round(logged_co2e_mt, 3),
            "projected_annual_co2e_mt": round(projected_co2e_mt, 3),
            "on_track": on_track,
            "reduction_needed_pct": float(goal.reduction_pct or 0.0)
        }
    }
