from fastapi import APIRouter
from app.schemas.authentication import LoginRequest
from app.services.authentication_service import login_with_transtrack

router = APIRouter()

@router.post("/login")
async def login(request: LoginRequest):
    """
    Login endpoint yang menggunakan API Transtrack third-party.
    
    Request body:
    - email: Email pengguna
    - password: Password pengguna
    
    Returns:
    - Response dari API Transtrack dengan token dan user data
    """
    return await login_with_transtrack(
        email=request.email,
        password=request.password
    )