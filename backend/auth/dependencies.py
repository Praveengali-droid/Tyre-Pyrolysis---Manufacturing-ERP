"""
FastAPI dependencies for authentication and authorization.

Usage:
    @router.get("/admin-only")
    def admin_endpoint(user: User = Depends(require_role(UserRole.ADMIN))):
        ...
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, List
from functools import wraps

from database import get_db
from models.user import User, UserRole
from auth.security import decode_token

# Bearer token extractor
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Extract and validate the current user from JWT token.
    Returns None if no token or invalid token (for optional auth).
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        return None
    
    username = payload.get("sub")
    if not username:
        return None
    
    user = db.query(User).filter(User.username == username).first()
    if not user or not user.is_active:
        return None
    
    return user


async def get_current_user_required(
    user: User = Depends(get_current_user)
) -> User:
    """
    Require a valid authenticated user.
    Raises 401 if not authenticated.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user


def require_role(*allowed_roles: UserRole):
    """
    Dependency factory to require specific roles.
    
    Usage:
        @router.get("/admin")
        def admin_only(user: User = Depends(require_role(UserRole.ADMIN))):
            ...
        
        @router.get("/managers")
        def managers_up(user: User = Depends(require_role(UserRole.ADMIN, UserRole.MANAGER))):
            ...
    """
    async def role_checker(user: User = Depends(get_current_user_required)) -> User:
        # Superuser bypasses role check
        if user.is_superuser:
            return user
        
        # Check if user's role is in allowed roles
        user_role = UserRole(user.role)
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {[r.value for r in allowed_roles]}"
            )
        return user
    
    return role_checker


def require_admin():
    """Shortcut for admin-only endpoints."""
    return require_role(UserRole.ADMIN)


def require_manager_or_above():
    """Shortcut for manager+ endpoints."""
    return require_role(UserRole.ADMIN, UserRole.MANAGER)


def require_operator_or_above():
    """Shortcut for operator+ endpoints (excludes VIEWER)."""
    return require_role(UserRole.ADMIN, UserRole.MANAGER, UserRole.OPERATOR)


# Role hierarchy check helper
ROLE_HIERARCHY = {
    UserRole.ADMIN: 4,
    UserRole.MANAGER: 3,
    UserRole.OPERATOR: 2,
    UserRole.VIEWER: 1
}


def has_role_or_higher(user: User, min_role: UserRole) -> bool:
    """Check if user has at least the specified role level."""
    if user.is_superuser:
        return True
    user_level = ROLE_HIERARCHY.get(UserRole(user.role), 0)
    min_level = ROLE_HIERARCHY.get(min_role, 999)
    return user_level >= min_level
