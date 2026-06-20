"""
apps/api/services/user_service.py
Service for user upsert and profile management.
"""


from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models.db_models import AuthProviderType, User


async def sync_firebase_user(db: AsyncSession, token_claims: dict) -> User:
    """
    Syncs Firebase user claims with the PostgreSQL users table.
    Upserts the user record.
    """
    uid = token_claims.get("uid")
    email = token_claims.get("email")
    name = token_claims.get("name", "")

    # Split name into first/last name
    first_name = None
    last_name = None
    if name:
        parts = name.split(" ", 1)
        first_name = parts[0]
        if len(parts) > 1:
            last_name = parts[1]

    # Map firebase auth provider
    firebase_meta = token_claims.get("firebase", {})
    provider_id = firebase_meta.get("sign_in_provider", "email")

    if "google" in provider_id:
        auth_provider = AuthProviderType.google
    elif "apple" in provider_id:
        auth_provider = AuthProviderType.apple
    else:
        auth_provider = AuthProviderType.email

    # Check if user already exists
    stmt = select(User).where(User.provider_user_id == uid)
    res = await db.execute(stmt)
    user = res.scalars().first()

    if not user:
        # Check by email as fallback to avoid duplicate emails
        stmt_email = select(User).where(User.email == email)
        res_email = await db.execute(stmt_email)
        user = res_email.scalars().first()

    if user:
        # Update user fields
        user.email = email
        user.provider_user_id = uid
        user.auth_provider = auth_provider
        user.deleted_at = None  # Restore if soft-deleted
        if not user.first_name:
            user.first_name = first_name
        if not user.last_name:
            user.last_name = last_name
        # Set a username if not set and email is present
        if not user.username and email:
            user.username = email.split("@")[0]
    else:
        # Create new user
        username = email.split("@")[0] if email else f"user_{uid[:8]}"
        user = User(
            email=email,
            provider_user_id=uid,
            auth_provider=auth_provider,
            first_name=first_name,
            last_name=last_name,
            username=username,
            region_code="GLOBAL",
            current_streak=0,
            highest_streak=0
        )
        db.add(user)

    await db.commit()
    await db.refresh(user)
    return user
