from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..auth import get_current_active_user
from ..models.user import User
from ..models.note import Note
from ..schemas import NoteCreate, NoteUpdate, NoteResponse

router = APIRouter(
    prefix="/notes",
    tags=["notes"],
    responses={404: {"description": "Not found"}},
)

# PUBLIC_INTERFACE
@router.post("/", response_model=NoteResponse, summary="Create a new note")
def create_note(
    note: NoteCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new note for the authenticated user.
    
    Args:
        note: Note creation data with title and content
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        NoteResponse: Created note data with metadata
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

# PUBLIC_INTERFACE
@router.get("/", response_model=List[NoteResponse], summary="Get user's notes")
def get_notes(
    skip: int = Query(0, ge=0, description="Number of notes to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of notes to return"),
    search: Optional[str] = Query(None, description="Search term for note titles and content"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user's notes with optional search and pagination.
    
    Args:
        skip: Number of notes to skip for pagination
        limit: Maximum number of notes to return
        search: Optional search term to filter notes by title or content
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[NoteResponse]: List of user's notes matching criteria
    """
    query = db.query(Note).filter(Note.owner_id == current_user.id)
    
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Note.title.ilike(search_filter)) | (Note.content.ilike(search_filter))
        )
    
    # Order by most recently updated first
    query = query.order_by(Note.updated_at.desc(), Note.created_at.desc())
    notes = query.offset(skip).limit(limit).all()
    return notes

# PUBLIC_INTERFACE
@router.get("/{note_id}", response_model=NoteResponse, summary="Get a specific note")
def get_note(
    note_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific note by ID.
    
    Args:
        note_id: ID of the note to retrieve
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        NoteResponse: Note data
        
    Raises:
        HTTPException: 404 if note not found or not owned by user
    """
    note = db.query(Note).filter(
        Note.id == note_id,
        Note.owner_id == current_user.id
    ).first()
    
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    return note

# PUBLIC_INTERFACE
@router.put("/{note_id}", response_model=NoteResponse, summary="Update a note")
def update_note(
    note_id: int,
    note_update: NoteUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update a specific note.
    
    Args:
        note_id: ID of the note to update
        note_update: Note update data (title and/or content)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        NoteResponse: Updated note data
        
    Raises:
        HTTPException: 404 if note not found or not owned by user
        HTTPException: 400 if no valid update data provided
    """
    note = db.query(Note).filter(
        Note.id == note_id,
        Note.owner_id == current_user.id
    ).first()
    
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    # Check if there's anything to update
    if note_update.title is None and note_update.content is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field (title or content) must be provided for update"
        )
    
    # Update note fields
    if note_update.title is not None:
        note.title = note_update.title
    if note_update.content is not None:
        note.content = note_update.content
    
    db.commit()
    db.refresh(note)
    
    return note

# PUBLIC_INTERFACE
@router.delete("/{note_id}", summary="Delete a note")
def delete_note(
    note_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a specific note.
    
    Args:
        note_id: ID of the note to delete
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        dict: Deletion confirmation message
        
    Raises:
        HTTPException: 404 if note not found or not owned by user
    """
    note = db.query(Note).filter(
        Note.id == note_id,
        Note.owner_id == current_user.id
    ).first()
    
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    db.delete(note)
    db.commit()
    
    return {"message": "Note deleted successfully"}

# PUBLIC_INTERFACE
@router.get("/search/", response_model=List[NoteResponse], summary="Search notes")
def search_notes(
    q: str = Query(..., min_length=1, description="Search query"),
    skip: int = Query(0, ge=0, description="Number of notes to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of notes to return"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Search notes by title and content.
    
    Args:
        q: Search query string
        skip: Number of notes to skip for pagination
        limit: Maximum number of notes to return
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[NoteResponse]: List of notes matching the search query
    """
    search_filter = f"%{q}%"
    query = db.query(Note).filter(
        Note.owner_id == current_user.id,
        (Note.title.ilike(search_filter)) | (Note.content.ilike(search_filter))
    )
    
    # Order by relevance (title matches first, then content matches)
    query = query.order_by(
        Note.title.ilike(search_filter).desc(),
        Note.updated_at.desc()
    )
    
    notes = query.offset(skip).limit(limit).all()
    return notes
