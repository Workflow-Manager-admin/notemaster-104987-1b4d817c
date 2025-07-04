from fastapi import APIRouter, Depends

from ..auth import get_current_active_user
from ..models.user import User
from ..schemas import UserResponse

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

# PUBLIC_INTERFACE
@router.get("/me", response_model=UserResponse, summary="Get current user")
def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """
    Get current authenticated user information.
    
    Args:
        current_user: Current authenticated user from JWT token
        
    Returns:
        UserResponse: Current user data without sensitive information
    """
    return current_user
