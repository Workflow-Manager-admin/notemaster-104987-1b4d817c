from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..database import init_db
from ..routers import auth, notes, users

# Initialize FastAPI app with comprehensive metadata
app = FastAPI(
    title="Notes API",
    description="""
    A comprehensive REST API for managing personal notes with user authentication.
    
    ## Features
    
    * **User Authentication**: Register, login, and logout with JWT tokens
    * **Notes Management**: Full CRUD operations for personal notes
    * **Search**: Search notes by title and content
    * **Security**: JWT-based authentication with proper error handling
    
    ## Authentication
    
    Most endpoints require authentication. Use the `/auth/login` endpoint to get a JWT token,
    then include it in the Authorization header as `Bearer <token>`.
    
    ## Usage
    
    1. Register a new account with `/auth/register`
    2. Login with `/auth/login` to get an access token
    3. Use the token to access protected endpoints
    4. Manage your notes with the `/notes/` endpoints
    """,
    version="1.0.0",
    contact={
        "name": "Notes API Support",
        "url": "https://github.com/yourorg/notes-api",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=[
        {
            "name": "authentication",
            "description": "User authentication and registration operations"
        },
        {
            "name": "notes",
            "description": "CRUD operations for managing personal notes"
        },
        {
            "name": "users",
            "description": "User profile and account management"
        },
        {
            "name": "health",
            "description": "Health check and system status"
        }
    ]
)

# CORS configuration
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://vscode-internal-2892-beta.beta01.cloud.kavia.ai:3000")

# Add CORS middleware with secure configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["X-Total-Count"],
    max_age=3600,
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle all unhandled exceptions globally."""
    error_msg = str(exc)
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    
    # Log unexpected errors
    print(f"Unexpected error: {error_msg}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred. Please try again later."}
    )

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables and perform startup tasks."""
    init_db()

# Include routers
app.include_router(auth.router)
app.include_router(notes.router)
app.include_router(users.router)

# Health check endpoint
@app.get("/", tags=["health"], summary="Health check")
def health_check():
    """
    Health check endpoint to verify API is running.
    
    Returns:
        dict: Health status message with API information
    """
    return {
        "message": "Notes API is healthy",
        "version": "1.0.0",
        "status": "active"
    }

# API documentation endpoint
@app.get("/health", tags=["health"], summary="Detailed health check")
def detailed_health_check():
    """
    Detailed health check with system information.
    
    Returns:
        dict: Detailed health status and system information
    """
    return {
        "status": "healthy",
        "service": "Notes API",
        "version": "1.0.0",
        "description": "REST API for managing personal notes",
        "endpoints": {
            "authentication": "/auth/",
            "notes": "/notes/",
            "users": "/users/",
            "documentation": "/docs",
            "openapi": "/openapi.json"
        }
    }
