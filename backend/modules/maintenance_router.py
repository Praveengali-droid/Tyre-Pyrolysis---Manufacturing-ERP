"""
Maintenance Router - Schedules, Logs, and Task Completion APIs.

Includes Safety Interlock logic for reactor maintenance.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
import os
import shutil

from database import get_db
from models.reactor import Reactor
from models.maintenance import MaintenanceSchedule, MaintenanceLog, MaintenanceRequest

router = APIRouter(prefix="/maintenance", tags=["Maintenance"])


# ═══════════════════════════════════════════════════════════
# SCHEMAS
# ═══════════════════════════════════════════════════════════

class ScheduleCreate(BaseModel):
    reactor_id: Optional[int] = None
    equipment_type: str = "REACTOR"
    task_name: str
    task_description: Optional[str] = None
    frequency_batches: Optional[int] = 3
    frequency_days: Optional[int] = 30
    warning_batches: Optional[int] = None

class ScheduleResponse(BaseModel):
    id: int
    reactor_id: Optional[int] = None
    task_name: str
    frequency_batches: Optional[int] = None
    frequency_days: Optional[int] = None
    is_active: bool
    
    class Config:
        from_attributes = True

class LogCreate(BaseModel):
    schedule_id: int
    reactor_id: int
    performed_by: Optional[str] = None
    notes: Optional[str] = None

class LogResponse(BaseModel):
    id: int
    schedule_id: int
    reactor_id: Optional[int] = None
    performed_date: datetime
    performed_by: Optional[str] = None
    notes: Optional[str] = None
    batches_at_maintenance: int
    
    class Config:
        from_attributes = True

class RequestCreate(BaseModel):
    reactor_id: Optional[int] = None
    equipment_type: str = "REACTOR"
    equipment_name: Optional[str] = None
    request_type: str = "BREAKDOWN"
    priority: str = "MEDIUM"
    title: str
    description: Optional[str] = None
    requested_by: str = "Operator"

class RequestResponse(BaseModel):
    id: int
    request_number: str
    reactor_id: Optional[int] = None
    equipment_type: str
    equipment_name: Optional[str] = None
    request_type: str
    priority: str
    status: str
    title: str
    description: Optional[str] = None
    requested_by: Optional[str] = None
    requested_at: datetime
    assigned_to: Optional[str] = None
    
    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════

def generate_request_number(db: Session) -> str:
    """Generate request number: REQ-YYYYMMDD-XXX"""
    today = date.today().strftime("%Y%m%d")
    prefix = f"REQ-{today}-"
    last = db.query(MaintenanceRequest).filter(
        MaintenanceRequest.request_number.like(f"{prefix}%")
    ).order_by(MaintenanceRequest.id.desc()).first()
    seq = 1
    if last:
        try:
            seq = int(last.request_number.split("-")[-1]) + 1
        except:
            pass
    return f"{prefix}{seq:03d}"


# ═══════════════════════════════════════════════════════════
# SCHEDULE ENDPOINTS
# ═══════════════════════════════════════════════════════════

@router.get("/schedules", response_model=List[ScheduleResponse])
def list_schedules(reactor_id: Optional[int] = None, db: Session = Depends(get_db)):
    """List all maintenance schedules."""
    query = db.query(MaintenanceSchedule).filter(MaintenanceSchedule.is_active == True)
    if reactor_id:
        query = query.filter(MaintenanceSchedule.reactor_id == reactor_id)
    return query.all()


@router.post("/schedules", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
def create_schedule(data: ScheduleCreate, db: Session = Depends(get_db)):
    """Create a new maintenance schedule."""
    schedule = MaintenanceSchedule(
        reactor_id=data.reactor_id,
        equipment_type=data.equipment_type,
        task_name=data.task_name,
        task_description=data.task_description,
        frequency_batches=data.frequency_batches,
        frequency_days=data.frequency_days,
        warning_batches=data.warning_batches or (data.frequency_batches - 1 if data.frequency_batches else None)
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


# ═══════════════════════════════════════════════════════════
# DUE TASKS / DASHBOARD
# ═══════════════════════════════════════════════════════════

@router.get("/due-tasks")
def get_due_tasks(db: Session = Depends(get_db)):
    """Get maintenance tasks that are due or approaching due date."""
    reactors = db.query(Reactor).filter(Reactor.is_active == True).all()
    
    due_tasks = []
    warning_tasks = []
    
    for reactor in reactors:
        task_info = {
            "reactor_id": reactor.id,
            "reactor_code": reactor.reactor_code,
            "reactor_name": reactor.name,
            "batches_since_cleaning": reactor.batches_since_last_cleaning or 0,
            "maintenance_frequency": reactor.maintenance_frequency or 3,
            "last_maintenance_date": str(reactor.last_maintenance_date) if reactor.last_maintenance_date else None,
            "task_name": "Carbon Cleaning"
        }
        
        if reactor.maintenance_due:
            task_info["status"] = "DUE"
            task_info["urgency"] = "CRITICAL"
            due_tasks.append(task_info)
        elif reactor.maintenance_warning:
            task_info["status"] = "WARNING"
            task_info["urgency"] = "WARNING"
            warning_tasks.append(task_info)
    
    return {
        "due": due_tasks,
        "warning": warning_tasks,
        "total_due": len(due_tasks),
        "total_warning": len(warning_tasks)
    }


@router.get("/reactor-status")
def get_reactor_maintenance_status(db: Session = Depends(get_db)):
    """Get maintenance status for all reactors (for dashboard cards)."""
    reactors = db.query(Reactor).filter(Reactor.is_active == True).all()
    
    result = []
    for reactor in reactors:
        maint_status = "OK"
        color = "green"
        can_start = True
        breakdown_info = None
        
        # Check for active breakdown requests (CRITICAL/HIGH)
        active_breakdown = db.query(MaintenanceRequest).filter(
            MaintenanceRequest.reactor_id == reactor.id,
            MaintenanceRequest.request_type == "BREAKDOWN",
            MaintenanceRequest.priority.in_(["CRITICAL", "HIGH"]),
            MaintenanceRequest.status.in_(["OPEN", "IN_PROGRESS", "ON_HOLD"])
        ).first()
        
        if active_breakdown:
            maint_status = "BREAKDOWN"
            color = "red"
            can_start = False
            breakdown_info = {
                "request_id": active_breakdown.id,
                "title": active_breakdown.title,
                "priority": active_breakdown.priority,
                "status": active_breakdown.status
            }
        elif reactor.maintenance_due:
            maint_status = "BLOCKED"
            color = "red"
            can_start = False
        elif reactor.maintenance_warning:
            maint_status = "WARNING"
            color = "yellow"
        
        result.append({
            "reactor_id": reactor.id,
            "reactor_code": reactor.reactor_code,
            "name": reactor.name,
            "status": reactor.status,
            "batches_since_cleaning": reactor.batches_since_last_cleaning or 0,
            "maintenance_frequency": reactor.maintenance_frequency or 3,
            "maintenance_status": maint_status,
            "maintenance_color": color,
            "can_start_batch": can_start,
            "last_maintenance": str(reactor.last_maintenance_date) if reactor.last_maintenance_date else None,
            "active_breakdown": breakdown_info
        })
    
    return result


# ═══════════════════════════════════════════════════════════
# COMPLETE TASK (MAINTENANCE LOG)
# ═══════════════════════════════════════════════════════════

@router.post("/complete-task")
def complete_maintenance_task(
    reactor_id: int = Form(...),
    task_name: str = Form(default="Carbon Cleaning"),
    performed_by: str = Form(default="Operator"),
    notes: Optional[str] = Form(default=None),
    photo: Optional[UploadFile] = File(default=None),
    db: Session = Depends(get_db)
):
    """
    Mark a maintenance task as complete.
    
    This action:
    1. Creates a MaintenanceLog entry
    2. RESETS reactor.batches_since_last_cleaning to 0
    3. Updates last_maintenance_date
    4. Optionally saves proof photo
    """
    # Get reactor
    reactor = db.query(Reactor).filter(Reactor.id == reactor_id).first()
    if not reactor:
        raise HTTPException(status_code=404, detail="Reactor not found")
    
    # Get or create schedule
    schedule = db.query(MaintenanceSchedule).filter(
        MaintenanceSchedule.reactor_id == reactor_id,
        MaintenanceSchedule.task_name == task_name
    ).first()
    
    if not schedule:
        # Auto-create schedule
        schedule = MaintenanceSchedule(
            reactor_id=reactor_id,
            task_name=task_name,
            frequency_batches=reactor.maintenance_frequency or 3
        )
        db.add(schedule)
        db.flush()
    
    # Save photo if provided
    photo_path = None
    if photo:
        upload_dir = "uploads/maintenance"
        os.makedirs(upload_dir, exist_ok=True)
        filename = f"{reactor.reactor_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{photo.filename}"
        photo_path = os.path.join(upload_dir, filename)
        with open(photo_path, "wb") as f:
            shutil.copyfileobj(photo.file, f)
    
    # Create log entry
    log = MaintenanceLog(
        schedule_id=schedule.id,
        reactor_id=reactor_id,
        performed_by=performed_by,
        notes=notes,
        photo_path=photo_path,
        batches_at_maintenance=reactor.batches_since_last_cleaning or 0,
        counter_reset=True
    )
    db.add(log)
    
    # RESET the reactor counter (safety unlock)
    reactor.batches_since_last_cleaning = 0
    reactor.last_maintenance_date = datetime.now()
    
    db.commit()
    db.refresh(log)
    
    return {
        "message": "Maintenance task completed",
        "reactor_code": reactor.reactor_code,
        "log_id": log.id,
        "batches_reset": True,
        "can_start_batch": True
    }


@router.get("/logs", response_model=List[LogResponse])
def list_logs(
    reactor_id: Optional[int] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List maintenance logs."""
    query = db.query(MaintenanceLog)
    if reactor_id:
        query = query.filter(MaintenanceLog.reactor_id == reactor_id)
    return query.order_by(MaintenanceLog.performed_date.desc()).limit(limit).all()


# ═══════════════════════════════════════════════════════════
# SAFETY INTERLOCK CHECK (called by production router)
# ═══════════════════════════════════════════════════════════

@router.get("/check-interlock/{reactor_id}")
def check_safety_interlock(reactor_id: int, db: Session = Depends(get_db)):
    """
    Check if a reactor is safe to start a new batch.
    Returns False if maintenance is due (safety lockout).
    """
    reactor = db.query(Reactor).filter(Reactor.id == reactor_id).first()
    if not reactor:
        raise HTTPException(status_code=404, detail="Reactor not found")
    
    if reactor.maintenance_due:
        return {
            "safe_to_start": False,
            "reason": f"Safety Lock: Maintenance Due. Reactor has run {reactor.batches_since_last_cleaning} batches since last cleaning (limit: {reactor.maintenance_frequency}).",
            "action_required": "Complete Carbon Cleaning maintenance before starting new batch.",
            "batches_since_cleaning": reactor.batches_since_last_cleaning,
            "limit": reactor.maintenance_frequency
        }
    
    return {
        "safe_to_start": True,
        "batches_since_cleaning": reactor.batches_since_last_cleaning,
        "limit": reactor.maintenance_frequency,
        "batches_remaining": (reactor.maintenance_frequency or 3) - (reactor.batches_since_last_cleaning or 0)
    }


# ═══════════════════════════════════════════════════════════
# MAINTENANCE REQUESTS
# ═══════════════════════════════════════════════════════════

@router.get("/requests", response_model=List[RequestResponse])
def list_requests(
    status_filter: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List maintenance requests with optional filtering."""
    query = db.query(MaintenanceRequest)
    if status_filter:
        query = query.filter(MaintenanceRequest.status == status_filter)
    if priority:
        query = query.filter(MaintenanceRequest.priority == priority)
    return query.order_by(MaintenanceRequest.requested_at.desc()).limit(limit).all()


@router.get("/requests/summary")
def get_requests_summary(db: Session = Depends(get_db)):
    """Get summary of requests by status."""
    open_count = db.query(MaintenanceRequest).filter(MaintenanceRequest.status == "OPEN").count()
    in_progress = db.query(MaintenanceRequest).filter(MaintenanceRequest.status == "IN_PROGRESS").count()
    on_hold = db.query(MaintenanceRequest).filter(MaintenanceRequest.status == "ON_HOLD").count()
    completed = db.query(MaintenanceRequest).filter(MaintenanceRequest.status == "COMPLETED").count()
    
    critical = db.query(MaintenanceRequest).filter(
        MaintenanceRequest.priority == "CRITICAL",
        MaintenanceRequest.status.in_(["OPEN", "IN_PROGRESS"])
    ).count()
    
    return {
        "open": open_count,
        "in_progress": in_progress,
        "on_hold": on_hold,
        "completed": completed,
        "critical_active": critical,
        "total_active": open_count + in_progress + on_hold
    }


@router.get("/requests/{request_id}", response_model=RequestResponse)
def get_request(request_id: int, db: Session = Depends(get_db)):
    """Get request details."""
    req = db.query(MaintenanceRequest).filter(MaintenanceRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    return req


@router.post("/requests", response_model=RequestResponse, status_code=status.HTTP_201_CREATED)
def create_request(data: RequestCreate, db: Session = Depends(get_db)):
    """Create a new maintenance request."""
    request = MaintenanceRequest(
        request_number=generate_request_number(db),
        reactor_id=data.reactor_id,
        equipment_type=data.equipment_type,
        equipment_name=data.equipment_name,
        request_type=data.request_type,
        priority=data.priority,
        status="OPEN",
        title=data.title,
        description=data.description,
        requested_by=data.requested_by,
        requested_at=datetime.now()
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


@router.put("/requests/{request_id}/assign")
def assign_request(request_id: int, assigned_to: str, db: Session = Depends(get_db)):
    """Assign a request to a technician."""
    req = db.query(MaintenanceRequest).filter(MaintenanceRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    
    req.assigned_to = assigned_to
    req.assigned_at = datetime.now()
    req.status = "IN_PROGRESS"
    db.commit()
    
    return {"message": f"Request assigned to {assigned_to}", "status": req.status}


@router.put("/requests/{request_id}/status")
def update_request_status(request_id: int, new_status: str, db: Session = Depends(get_db)):
    """Update request status (OPEN, IN_PROGRESS, ON_HOLD, DEFERRED, CANCELLED)."""
    req = db.query(MaintenanceRequest).filter(MaintenanceRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    
    valid_statuses = ["OPEN", "IN_PROGRESS", "ON_HOLD", "DEFERRED", "CANCELLED"]
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    req.status = new_status
    db.commit()
    
    return {"message": f"Status updated to {new_status}"}


@router.put("/requests/{request_id}/complete")
def complete_request(
    request_id: int,
    resolution_notes: str,
    resolved_by: str = "Technician",
    downtime_hours: Optional[float] = None,
    labor_hours: Optional[float] = None,
    parts_cost: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """Mark a request as completed with resolution details."""
    req = db.query(MaintenanceRequest).filter(MaintenanceRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    
    req.status = "COMPLETED"
    req.resolution_notes = resolution_notes
    req.resolved_by = resolved_by
    req.resolved_at = datetime.now()
    
    if downtime_hours:
        req.downtime_hours = Decimal(str(downtime_hours))
    if labor_hours:
        req.labor_hours = Decimal(str(labor_hours))
    if parts_cost:
        req.parts_cost = Decimal(str(parts_cost))
    
    # Calculate total cost (labor at ₹500/hr as example)
    labor_rate = 500
    req.labor_cost = Decimal(str((labor_hours or 0) * labor_rate))
    req.total_cost = (req.parts_cost or 0) + (req.labor_cost or 0)
    
    db.commit()
    
    return {
        "message": "Request completed",
        "request_number": req.request_number,
        "total_cost": float(req.total_cost)
    }


# ═══════════════════════════════════════════════════════════
# SPARE PARTS
# ═══════════════════════════════════════════════════════════

from models.maintenance import SparePart, SparePartsStock, PartsUsage

class SparePartCreate(BaseModel):
    part_code: str
    part_name: str
    description: Optional[str] = None
    category: str = "OTHER"
    equipment_type: Optional[str] = None
    unit: str = "PCS"
    reorder_level: int = 2
    reorder_quantity: int = 5
    current_price: float = 0

class SparePartResponse(BaseModel):
    id: int
    part_code: str
    part_name: str
    category: Optional[str] = None
    unit: str
    reorder_level: int
    current_price: float
    is_active: bool
    
    class Config:
        from_attributes = True


@router.get("/spare-parts")
def list_spare_parts(category: Optional[str] = None, db: Session = Depends(get_db)):
    """List all spare parts with current stock levels."""
    query = db.query(SparePart).filter(SparePart.is_active == True)
    if category:
        query = query.filter(SparePart.category == category)
    
    parts = query.all()
    result = []
    for part in parts:
        stock = db.query(SparePartsStock).filter(SparePartsStock.part_id == part.id).first()
        result.append({
            "id": part.id,
            "part_code": part.part_code,
            "part_name": part.part_name,
            "category": part.category,
            "unit": part.unit,
            "current_price": float(part.current_price or 0),
            "reorder_level": part.reorder_level,
            "current_qty": stock.current_qty if stock else 0,
            "available_qty": stock.available_qty if stock else 0,
            "is_below_reorder": stock.is_below_reorder if stock else False,
            "storage_location": stock.storage_location if stock else None
        })
    return result


@router.get("/spare-parts/low-stock")
def get_low_stock_parts(db: Session = Depends(get_db)):
    """Get parts that are below reorder level."""
    result = db.query(SparePart, SparePartsStock).join(
        SparePartsStock, SparePart.id == SparePartsStock.part_id
    ).filter(SparePartsStock.is_below_reorder == True).all()
    
    parts = []
    for part, stock in result:
        parts.append({
            "id": part.id,
            "part_code": part.part_code,
            "part_name": part.part_name,
            "current_qty": stock.current_qty,
            "reorder_level": part.reorder_level,
            "reorder_quantity": part.reorder_quantity,
            "preferred_vendor_id": part.preferred_vendor_id
        })
    return parts


@router.post("/spare-parts", status_code=status.HTTP_201_CREATED)
def create_spare_part(data: SparePartCreate, db: Session = Depends(get_db)):
    """Create a new spare part."""
    # Check for duplicate
    existing = db.query(SparePart).filter(SparePart.part_code == data.part_code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Part code {data.part_code} already exists")
    
    part = SparePart(
        part_code=data.part_code,
        part_name=data.part_name,
        description=data.description,
        category=data.category,
        equipment_type=data.equipment_type,
        unit=data.unit,
        reorder_level=data.reorder_level,
        reorder_quantity=data.reorder_quantity,
        current_price=Decimal(str(data.current_price))
    )
    db.add(part)
    db.flush()
    
    # Create stock record
    stock = SparePartsStock(part_id=part.id, current_qty=0, available_qty=0, is_below_reorder=True)
    db.add(stock)
    
    db.commit()
    db.refresh(part)
    return {"id": part.id, "part_code": part.part_code, "message": "Part created"}


@router.post("/spare-parts/{part_id}/receive")
def receive_stock(
    part_id: int,
    quantity: int,
    unit_price: Optional[float] = None,
    location: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Receive stock for a spare part (e.g., from PO delivery)."""
    part = db.query(SparePart).filter(SparePart.id == part_id).first()
    if not part:
        raise HTTPException(status_code=404, detail="Spare part not found")
    
    stock = db.query(SparePartsStock).filter(SparePartsStock.part_id == part_id).first()
    if not stock:
        stock = SparePartsStock(part_id=part_id)
        db.add(stock)
    
    stock.current_qty = (stock.current_qty or 0) + quantity
    stock.available_qty = stock.current_qty - (stock.reserved_qty or 0)
    stock.last_received_at = datetime.now()
    if location:
        stock.storage_location = location
    
    # Update reorder alert
    stock.is_below_reorder = stock.current_qty < part.reorder_level
    
    # Update pricing
    if unit_price:
        part.last_purchase_price = part.current_price
        part.current_price = Decimal(str(unit_price))
    
    stock.total_value = Decimal(str(stock.current_qty)) * (part.current_price or 0)
    
    db.commit()
    return {
        "message": f"Received {quantity} {part.unit} of {part.part_name}",
        "new_qty": stock.current_qty,
        "is_below_reorder": stock.is_below_reorder
    }


@router.post("/spare-parts/{part_id}/issue")
def issue_stock(
    part_id: int,
    quantity: int,
    request_id: Optional[int] = None,
    issued_by: str = "Technician",
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Issue stock for maintenance work."""
    part = db.query(SparePart).filter(SparePart.id == part_id).first()
    if not part:
        raise HTTPException(status_code=404, detail="Spare part not found")
    
    stock = db.query(SparePartsStock).filter(SparePartsStock.part_id == part_id).first()
    if not stock or stock.available_qty < quantity:
        raise HTTPException(status_code=400, detail=f"Insufficient stock. Available: {stock.available_qty if stock else 0}")
    
    # Deduct stock
    stock.current_qty -= quantity
    stock.available_qty = stock.current_qty - (stock.reserved_qty or 0)
    stock.last_issued_at = datetime.now()
    stock.is_below_reorder = stock.current_qty < part.reorder_level
    stock.total_value = Decimal(str(stock.current_qty)) * (part.current_price or 0)
    
    # Log usage
    usage = PartsUsage(
        request_id=request_id,
        part_id=part_id,
        quantity=quantity,
        unit_price=part.current_price or 0,
        total_price=(part.current_price or 0) * quantity,
        used_by=issued_by,
        notes=notes
    )
    db.add(usage)
    
    # Update maintenance request parts cost if linked
    if request_id:
        req = db.query(MaintenanceRequest).filter(MaintenanceRequest.id == request_id).first()
        if req:
            req.parts_cost = (req.parts_cost or 0) + usage.total_price
            req.total_cost = (req.parts_cost or 0) + (req.labor_cost or 0)
    
    db.commit()
    return {
        "message": f"Issued {quantity} {part.unit} of {part.part_name}",
        "remaining_qty": stock.current_qty,
        "is_below_reorder": stock.is_below_reorder
    }


@router.get("/spare-parts/summary")
def get_spare_parts_summary(db: Session = Depends(get_db)):
    """Get summary stats for spare parts inventory."""
    total_parts = db.query(SparePart).filter(SparePart.is_active == True).count()
    low_stock = db.query(SparePartsStock).filter(SparePartsStock.is_below_reorder == True).count()
    total_value = db.query(func.sum(SparePartsStock.total_value)).scalar() or 0
    
    return {
        "total_parts": total_parts,
        "low_stock_count": low_stock,
        "total_inventory_value": float(total_value)
    }
