"""
API routes for warranty registration and management.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime, timedelta
import math

from ..database import get_db
from .. import models, schemas
from ..auth import (
    get_current_user, 
    get_current_admin_user, 
    validate_api_key,
    get_api_key_or_user
)

router = APIRouter(prefix="/warranties", tags=["warranties"])


@router.post(
    "/register",
    response_model=schemas.WarrantyRegistrationResult,
    summary="Register a device warranty",
    description="Register a new warranty for an asset. Can be called with API key from Next.js app."
)
async def register_warranty(
    warranty_data: schemas.WarrantyRegisterRequest,
    auth_result: tuple = Depends(get_api_key_or_user),
    db: Session = Depends(get_db)
):
    """
    Register a new warranty for an asset.
    
    This endpoint can be called by:
    - The Next.js app using an API key (X-API-Key header)
    - Authenticated users using JWT token
    
    Args:
        warranty_data: Warranty registration data
        auth_result: Authentication result (user or API key)
        db: Database session
    
    Returns:
        WarrantyRegistrationResult with success status and warranty ID
    """
    user, is_api_key = auth_result
    
    # Check if warranty already exists for this asset
    existing = db.query(models.Warranty).filter(
        models.Warranty.asset_id == warranty_data.asset_id
    ).first()
    
    if existing:
        return schemas.WarrantyRegistrationResult(
            success=False,
            message="Warranty already registered for this asset",
            warranty_id=existing.id,
            warranty_status=existing.warranty_status.value
        )
    
    # For API key auth, we need a system user or create one
    if is_api_key:
        # Find or create a system user for API registrations
        system_user = db.query(models.User).filter(
            models.User.email == "system@warranty-api.local"
        ).first()
        
        if not system_user:
            from ..auth import get_password_hash
            system_user = models.User(
                email="system@warranty-api.local",
                hashed_password=get_password_hash("system-password-not-for-login"),
                full_name="System User",
                is_active='Y',
                is_admin='N'
            )
            db.add(system_user)
            db.commit()
            db.refresh(system_user)
        
        registered_by_id = system_user.id
    else:
        registered_by_id = user.id
    
    # Calculate warranty end date (1 year from registration)
    warranty_end = datetime.utcnow() + timedelta(days=365)
    
    # Create warranty record
    warranty = models.Warranty(
        asset_id=warranty_data.asset_id,
        asset_name=warranty_data.asset_name,
        category=warranty_data.category,
        department=warranty_data.department,
        cost=warranty_data.cost,
        date_purchased=warranty_data.date_purchased,
        warranty_status=models.WarrantyStatus.REGISTERED,
        warranty_start_date=datetime.utcnow(),
        warranty_end_date=warranty_end,
        warranty_notes=warranty_data.warranty_notes,
        registered_by=registered_by_id,
        registered_by_email=warranty_data.registered_by_email
    )
    
    db.add(warranty)
    db.commit()
    db.refresh(warranty)
    
    return schemas.WarrantyRegistrationResult(
        success=True,
        message="Warranty registered successfully",
        warranty_id=warranty.id,
        warranty_status=warranty.warranty_status.value
    )


@router.get(
    "/check/{asset_id}",
    response_model=Optional[schemas.WarrantyResponse],
    summary="Check warranty status for an asset",
    description="Check if an asset has a registered warranty"
)
async def check_warranty(
    asset_id: str,
    api_key_valid: bool = Depends(validate_api_key),
    db: Session = Depends(get_db)
):
    """
    Check warranty status for a specific asset.
    
    Args:
        asset_id: The asset ID to check
        db: Database session
    
    Returns:
        Warranty details if found, null otherwise
    """
    warranty = db.query(models.Warranty).filter(
        models.Warranty.asset_id == asset_id
    ).first()
    
    return warranty


@router.get(
    "/",
    response_model=schemas.WarrantyListResponse,
    summary="List all registered warranties",
    description="Get a paginated list of all registered warranties (admin only)"
)
async def list_warranties(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, description="Filter by warranty status"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all registered warranties with pagination.
    
    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        status_filter: Optional status filter
        current_user: Authenticated user
        db: Database session
    
    Returns:
        Paginated list of warranties
    """
    query = db.query(models.Warranty)
    
    # Apply status filter if provided
    if status_filter:
        try:
            status_enum = models.WarrantyStatus(status_filter)
            query = query.filter(models.Warranty.warranty_status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status filter: {status_filter}"
            )
    
    # Get total count
    total = query.count()
    
    # Calculate pagination
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    offset = (page - 1) * page_size
    
    # Get paginated results
    warranties = query.order_by(
        models.Warranty.registered_at.desc()
    ).offset(offset).limit(page_size).all()
    
    return schemas.WarrantyListResponse(
        warranties=warranties,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get(
    "/{warranty_id}",
    response_model=schemas.WarrantyResponse,
    summary="Get warranty details",
    description="Get details of a specific warranty"
)
async def get_warranty(
    warranty_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get details of a specific warranty.
    
    Args:
        warranty_id: The warranty UUID
        current_user: Authenticated user
        db: Database session
    
    Returns:
        Warranty details
    
    Raises:
        HTTPException: If warranty not found
    """
    warranty = db.query(models.Warranty).filter(
        models.Warranty.id == warranty_id
    ).first()
    
    if not warranty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warranty not found"
        )
    
    return warranty


@router.put(
    "/{warranty_id}/status",
    response_model=schemas.WarrantyResponse,
    summary="Update warranty status",
    description="Update the status of a warranty (admin only)"
)
async def update_warranty_status(
    warranty_id: str,
    new_status: str,
    current_user: models.User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update warranty status.
    
    Args:
        warranty_id: The warranty UUID
        new_status: New status value
        current_user: Admin user
        db: Database session
    
    Returns:
        Updated warranty details
    """
    warranty = db.query(models.Warranty).filter(
        models.Warranty.id == warranty_id
    ).first()
    
    if not warranty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warranty not found"
        )
    
    try:
        status_enum = models.WarrantyStatus(new_status)
        warranty.warranty_status = status_enum
        db.commit()
        db.refresh(warranty)
        return warranty
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status: {new_status}"
        )
