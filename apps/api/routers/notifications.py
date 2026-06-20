from fastapi import APIRouter

router = APIRouter()


@router.get('/')
async def placeholder():
    return {'router': 'notifications', 'status': 'not yet implemented'}

