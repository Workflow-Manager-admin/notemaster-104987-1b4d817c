from datetime import timedelta
from typing import List
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from ..database import get_db, init_db
from ..auth import (
    authenticate_user, 
    create_access_token, 
    get_current_active_user, 
    get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from ..models.user import User
from ..models.note import Note
from ..schemas import (
    UserCreate, 
    UserResponse, 
    UserLogin, 
    Token,
    NoteCreate, 
    NoteUpdate, 
    NoteResponse
)

# Initialize FastAPI app
app = FastAPI(
    title="Notes API",
    description="A REST API for managing personal notes with user authentication",
    version="1.0.0",
    openapi_tags=[
        {
            "name": "authentication",
            "description": "User authentication and registration"
        },
        {
            "name": "notes",
            "description": "CRUD operations for notes"
        },
        {
            "name": "users",
            "description": "User management operations"
        }
    ]
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on application startup."""
    init_db()

# Health check endpoint
@app.get("/", tags=["health"])
def health_check():
    """
    Health check endpoint.
    
    Returns:
        dict: Health status message
    """
    return {"message": "Notes API is healthy"}

# Authentication endpoints
@app.post("/auth/register", response_model=UserResponse, tags=["authentication"])
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    
    Args:
        user: User registration data
        db: Database session
        
    Returns:
        UserResponse: Created user data
        
    Raises:
        HTTPException: If username or email already exists
    """
    # Check if user already exists
    db_user = db.query(User).filter(
        (User.email == user.email) | (User.username == user.username)
    ).first()
    if db_user:
        raise HTTPException(
            status_code=400,
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

@app.post("/auth/login", response_model=Token, tags=["authentication"])
def login_user(user_login: UserLogin, db: Session = Depends(get_db)):
    """
    Login user and return JWT token.
    
    Args:
        user_login: User login credentials
        db: Database session
        
    Returns:
        Token: JWT access token
        
    Raises:
        HTTPException: If authentication fails
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

# User endpoints
@app.get("/users/me", response_model=UserResponse, tags=["users"])
def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """
    Get current user information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        UserResponse: Current user data
    """
    return current_user

# Note endpoints
@app.post("/notes", response_model=NoteResponse, tags=["notes"])
def create_note(
    note: NoteCreate, 
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new note.
    
    Args:
        note: Note creation data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        NoteResponse: Created note data
    """
    db_note = Note(
        title=note.title,
        content=note.content,
        owner_id=current_user.id
    )
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    
    return db_note

@app.get("/notes", response_model=List[NoteResponse], tags=["notes"])
def get_notes(
    skip: int = 0,
    limit: int = 100,
    search: str = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user's notes with optional search and pagination.
    
    Args:
        skip: Number of notes to skip
        limit: Maximum number of notes to return
        search: Optional search term for note titles and content
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[NoteResponse]: List of user notes
    """
    query = db.query(Note).filter(Note.owner_id == current_user.id)
    
    if search:
        query = query.filter(
            (Note.title.contains(search)) | (Note.content.contains(search))
        )
    
    notes = query.offset(skip).limit(limit).all()
    return notes

@app.get("/notes/{note_id}", response_model=NoteResponse, tags=["notes"])
def get_note(
    note_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific note by ID.
    
    Args:
        note_id: Note ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        NoteResponse: Note data
        
    Raises:
        HTTPException: If note not found or not owned by user
    """
    note = db.query(Note).filter(
        Note.id == note_id,
        Note.owner_id == current_user.id
    ).first()
    
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    return note

@app.put("/notes/{note_id}", response_model=NoteResponse, tags=["notes"])
def update_note(
    note_id: int,
    note_update: NoteUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update a specific note.
    
    Args:
        note_id: Note ID
        note_update: Note update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        NoteResponse: Updated note data
        
    Raises:
        HTTPException: If note not found or not owned by user
    """
    note = db.query(Note).filter(
        Note.id == note_id,
        Note.owner_id == current_user.id
    ).first()
    
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Update note fields
    if note_update.title is not None:
        note.title = note_update.title
    if note_update.content is not None:
        note.content = note_update.content
    
    db.commit()
    db.refresh(note)
    
    return note

@app.delete("/notes/{note_id}", tags=["notes"])
def delete_note(
    note_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a specific note.
    
    Args:
        note_id: Note ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        dict: Deletion confirmation message
        
    Raises:
        HTTPException: If note not found or not owned by user
    """
    note = db.query(Note).filter(
        Note.id == note_id,
        Note.owner_id == current_user.id
    ).first()
    
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    db.delete(note)
    db.commit()
    
    return {"message": "Note deleted successfully"}
