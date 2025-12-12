"""
API routes for user authentication.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from ..database import get_db
from .. import models, schemas
from ..auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
    get_current_admin_user
)
from ..config import get_settings

router = APIRouter(prefix="/auth", tags=["authentication"])
settings = get_settings()


@router.post(
    "/register",
    response_model=schemas.UserWithToken,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account"
)
async def register_user(
    user_data: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.
    
    Args:
        user_data: User registration data
        db: Database session
    
    Returns:
        Created user with access token
    
    Raises:
        HTTPException: If email already exists
    """
    # Check if user exists
    existing_user = db.query(models.User).filter(
        models.User.email == user_data.email
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = models.User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        is_active='Y',
        is_admin='N'
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Generate access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": new_user.email, "user_id": str(new_user.id)},
        expires_delta=access_token_expires
    )
    
    return schemas.UserWithToken(
        user=schemas.UserResponse.model_validate(new_user),
        access_token=access_token,
        token_type="bearer"
    )


@router.post(
    "/login",
    response_model=schemas.UserWithToken,
    summary="User login",
    description="Authenticate user and return access token"
)
async def login(
    login_data: schemas.UserLogin,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return access token.
    
    Args:
        login_data: Login credentials
        db: Database session
    
    Returns:
        User with access token
    
    Raises:
        HTTPException: If credentials are invalid
    """
    # Find user by email
    user = db.query(models.User).filter(
        models.User.email == login_data.email
    ).first()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.is_active != 'Y':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Generate access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": str(user.id)},
        expires_delta=access_token_expires
    )
    
    return schemas.UserWithToken(
        user=schemas.UserResponse.model_validate(user),
        access_token=access_token,
        token_type="bearer"
    )


@router.get(
    "/me",
    response_model=schemas.UserResponse,
    summary="Get current user",
    description="Get the currently authenticated user's profile"
)
async def get_me(
    current_user: models.User = Depends(get_current_user)
):
    """
    Get current authenticated user's profile.
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        User profile
    """
    return current_user


@router.post(
    "/create-admin",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create admin user",
    description="Create a new admin user (requires admin privileges)"
)
async def create_admin(
    user_data: schemas.UserCreate,
    current_admin: models.User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Create a new admin user.
    
    Args:
        user_data: User data for new admin
        current_admin: Current admin user (for authorization)
        db: Database session
    
    Returns:
        Created admin user
    """
    # Check if user exists
    existing_user = db.query(models.User).filter(
        models.User.email == user_data.email
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new admin user
    hashed_password = get_password_hash(user_data.password)
    new_admin = models.User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        is_active='Y',
        is_admin='Y'
    )
    
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    
    return new_admin
