from fastapi import APIRouter

router = APIRouter()


@router.get('/')
async def placeholder():
    return {'router': 'logs', 'status': 'not yet implemented'}

