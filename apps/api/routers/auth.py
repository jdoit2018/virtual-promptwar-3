"""
apps/api/routers/auth.py
Authentication syncing endpoint.
"""

from fastapi import APIRouter, Depends
from core.firebase import get_current_user
from models.db_models import User
from models.schemas import UserResponse

router = APIRouter()


@router.post('/sync', response_model=UserResponse)
async def sync_user(current_user: User = Depends(get_current_user)):
    """
    Verifies Firebase token and registers/updates user in database.
    """
    return current_user
