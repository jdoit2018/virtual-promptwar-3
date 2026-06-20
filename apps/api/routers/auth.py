from fastapi import APIRouter

router = APIRouter()


@router.get('/')
async def placeholder():
    return {'router': 'auth', 'status': 'not yet implemented'}

