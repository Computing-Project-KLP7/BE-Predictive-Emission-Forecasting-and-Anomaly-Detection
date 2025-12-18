from fastapi import APIRouter, HTTPException, status
from app.schemas.authentication import LoginRequest, LoginResponse, AuthToken
from app.services.authentication_service import login_with_transtrack

router = APIRouter()


@router.get("/")
def data_summary(emision_id: int):
    return {"status": "healthy", "emission_id": emision_id}


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Login endpoint yang menggunakan API Transtrack third-party.
    
    Request body:
    - email: Email pengguna
    - password: Password pengguna
    
    Returns:
    - Response dari API Transtrack dengan token dan user data
    """
    try:
        response = await login_with_transtrack(
            email=request.email,
            password=request.password
        )
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Terjadi error saat proses login"
        )