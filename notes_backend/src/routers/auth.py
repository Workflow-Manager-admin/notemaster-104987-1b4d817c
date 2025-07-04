from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..database import get_db
from ..auth import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from ..models.user import User
from ..schemas import UserCreate, UserResponse, UserLogin, Token

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    responses={404: {"description": "Not found"}},
)

security = HTTPBearer()

# PUBLIC_INTERFACE
@router.post("/register", response_model=UserResponse, summary="Register a new user")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account.
    
    Args:
        user: User registration data containing email, username, and password
        db: Database session
        
    Returns:
        UserResponse: Created user data without password
        
    Raises:
        HTTPException: 400 if username or email already exists
    """
    # Check if user already exists
    db_user = db.query(User).filter(
        (User.email == user.email) | (User.username == user.username)
    ).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

# PUBLIC_INTERFACE
@router.post("/login", response_model=Token, summary="Login user")
def login_user(user_login: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT access token.
    
    Args:
        user_login: User login credentials (username/email and password)
        db: Database session
        
    Returns:
        Token: JWT access token and token type
        
    Raises:
        HTTPException: 401 if authentication fails
    """
    user = authenticate_user(db, user_login.username, user_login.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# PUBLIC_INTERFACE
@router.post("/logout", summary="Logout user")
def logout_user(
    current_user: User = Depends(get_current_active_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Logout the current user.
    
    Note: Since JWT tokens are stateless, this endpoint serves as a logout confirmation.
    The client should discard the token after calling this endpoint.
    
    Args:
        current_user: Current authenticated user
        credentials: JWT token credentials
        
    Returns:
        dict: Logout confirmation message
    """
    return {
        "message": "Successfully logged out",
        "detail": "Token should be discarded on client side"
    }
