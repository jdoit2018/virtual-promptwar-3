from fastapi import APIRouter

router = APIRouter()


@router.get('/')
async def placeholder():
    return {'router': 'goals', 'status': 'not yet implemented'}

