"""
Warranty Register API - Main Application Entry Point

A FastAPI application for registering and managing device warranties.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from contextlib import asynccontextmanager
import logging

from .config import get_settings
from .database import engine, Base
from .routes import auth, warranty, web

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting Warranty Register API...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")
    
    # Create initial admin user if none exists
    from .database import SessionLocal
    from . import models
    from .auth import get_password_hash
    
    db = SessionLocal()
    try:
        admin_exists = db.query(models.User).filter(
            models.User.is_admin == 'Y'
        ).first()
        
        if not admin_exists:
            # Create default admin user
            admin_user = models.User(
                email="admin@warranty.local",
                hashed_password=get_password_hash("Admin@123"),
                full_name="System Administrator",
                is_active='Y',
                is_admin='Y'
            )
            db.add(admin_user)
            db.commit()
            logger.info("Default admin user created: admin@warranty.local / Admin@123")
    except Exception as e:
        logger.error(f"Error creating default admin: {e}")
    finally:
        db.close()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Warranty Register API...")


# Create FastAPI application
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
origins = settings.allowed_origins.split(",") if settings.allowed_origins != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions globally."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else None
        }
    )


# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(warranty.router, prefix="/api/v1")
app.include_router(web.router)


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint for load balancers and monitoring."""
    return {
        "status": "healthy",
        "service": "warranty-register-api",
        "version": settings.api_version
    }


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Redirect to web login page."""
    return RedirectResponse(url="/web/login")


# API info endpoint
@app.get("/api", tags=["root"])
async def api_info():
    """API information endpoint."""
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "description": settings.api_description,
        "docs": "/docs",
        "health": "/health"
    }
