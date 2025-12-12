"""
SQLAlchemy ORM models for the Warranty Register database.
"""
from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from .database import Base


class WarrantyStatus(str, enum.Enum):
    """Enum for warranty status."""
    REGISTERED = "registered"
    ACTIVE = "active"
    EXPIRED = "expired"
    CLAIMED = "claimed"


class User(Base):
    """User model for authentication and warranty tracking."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(String(1), default='Y')
    is_admin = Column(String(1), default='N')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    warranties = relationship("Warranty", back_populates="registered_by_user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class Warranty(Base):
    """Warranty registration model for assets."""
    __tablename__ = "warranties"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Asset details from Next.js app
    asset_id = Column(String(255), nullable=False, index=True)
    asset_name = Column(String(255), nullable=False)
    category = Column(String(255), nullable=True)
    department = Column(String(255), nullable=True)
    cost = Column(Float, nullable=True)
    date_purchased = Column(DateTime, nullable=True)
    
    # Warranty details
    warranty_status = Column(
        SQLEnum(WarrantyStatus),
        default=WarrantyStatus.REGISTERED,
        nullable=False
    )
    warranty_start_date = Column(DateTime, default=datetime.utcnow)
    warranty_end_date = Column(DateTime, nullable=True)
    warranty_notes = Column(Text, nullable=True)
    
    # Registration tracking
    registered_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    registered_by_email = Column(String(255), nullable=True)
    registered_at = Column(DateTime, default=datetime.utcnow)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    registered_by_user = relationship("User", back_populates="warranties")
    
    def __repr__(self):
        return f"<Warranty(id={self.id}, asset={self.asset_name}, status={self.warranty_status})>"
