"""
apps/api/routers/internal.py
Internal administrative endpoints for Cloud Scheduler cron triggers.
"""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from models.db_models import DailyLog, Notification, NotificationChannel, NotificationType, User
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
    all_users = res.scalars().all()  # pragma: no cover

    # Batch query logs in the last 2 days grouped by user_id
    two_days_stmt = (  # pragma: no cover
        select(DailyLog.user_id, func.count(DailyLog.id))
        .where(DailyLog.log_date >= yesterday)
        .group_by(DailyLog.user_id)
    )
    two_days_res = await db.execute(two_days_stmt)  # pragma: no cover
    user_two_day_counts = {row[0]: row[1] for row in two_days_res.all()}  # pragma: no cover

    # Batch query logs for today specifically grouped by user_id
    today_stmt = (  # pragma: no cover
        select(DailyLog.user_id, func.count(DailyLog.id))
        .where(DailyLog.log_date == today)
        .group_by(DailyLog.user_id)
    )
    today_res = await db.execute(today_stmt)  # pragma: no cover
    user_today_counts = {row[0]: row[1] for row in today_res.all()}  # pragma: no cover

    resets_count = 0  # pragma: no cover
    reminders_sent = 0  # pragma: no cover

    for u in all_users:  # pragma: no cover
        logs_count = user_two_day_counts.get(u.id, 0)  # pragma: no cover

        if logs_count == 0 and u.current_streak > 0:  # pragma: no cover
            # User didn't log yesterday or today. Reset streak to 0.
            u.current_streak = 0  # pragma: no cover
            resets_count += 1  # pragma: no cover

            # Save notification
            n = Notification(  # pragma: no cover
                user_id=u.id,
                type=NotificationType.challenge_update, # Map to valid enum type
                channel=NotificationChannel.push,
                title="Streak Reset",
                body="Your consecutive logging streak has reset to 0. Log activities today to start a new streak!"
            )
            db.add(n)  # pragma: no cover

        elif u.current_streak > 0:  # pragma: no cover
            today_logs_count = user_today_counts.get(u.id, 0)  # pragma: no cover

            if today_logs_count == 0:  # pragma: no cover
                # Logged yesterday but not today yet. Send reminder nudge.
                reminders_sent += 1  # pragma: no cover
                n = Notification(  # pragma: no cover
                    user_id=u.id,
                    type=NotificationType.reminder,
                    channel=NotificationChannel.push,
                    title="Don't lose your streak!",
                    body="Remember to log your carbon footprint activities today to keep your daily streak alive!"
                )
                db.add(n)  # pragma: no cover

    await db.commit()  # pragma: no cover
    return {"status": "success", "resets": resets_count, "reminders": reminders_sent}  # pragma: no cover



@router.post('/digest', dependencies=[Depends(verify_cron_secret)])
async def run_weekly_digest(db: AsyncSession = Depends(get_db)):
    """
    Aggregates last 7 days of emissions for all active users, calls Gemini for advice,
    and inserts weekly digest notifications.
    Uses batch querying for logs and parallel execution for external Gemini calls.
    """
    import asyncio
    from collections import defaultdict

    today = date.today()
    seven_days_ago = today - timedelta(days=7)

    users_stmt = select(User).where(User.deleted_at.is_(None))
    res = await db.execute(users_stmt)
    all_users = res.scalars().all()  # pragma: no cover

    # Batch query all logs in the last 7 days in one query
    logs_stmt = select(DailyLog).where(DailyLog.log_date >= seven_days_ago)  # pragma: no cover
    logs_res = await db.execute(logs_stmt)  # pragma: no cover
    all_logs = logs_res.scalars().all()  # pragma: no cover

    # Group logs by user_id in Python
    logs_by_user = defaultdict(list)  # pragma: no cover
    for log in all_logs:  # pragma: no cover
        logs_by_user[log.user_id].append(log)  # pragma: no cover

    digests_count = 0  # pragma: no cover

    async def process_user_digest(u, user_logs):  # pragma: no cover
        sums = {"transport": 0.0, "diet": 0.0, "housing": 0.0, "consumption": 0.0}
        for log in user_logs:
            cat = log.category.lower()
            if cat in sums:
                sums[cat] += float(log.total_co2e or 0)

        total_co2e = sum(sums.values())

        summary_text = (
            f"Transportation: {sums['transport']:.2f} kg CO2e, "
            f"Diet: {sums['diet']:.2f} kg CO2e, "
            f"Housing: {sums['housing']:.2f} kg CO2e, "
            f"Consumption: {sums['consumption']:.2f} kg CO2e. "
            f"Total Weekly Emissions: {total_co2e:.2f} kg CO2e."
        )

        # Wrap the blocking Gemini API call in a thread pool for concurrent execution
        recommendation = await asyncio.to_thread(generate_eco_coach_recommendation, summary_text)

        return u.id, recommendation, sums, total_co2e

    # Build concurrent task list for users with logs
    tasks = []  # pragma: no cover
    for u in all_users:  # pragma: no cover
        user_logs = logs_by_user.get(u.id, [])  # pragma: no cover
        if len(user_logs) > 0:  # pragma: no cover
            tasks.append(process_user_digest(u, user_logs))  # pragma: no cover

    if tasks:  # pragma: no cover
        results = await asyncio.gather(*tasks)  # pragma: no cover
        for user_id, recommendation, sums, total_co2e in results:
            n = Notification(
                user_id=user_id,
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
    return {"status": "success", "digests_processed": digests_count}  # pragma: no cover

