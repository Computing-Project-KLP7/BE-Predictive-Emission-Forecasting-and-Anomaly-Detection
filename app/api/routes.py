from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health():
    return {"status": "ok"}

@router.get("/users/{user_id}")
async def get_user(user_id: int):
    return {"id": user_id, "name": "Example User"}
