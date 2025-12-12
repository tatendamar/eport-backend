"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum


class WarrantyStatusEnum(str, Enum):
    """Warranty status enumeration."""
    REGISTERED = "registered"
    ACTIVE = "active"
    EXPIRED = "expired"
    CLAIMED = "claimed"


# ==================== User Schemas ====================

class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """Schema for user responses."""
    id: UUID
    is_active: str
    is_admin: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserWithToken(BaseModel):
    """Schema for user with access token."""
    user: UserResponse
    access_token: str
    token_type: str = "bearer"


# ==================== Warranty Schemas ====================

class WarrantyRegisterRequest(BaseModel):
    """Schema for registering a warranty from the Next.js app."""
    asset_id: str = Field(..., description="UUID of the asset from Next.js app")
    asset_name: str = Field(..., description="Name of the asset")
    category: Optional[str] = Field(None, description="Asset category")
    department: Optional[str] = Field(None, description="Asset department")
    cost: Optional[float] = Field(None, ge=0, description="Asset cost")
    date_purchased: Optional[datetime] = Field(None, description="Purchase date")
    warranty_notes: Optional[str] = Field(None, description="Additional warranty notes")
    registered_by_email: Optional[str] = Field(None, description="Email of the user registering")


class WarrantyResponse(BaseModel):
    """Schema for warranty responses."""
    id: UUID
    asset_id: str
    asset_name: str
    category: Optional[str]
    department: Optional[str]
    cost: Optional[float]
    date_purchased: Optional[datetime]
    warranty_status: WarrantyStatusEnum
    warranty_start_date: Optional[datetime]
    warranty_end_date: Optional[datetime]
    warranty_notes: Optional[str]
    registered_by: UUID
    registered_by_email: Optional[str]
    registered_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class WarrantyListResponse(BaseModel):
    """Schema for listing warranties with pagination."""
    warranties: List[WarrantyResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class WarrantyRegistrationResult(BaseModel):
    """Schema for warranty registration result."""
    success: bool
    message: str
    warranty_id: Optional[UUID] = None
    warranty_status: Optional[str] = None


# ==================== Token Schemas ====================

class Token(BaseModel):
    """JWT token schema."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data."""
    email: Optional[str] = None
    user_id: Optional[str] = None


# ==================== API Response Schemas ====================

class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool = True
    message: str


class ErrorResponse(BaseModel):
    """Generic error response."""
    success: bool = False
    error: str
    detail: Optional[str] = None
