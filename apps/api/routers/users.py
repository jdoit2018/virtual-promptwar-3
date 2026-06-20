from fastapi import APIRouter

router = APIRouter()


@router.get('/')
async def placeholder():
    return {'router': 'users', 'status': 'not yet implemented'}

