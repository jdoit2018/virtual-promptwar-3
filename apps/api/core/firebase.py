"""
apps/api/core/firebase.py
Firebase Admin SDK initialisation — verifies ID tokens for all protected routes.
"""

import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings

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
        print("⚠️  Firebase credentials not set — auth middleware will reject all tokens")


async def verify_firebase_token(
    credentials: HTTPAuthorizationCredentials = Security(_bearer),
) -> dict:
    """
    FastAPI dependency — verifies Firebase ID token in Authorization header.
    Returns decoded token claims on success, raises 401 on failure.

    Usage:
        @router.get("/me")
        async def get_me(token: dict = Depends(verify_firebase_token)):
            uid = token["uid"]
    """
    try:
        decoded = firebase_auth.verify_id_token(credentials.credentials)
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
