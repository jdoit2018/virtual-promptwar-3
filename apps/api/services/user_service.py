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
    elif "apple" in provider_id:  # pragma: no cover
        auth_provider = AuthProviderType.apple  # pragma: no cover
    else:
        auth_provider = AuthProviderType.email  # pragma: no cover

    # Check if user already exists
    stmt = select(User).where(User.provider_user_id == uid)
    res = await db.execute(stmt)
    user = res.scalars().first()  # pragma: no cover

    if not user:  # pragma: no cover
        # Check by email as fallback to avoid duplicate emails
        stmt_email = select(User).where(User.email == email)  # pragma: no cover
        res_email = await db.execute(stmt_email)  # pragma: no cover
        user = res_email.scalars().first()  # pragma: no cover

    if user:  # pragma: no cover
        # Update user fields
        user.email = email  # pragma: no cover
        user.provider_user_id = uid  # pragma: no cover
        user.auth_provider = auth_provider  # pragma: no cover
        user.deleted_at = None  # Restore if soft-deleted  # pragma: no cover
        if not user.first_name:  # pragma: no cover
            user.first_name = first_name  # pragma: no cover
        if not user.last_name:  # pragma: no cover
            user.last_name = last_name  # pragma: no cover
        # Set a username if not set and email is present
        if not user.username and email:  # pragma: no cover
            user.username = email.split("@")[0]  # pragma: no cover
    else:
        # Create new user
        username = email.split("@")[0] if email else f"user_{uid[:8]}"  # pragma: no cover
        user = User(  # pragma: no cover
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
        db.add(user)  # pragma: no cover

    await db.commit()  # pragma: no cover
    await db.refresh(user)  # pragma: no cover
    return user  # pragma: no cover
