"""
apps/api/routers/challenges.py
Eco-challenge catalog and user participation progression.
"""

from datetime import datetime

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from core.database import get_db
from core.firebase import get_current_user
from models.db_models import ChallengeStatus, EcoChallenge, User, UserChallenge
from models.schemas import EcoChallengeResponse, UserChallengeResponse

router = APIRouter()


@router.get('', response_model=list[EcoChallengeResponse])
async def list_challenges(
    db: AsyncSession = Depends(get_db)
):
    """
    Returns all active eco-challenges from the catalogue.
    """
    stmt = select(EcoChallenge).where(EcoChallenge.is_active == True)
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.post('/{id}/start', response_model=UserChallengeResponse)
async def start_challenge(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Enrolls the authenticated user in an eco-challenge.
    """
    # Verify challenge exists
    stmt_challenge = select(EcoChallenge).where(EcoChallenge.id == id, EcoChallenge.is_active == True)
    res_challenge = await db.execute(stmt_challenge)
    challenge = res_challenge.scalars().first()

    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Challenge not found or inactive."
        )

    # Check for existing enrollment
    stmt_enroll = select(UserChallenge).where(
        UserChallenge.user_id == current_user.id,
        UserChallenge.challenge_id == id
    )
    res_enroll = await db.execute(stmt_enroll)
    existing = res_enroll.scalars().first()

    if existing:
        if existing.status == ChallengeStatus.active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You are already participating in this challenge."
            )
        else:
            # Re-activate or return completed state
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"You have already finished this challenge with status: {existing.status.value}"
            )

    enrollment = UserChallenge(
        user_id=current_user.id,
        challenge_id=id,
        status=ChallengeStatus.active,
        progress=0,
        started_at=datetime.utcnow()
    )
    db.add(enrollment)
    await db.commit()

    # Load relationship for response
    stmt_load = select(UserChallenge).options(selectinload(UserChallenge.challenge)).where(UserChallenge.id == enrollment.id)
    res_load = await db.execute(stmt_load)

    return res_load.scalars().first()


@router.patch('/{id}/progress', response_model=UserChallengeResponse)
async def update_challenge_progress(
    id: str,
    progress: int = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Updates the user's progress for an active challenge.
    If the progress reaches or exceeds the target_value, the status is automatically
    marked as 'completed'.
    """
    stmt = (
        select(UserChallenge)
        .options(selectinload(UserChallenge.challenge))
        .where(
            UserChallenge.user_id == current_user.id,
            UserChallenge.challenge_id == id
        )
    )
    res = await db.execute(stmt)
    enrollment = res.scalars().first()

    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not enrolled in this challenge."
        )

    if enrollment.status != ChallengeStatus.active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot update progress. Challenge is already {enrollment.status.value}."
        )

    enrollment.progress = progress

    # Check if target is met
    if enrollment.progress >= enrollment.challenge.target_value:
        enrollment.status = ChallengeStatus.completed
        enrollment.completed_at = datetime.utcnow()

    await db.commit()
    await db.refresh(enrollment)
    return enrollment
