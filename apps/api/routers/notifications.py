"""
apps/api/routers/notifications.py
Notifications and FCM device token registration.
"""

from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from core.database import get_db
from core.firebase import get_current_user
from models.db_models import User, Notification, NotificationType, NotificationChannel
from models.schemas import FCMTokenRegister, NotificationResponse

router = APIRouter()


@router.get('', response_model=List[NotificationResponse])
async def get_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Fetches notifications for the authenticated user, ordered by creation time descending.
    """
    stmt = select(Notification).where(Notification.user_id == current_user.id).order_by(Notification.created_at.desc())
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.post('/register-token', status_code=status.HTTP_201_CREATED)
async def register_fcm_token(
    payload: FCMTokenRegister,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Registers or updates the user's FCM device token.
    Stores the token in the metadata field of a specific registration notification entry.
    """
    # Check if there is an existing token registration row for this user
    stmt = select(Notification).where(
        Notification.user_id == current_user.id,
        Notification.type == NotificationType.reminder,
        Notification.channel == NotificationChannel.push,
        Notification.title == "FCM Token Registration"
    )
    res = await db.execute(stmt)
    existing = res.scalars().first()

    if existing:
        existing.metadata = {"fcm_token": payload.token}
        existing.sent_at = datetime.utcnow()
    else:
        new_reg = Notification(
            user_id=current_user.id,
            type=NotificationType.reminder,
            channel=NotificationChannel.push,
            title="FCM Token Registration",
            body="Device token successfully registered",
            sent_at=datetime.utcnow(),
            metadata={"fcm_token": payload.token}
        )
        db.add(new_reg)

    await db.commit()
    return {"status": "success", "message": "FCM token registered successfully"}
