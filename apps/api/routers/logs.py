"""
apps/api/routers/logs.py
Daily emission logging endpoints.
"""

from datetime import date, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from core.database import get_db
from core.firebase import get_current_user
from models.db_models import User, DailyLog
from models.schemas import LogCreate, LogResponse, LogsSummaryWeekly

router = APIRouter()


async def recalculate_user_streak(db: AsyncSession, user_id: str) -> int:
    """
    Recalculates the consecutive daily logging streak for a user.
    A streak is the number of consecutive days ending either today or yesterday
    where the user has logged at least one activity.
    """
    today = date.today()
    current_date = today
    
    # Check today's logs
    stmt = select(DailyLog).where(
        and_(DailyLog.user_id == user_id, DailyLog.log_date == today)
    )
    res = await db.execute(stmt)
    has_today = res.scalars().first() is not None
    
    if not has_today:
        # Check yesterday's logs
        yesterday = today - timedelta(days=1)
        stmt = select(DailyLog).where(
            and_(DailyLog.user_id == user_id, DailyLog.log_date == yesterday)
        )
        res = await db.execute(stmt)
        has_yesterday = res.scalars().first() is not None
        if not has_yesterday:
            return 0
        current_date = yesterday
        
    streak = 0
    while True:
        stmt = select(DailyLog).where(
            and_(DailyLog.user_id == user_id, DailyLog.log_date == current_date)
        )
        res = await db.execute(stmt)
        if res.scalars().first() is None:
            break
        streak += 1
        current_date -= timedelta(days=1)
        
    return streak


@router.post('', response_model=LogResponse)
async def create_log_entry(
    payload: LogCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Creates or updates a daily log entry for a specific activity.
    The database trigger 'trg_calculate_co2e' automatically resolves
    the appropriate emission factor and calculates the total CO2e.
    """
    # Build upsert statement (ON CONFLICT DO UPDATE)
    insert_stmt = insert(DailyLog).values(
        user_id=current_user.id,
        log_date=payload.log_date,
        category=payload.category,
        activity_type=payload.activity_type,
        quantity=payload.quantity,
        log_metadata=payload.log_metadata,
        is_estimated=False
    )
    
    # On conflict, update quantity and log_metadata, reset total_co2e and emission_factor_id so trigger re-evaluates
    update_stmt = insert_stmt.on_conflict_do_update(
        constraint="unique_user_date_activity",
        set_={
            DailyLog.quantity: payload.quantity,
            DailyLog.log_metadata: payload.log_metadata,
            DailyLog.total_co2e: None,
            DailyLog.emission_factor_id: None
        }
    ).returning(DailyLog)

    try:
        res = await db.execute(update_stmt)
        log_row = res.scalars().first()
        
        # Streak Update Logic
        streak = await recalculate_user_streak(db, current_user.id)
        
        # Update user's streak in the database
        stmt_user = select(User).where(User.id == current_user.id)
        res_user = await db.execute(stmt_user)
        db_user = res_user.scalars().first()
        
        if db_user:
            db_user.current_streak = streak
            if streak > db_user.highest_streak:
                db_user.highest_streak = streak

        await db.commit()
        
        # Refresh to pull fields computed by the database trigger
        await db.refresh(log_row)
        return log_row
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to log activity: {str(e)}"
        )


@router.get('', response_model=List[LogResponse])
async def get_logs(
    log_date: Optional[date] = Query(None, description="Filter by specific date"),
    start_date: Optional[date] = Query(None, description="Start date of range"),
    end_date: Optional[date] = Query(None, description="End date of range"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Fetches the user's daily logs. If no parameters are passed, defaults to the last 30 days of logs.
    """
    stmt = select(DailyLog).where(DailyLog.user_id == current_user.id)
    
    if log_date:
        stmt = stmt.where(DailyLog.log_date == log_date)
    elif start_date and end_date:
        stmt = stmt.where(and_(DailyLog.log_date >= start_date, DailyLog.log_date <= end_date))
    else:
        # Default to last 30 days
        thirty_days_ago = date.today() - timedelta(days=30)
        stmt = stmt.where(DailyLog.log_date >= thirty_days_ago)

    stmt = stmt.order_by(DailyLog.log_date.desc(), DailyLog.created_at.desc())
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.get('/summary/weekly', response_model=LogsSummaryWeekly)
async def get_weekly_summary(
    end_date: Optional[date] = Query(None, description="End date for the weekly calculation. Defaults to today."),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns aggregated carbon emission totals for the 7 days ending at end_date,
    broken down by category.
    """
    ref_date = end_date or date.today()
    start_date = ref_date - timedelta(days=6)

    # Query sum of CO2e grouped by category
    stmt = (
        select(DailyLog.category, func.sum(DailyLog.total_co2e))
        .where(
            and_(
                DailyLog.user_id == current_user.id,
                DailyLog.log_date >= start_date,
                DailyLog.log_date <= ref_date
            )
        )
        .group_by(DailyLog.category)
    )

    res = await db.execute(stmt)
    rows = res.all()

    breakdown = {}
    total_co2e = 0.0

    for category, val in rows:
        co2e_val = float(val or 0.0)
        breakdown[category] = round(co2e_val, 3)
        total_co2e += co2e_val

    return LogsSummaryWeekly(
        week_start=start_date,
        week_end=ref_date,
        total_co2e=round(total_co2e, 3),
        breakdown=breakdown
    )
