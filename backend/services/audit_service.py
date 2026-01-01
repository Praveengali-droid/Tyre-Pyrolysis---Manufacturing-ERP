"""
Audit Service - Centralized audit logging for domain events.

Tracks:
- Auth events (login, password reset)
- Recipe changes (safety critical)
- Stock adjustments (theft risk)
- Maintenance logs (compliance)
- Batch completions
"""
from sqlalchemy.orm import Session
from models.user import AuditLog, User
from typing import Optional
from datetime import datetime
import json


class AuditService:
    """Centralized audit logging for all critical domain events."""
    
    @staticmethod
    def log(
        db: Session,
        action: str,
        entity_type: str,
        entity_id: Optional[int] = None,
        user: Optional[User] = None,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        description: str = None,
        old_values: dict = None,
        new_values: dict = None,
        ip_address: str = None
    ):
        """
        Create an audit log entry.
        
        Args:
            db: Database session
            action: CREATE, UPDATE, DELETE, LOGIN, LOGOUT, COMPLETE, ADJUST
            entity_type: User, Recipe, Batch, Stock, Maintenance, etc.
            entity_id: ID of the affected record
            user: User object (optional, will extract id and username)
            user_id: Direct user ID if user object not available
            username: Username string if user object not available
            description: Human-readable description
            old_values: Dictionary of old values (for UPDATE)
            new_values: Dictionary of new values (for UPDATE/CREATE)
            ip_address: Client IP if available
        """
        # Extract user info
        final_user_id = user.id if user else user_id
        final_username = user.username if user else (username or "SYSTEM")
        
        log_entry = AuditLog(
            user_id=final_user_id,
            username=final_username,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            old_values=json.dumps(old_values) if old_values else None,
            new_values=json.dumps(new_values) if new_values else None,
            ip_address=ip_address
        )
        db.add(log_entry)
        # Don't commit here - let the caller manage transaction
        return log_entry
    
    # ─────────────────────────────────────────────
    # Convenience methods for common audit events
    # ─────────────────────────────────────────────
    
    @staticmethod
    def log_recipe_change(db: Session, user: User, recipe_id: int, recipe_name: str, 
                          old_values: dict = None, new_values: dict = None):
        """Log recipe creation or modification (safety critical)."""
        action = "CREATE" if old_values is None else "UPDATE"
        return AuditService.log(
            db, action, "Recipe", recipe_id, user,
            description=f"Recipe '{recipe_name}' {action.lower()}d",
            old_values=old_values,
            new_values=new_values
        )
    
    @staticmethod
    def log_stock_adjustment(db: Session, user: User, lot_id: int, material_type: str,
                             qty_before: float, qty_after: float, reason: str = None):
        """Log stock quantity adjustments (theft risk)."""
        return AuditService.log(
            db, "ADJUST", "Stock", lot_id, user,
            description=f"Stock adjustment: {material_type} from {qty_before} to {qty_after}. Reason: {reason or 'Not specified'}",
            old_values={"quantity": qty_before},
            new_values={"quantity": qty_after, "reason": reason}
        )
    
    @staticmethod
    def log_batch_complete(db: Session, user: User, batch_id: int, batch_number: str,
                           reactor_code: str, yields: dict):
        """Log batch completion with yields."""
        return AuditService.log(
            db, "COMPLETE", "Batch", batch_id, user,
            description=f"Batch {batch_number} completed on {reactor_code}",
            new_values=yields
        )
    
    @staticmethod
    def log_maintenance(db: Session, user: User, log_id: int, task_name: str, 
                        reactor_code: str = None):
        """Log maintenance task completion (compliance)."""
        desc = f"Maintenance '{task_name}'"
        if reactor_code:
            desc += f" on {reactor_code}"
        desc += " completed"
        return AuditService.log(
            db, "COMPLETE", "Maintenance", log_id, user,
            description=desc
        )
    
    @staticmethod
    def log_dispatch(db: Session, user: User, dispatch_id: int, challan_number: str,
                     customer_name: str, total_qty: float):
        """Log dispatch creation."""
        return AuditService.log(
            db, "CREATE", "Dispatch", dispatch_id, user,
            description=f"Dispatch {challan_number} to {customer_name}: {total_qty} units"
        )
    
    @staticmethod
    def log_delete(db: Session, user: User, entity_type: str, entity_id: int, 
                   description: str, old_values: dict = None):
        """Log any deletion (critical, needs admin)."""
        return AuditService.log(
            db, "DELETE", entity_type, entity_id, user,
            description=description,
            old_values=old_values
        )
