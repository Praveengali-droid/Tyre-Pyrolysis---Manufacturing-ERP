"""
User and Authentication Models.

Roles:
- ADMIN: Full access, costing, profits, delete, user management
- MANAGER: Approvals, reports, no delete
- OPERATOR: Production batches, maintenance logs, gate entry (vendor read-only)
- VIEWER: Read-only access
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum, ForeignKey
from sqlalchemy.sql import func
from database import Base
import enum


class UserRole(str, enum.Enum):
    """User roles with hierarchical permissions."""
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    OPERATOR = "OPERATOR"
    VIEWER = "VIEWER"


class User(Base):
    """
    System user for authentication and authorization.
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    
    # Role
    role = Column(String(20), default=UserRole.OPERATOR.value)
    
    # Profile
    full_name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)  # For first admin bypass
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


class AuditLog(Base):
    """
    Track critical actions: WHO did WHAT to WHICH record WHEN.
    Used for compliance and debugging.
    """
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Who
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    username = Column(String(50), nullable=True)  # Denormalized for history
    
    # What
    action = Column(String(50), nullable=False)  # CREATE, UPDATE, DELETE, LOGIN, LOGOUT
    entity_type = Column(String(50), nullable=False)  # User, Batch, Vendor, etc.
    entity_id = Column(Integer, nullable=True)
    
    # Details
    description = Column(Text, nullable=True)  # "Deleted Batch GRN-001"
    old_values = Column(Text, nullable=True)   # JSON of old values
    new_values = Column(Text, nullable=True)   # JSON of new values
    
    # Context
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)
    
    # When
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<AuditLog {self.action} {self.entity_type}:{self.entity_id} by {self.username}>"
