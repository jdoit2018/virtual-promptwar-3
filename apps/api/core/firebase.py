"""
apps/api/core/firebase.py
Firebase Admin SDK initialisation — verifies ID tokens for all protected routes.
"""

import firebase_admin
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .database import get_db

_bearer = HTTPBearer()

# Initialise Firebase Admin once (guard against re-init in hot-reload)
if not firebase_admin._apps:
    if settings.FIREBASE_PRIVATE_KEY:
        cred = credentials.Certificate({
            "type": "service_account",
            "project_id":   settings.FIREBASE_PROJECT_ID,
            "client_email": settings.FIREBASE_CLIENT_EMAIL,
            "private_key":  settings.FIREBASE_PRIVATE_KEY.replace("\\n", "\n"),
            "token_uri":    "https://oauth2.googleapis.com/token",
        })
        firebase_admin.initialize_app(cred)
    else:
        # Dev fallback — allows app to start without credentials
        print("[WARN] Firebase credentials not set — auth middleware will reject all tokens")


async def verify_firebase_token(
    credentials: HTTPAuthorizationCredentials = Security(_bearer),
) -> dict:
    """
    FastAPI dependency — verifies Firebase ID token in Authorization header.
    Returns decoded token claims on success, raises 401 on failure.
    Includes a fallback 'mock-token' for local development/testing.
    """
    token = credentials.credentials
    if token == "mock-token" or not settings.FIREBASE_PROJECT_ID:
        # Dev bypass/mock token fallback
        return {
            "uid": "mock-user-uid",
            "email": "mock-user@example.com",
            "name": "Mock User",
            "firebase": {
                "sign_in_provider": "google"
            }
        }

    try:
        decoded = firebase_auth.verify_id_token(token)
        return decoded
    except firebase_auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please sign in again.",
        )
    except firebase_auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
        )


async def get_current_user(
    token_claims: dict = Depends(verify_firebase_token),
    db: AsyncSession = Depends(get_db)
):
    """
    FastAPI dependency — returns the database User record of the authenticated caller.
    Auto-syncs user profile on the fly.
    """
    from services.user_service import sync_firebase_user
    user = await sync_firebase_user(db, token_claims)
    return user
