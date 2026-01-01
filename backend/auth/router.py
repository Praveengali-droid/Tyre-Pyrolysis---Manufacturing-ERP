"""
Authentication Router - Login, User Management, Password Reset.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import json

from database import get_db
from models.user import User, UserRole, AuditLog
from auth.security import verify_password, get_password_hash, create_access_token
from auth.dependencies import get_current_user_required, require_role, require_admin

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ═══════════════════════════════════════════════════════════
# SCHEMAS
# ═══════════════════════════════════════════════════════════

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: str = "OPERATOR"

class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: str
    is_active: bool
    
    class Config:
        from_attributes = True

class PasswordReset(BaseModel):
    new_password: str


# ═══════════════════════════════════════════════════════════
# HELPER: Audit Logging
# ═══════════════════════════════════════════════════════════

def log_audit(
    db: Session,
    user: Optional[User],
    action: str,
    entity_type: str,
    entity_id: Optional[int] = None,
    description: str = None,
    old_values: dict = None,
    new_values: dict = None,
    request: Request = None
):
    """Create an audit log entry."""
    log = AuditLog(
        user_id=user.id if user else None,
        username=user.username if user else "SYSTEM",
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        old_values=json.dumps(old_values) if old_values else None,
        new_values=json.dumps(new_values) if new_values else None,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None
    )
    db.add(log)
    db.commit()


# ═══════════════════════════════════════════════════════════
# LOGIN / LOGOUT
# ═══════════════════════════════════════════════════════════

@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token."""
    user = db.query(User).filter(User.username == data.username).first()
    
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    
    # Update last login
    user.last_login = datetime.now()
    db.commit()
    
    # Create token
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    
    # Audit log
    log_audit(db, user, "LOGIN", "User", user.id, f"User {user.username} logged in", request=request)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role
        }
    }


@router.get("/me", response_model=UserResponse)
def get_current_user_info(user: User = Depends(get_current_user_required)):
    """Get current authenticated user's info."""
    return user


# ═══════════════════════════════════════════════════════════
# USER MANAGEMENT (Admin Only)
# ═══════════════════════════════════════════════════════════

@router.get("/users", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin())
):
    """List all users (Admin only)."""
    return db.query(User).order_by(User.username).all()


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin())
):
    """Create a new user (Admin only)."""
    # Check for existing username
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Validate role
    if data.role not in [r.value for r in UserRole]:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be: {[r.value for r in UserRole]}")
    
    user = User(
        username=data.username,
        email=data.email,
        password_hash=get_password_hash(data.password),
        full_name=data.full_name,
        role=data.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Audit log
    log_audit(db, admin, "CREATE", "User", user.id, f"Created user {user.username}", request=request)
    
    return user


@router.put("/users/{user_id}/reset-password")
def reset_password(
    user_id: int,
    data: PasswordReset,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin())
):
    """Reset a user's password (Admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.password_hash = get_password_hash(data.new_password)
    db.commit()
    
    # Audit log
    log_audit(db, admin, "PASSWORD_RESET", "User", user.id, 
              f"Admin {admin.username} reset password for {user.username}", request=request)
    
    return {"message": f"Password reset for {user.username}"}


@router.put("/users/{user_id}/deactivate")
def deactivate_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin())
):
    """Deactivate a user account (Admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    
    user.is_active = False
    db.commit()
    
    # Audit log
    log_audit(db, admin, "DEACTIVATE", "User", user.id, 
              f"Admin {admin.username} deactivated user {user.username}", request=request)
    
    return {"message": f"User {user.username} deactivated"}


@router.put("/users/{user_id}/activate")
def activate_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin())
):
    """Reactivate a user account (Admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = True
    db.commit()
    
    # Audit log
    log_audit(db, admin, "ACTIVATE", "User", user.id, 
              f"Admin {admin.username} activated user {user.username}", request=request)
    
    return {"message": f"User {user.username} activated"}


# ═══════════════════════════════════════════════════════════
# AUDIT LOGS (Admin Only)
# ═══════════════════════════════════════════════════════════

@router.get("/audit-logs")
def get_audit_logs(
    entity_type: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin())
):
    """Get audit logs (Admin only)."""
    query = db.query(AuditLog)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if action:
        query = query.filter(AuditLog.action == action)
    
    logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    
    return [{
        "id": log.id,
        "username": log.username,
        "action": log.action,
        "entity_type": log.entity_type,
        "entity_id": log.entity_id,
        "description": log.description,
        "created_at": str(log.created_at)
    } for log in logs]
