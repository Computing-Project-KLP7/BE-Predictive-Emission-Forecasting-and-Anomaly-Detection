import httpx
import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

TRANSTRACK_LOGIN_URL = "https://telematics.transtrack.id/api/login"
TRANSTRACK_LANG = "en"


async def login_with_transtrack(email: str, password: str) -> Dict[str, Any]:
    """
    Login menggunakan API Transtrack third-party.
    
    Args:
        email: Email pengguna
        password: Password pengguna
        
    Returns:
        Response data dari API Transtrack
        
    Raises:
        HTTPException: Jika login gagal
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "email": email,
                "password": password
            }
            
            params = {
                "lang": TRANSTRACK_LANG
            }
            
            response = await client.post(
                TRANSTRACK_LOGIN_URL,
                json=payload,
                params=params
            )
            
            response_data = response.json()
            
            # Check response status - success jika status code 200
            if response.status_code == 200:
                logger.info(f"Login successful untuk email: {email}")
                return response_data
            else:
                # Handle error response dari API
                error_msg = response_data.get("message", "Login gagal")
                logger.warning(
                    f"Login failed with status {response.status_code}: {error_msg}"
                )
                raise HTTPException(
                    status_code=response.status_code if response.status_code >= 400 else status.HTTP_401_UNAUTHORIZED,
                    detail=error_msg
                )
            
    except HTTPException:
        # Re-raise HTTPException yang sudah dibuat
        raise
    except httpx.RequestError as e:
        logger.error(f"Request error saat login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Transtrack API tidak tersedia"
        )
    except Exception as e:
        logger.error(f"Unexpected error saat login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Terjadi error saat proses login"
        )


async def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify token dari API Transtrack (optional).
    Bisa digunakan untuk middleware authentication.
    
    Args:
        token: Access token dari login
        
    Returns:
        User data jika token valid, None jika tidak valid
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {
                "Authorization": f"Bearer {token}"
            }
            
            # Endpoint untuk verify token bisa disesuaikan
            # sesuai dengan dokumentasi Transtrack API
            response = await client.get(
                f"{TRANSTRACK_LOGIN_URL}/verify",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
    except Exception as e:
        logger.error(f"Error verifying token: {str(e)}")
        return None
