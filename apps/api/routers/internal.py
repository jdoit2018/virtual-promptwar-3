"""
apps/api/routers/internal.py
Internal administrative endpoints for Cloud Scheduler cron triggers.
"""

from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.config import settings
from models.db_models import User, DailyLog, Notification, NotificationType, NotificationChannel
from services.gemini_service import generate_eco_coach_recommendation

router = APIRouter()

def verify_cron_secret(authorization: str = Header(None)):
    """Verifies that the incoming request is authorized with the internal CRON_SECRET."""
    expected = f"Bearer {settings.CRON_SECRET}"
    if not authorization or authorization != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing cron secret authorization header"
        )

@router.post('/streak-check', dependencies=[Depends(verify_cron_secret)])
async def run_streak_check(db: AsyncSession = Depends(get_db)):
    """
    Checks all users' streaks. Resets streak to 0 if no logs are found for today or yesterday.
    Sends reminders if logs are missing for today but existed yesterday.
    """
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    # Fetch all active users
    users_stmt = select(User).where(User.deleted_at.is_(None))
    res = await db.execute(users_stmt)
    all_users = res.scalars().all()
    
    resets_count = 0
    reminders_sent = 0
    
    for u in all_users:
        # Check logs count for today and yesterday
        logs_stmt = select(func.count(DailyLog.id)).where(
            and_(
                DailyLog.user_id == u.id,
                DailyLog.log_date >= yesterday
            )
        )
        logs_count_res = await db.execute(logs_stmt)
        logs_count = logs_count_res.scalar() or 0
        
        if logs_count == 0 and u.current_streak > 0:
            # User didn't log yesterday or today. Reset streak to 0.
            u.current_streak = 0
            resets_count += 1
            
            # Save notification
            n = Notification(
                user_id=u.id,
                type=NotificationType.challenge_update, # Map to valid enum type
                channel=NotificationChannel.push,
                title="Streak Reset",
                body="Your consecutive logging streak has reset to 0. Log activities today to start a new streak!"
            )
            db.add(n)
        
        elif u.current_streak > 0:
            # Check if they logged today specifically
            today_logs_stmt = select(func.count(DailyLog.id)).where(
                and_(
                    DailyLog.user_id == u.id,
                    DailyLog.log_date == today
                )
            )
            today_logs_count_res = await db.execute(today_logs_stmt)
            today_logs_count = today_logs_count_res.scalar() or 0
            
            if today_logs_count == 0:
                # Logged yesterday but not today yet. Send reminder nudge.
                reminders_sent += 1
                n = Notification(
                    user_id=u.id,
                    type=NotificationType.reminder,
                    channel=NotificationChannel.push,
                    title="Don't lose your streak!",
                    body="Remember to log your carbon footprint activities today to keep your daily streak alive!"
                )
                db.add(n)
                
    await db.commit()
    return {"status": "success", "resets": resets_count, "reminders": reminders_sent}


@router.post('/digest', dependencies=[Depends(verify_cron_secret)])
async def run_weekly_digest(db: AsyncSession = Depends(get_db)):
    """
    Aggregates last 7 days of emissions for all active users, calls Gemini for advice,
    and inserts weekly digest notifications.
    """
    today = date.today()
    seven_days_ago = today - timedelta(days=7)
    
    users_stmt = select(User).where(User.deleted_at.is_(None))
    res = await db.execute(users_stmt)
    all_users = res.scalars().all()
    
    digests_count = 0
    
    for u in all_users:
        # Get logs for last 7 days
        logs_stmt = select(DailyLog).where(
            and_(
                DailyLog.user_id == u.id,
                DailyLog.log_date >= seven_days_ago
            )
        )
        logs_res = await db.execute(logs_stmt)
        user_logs = logs_res.scalars().all()
        
        if len(user_logs) > 0:
            # Aggregate category sums
            sums = {"transport": 0.0, "diet": 0.0, "housing": 0.0, "consumption": 0.0}
            for log in user_logs:
                cat = log.category.lower()
                if cat in sums:
                    sums[cat] += float(log.total_co2e or 0)
            
            total_co2e = sum(sums.values())
            
            # Format text for Gemini input
            summary_text = (
                f"Transportation: {sums['transport']:.2f} kg CO2e, "
                f"Diet: {sums['diet']:.2f} kg CO2e, "
                f"Housing: {sums['housing']:.2f} kg CO2e, "
                f"Consumption: {sums['consumption']:.2f} kg CO2e. "
                f"Total Weekly Emissions: {total_co2e:.2f} kg CO2e."
            )
            
            recommendation = generate_eco_coach_recommendation(summary_text)
            
            n = Notification(
                user_id=u.id,
                type=NotificationType.weekly_digest,
                channel=NotificationChannel.push,
                title="Your Weekly Carbon Digest",
                body=recommendation,
                notification_metadata={
                    "weekly_totals": sums,
                    "total_co2e": total_co2e
                }
            )
            db.add(n)
            digests_count += 1
            
    await db.commit()
    return {"status": "success", "digests_processed": digests_count}
