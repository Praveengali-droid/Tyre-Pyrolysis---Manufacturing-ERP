"""
Production API Router - Endpoints for reactor and batch management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel
from decimal import Decimal

from database import get_db
from models.reactor import Reactor, ReactorStatus
from models.production_batch import ProductionBatch, BatchStatus
from models.inventory_lot import InventoryLot
from models.storage_tank import StorageTank
from models.batch_recipe import BatchRecipe
from models.recipe_stage import RecipeStage
from models.batch_log_entry import BatchLogEntry
from modules.production import service


router = APIRouter(prefix="/production", tags=["Production"])


# ═══════════════════════════════════════════════════════════
# SCHEMAS
# ═══════════════════════════════════════════════════════════

class ReactorResponse(BaseModel):
    id: int
    reactor_code: str
    name: str
    capacity_kg: float
    status: str
    status_color: str
    is_available: bool
    current_batch_id: Optional[int]
    total_batches_processed: int
    
    class Config:
        from_attributes = True


class LotResponse(BaseModel):
    id: int
    lot_id: str
    vendor_id: int
    receipt_date: date
    received_qty_kg: float
    current_qty_kg: float
    rate_per_kg: float
    
    class Config:
        from_attributes = True


class StartBatchRequest(BaseModel):
    reactor_id: int
    recipe_id: Optional[int] = None  # Link to BatchRecipe for process tracking
    input_lot_id: int
    input_weight_kg: float
    meter_start: float
    started_by: str = "Operator"


class CompleteBatchRequest(BaseModel):
    oil_output_kg: float
    carbon_output_kg: float
    steel_output_kg: float
    destination_tank_id: int
    meter_end: float
    oil_quality_grade: Optional[str] = None
    carbon_quality_grade: Optional[str] = None
    quality_notes: Optional[str] = None
    completed_by: str = "Operator"


class BatchResponse(BaseModel):
    id: int
    batch_number: str
    reactor_id: int
    recipe_id: Optional[int] = None
    status: str
    current_stage: Optional[str] = None
    current_stage_sequence: Optional[int] = None
    expected_end_time: Optional[str] = None
    input_weight_kg: float
    batch_date: date
    start_datetime: Optional[str]
    end_datetime: Optional[str]
    oil_output_kg: Optional[float]
    carbon_output_kg: Optional[float]
    steel_output_kg: Optional[float]
    syn_gas_loss_kg: Optional[float]
    oil_yield_pct: Optional[float]
    carbon_yield_pct: Optional[float]
    steel_yield_pct: Optional[float]
    loss_pct: Optional[float]
    electricity_used_kwh: Optional[float]
    electricity_cost: Optional[float]
    destination_tank_id: Optional[int]
    
    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════
# REACTOR ENDPOINTS
# ═══════════════════════════════════════════════════════════

@router.get("/reactors", response_model=list[ReactorResponse])
def list_reactors(db: Session = Depends(get_db)):
    """List all reactors with status."""
    reactors = db.query(Reactor).filter(Reactor.is_active == True).order_by(Reactor.reactor_code).all()
    
    return [
        ReactorResponse(
            id=r.id,
            reactor_code=r.reactor_code,
            name=r.name,
            capacity_kg=float(r.capacity_kg),
            status=r.status,
            status_color=r.status_color,
            is_available=r.is_available,
            current_batch_id=r.current_batch_id,
            total_batches_processed=r.total_batches_processed or 0,
        )
        for r in reactors
    ]


@router.post("/reactors", response_model=ReactorResponse, status_code=status.HTTP_201_CREATED)
def create_reactor(
    reactor_code: str,
    name: str,
    capacity_kg: float,
    db: Session = Depends(get_db)
):
    """Create a new reactor."""
    # Check for duplicate reactor code
    existing = db.query(Reactor).filter(Reactor.reactor_code == reactor_code).first()
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"Reactor with code '{reactor_code}' already exists"
        )
    
    try:
        reactor = Reactor(
            reactor_code=reactor_code,
            name=name,
            capacity_kg=Decimal(str(capacity_kg)),
            status=ReactorStatus.IDLE.value,
        )
        db.add(reactor)
        db.commit()
        db.refresh(reactor)
        
        return ReactorResponse(
            id=reactor.id,
            reactor_code=reactor.reactor_code,
            name=reactor.name,
            capacity_kg=float(reactor.capacity_kg),
            status=reactor.status,
            status_color=reactor.status_color,
            is_available=reactor.is_available,
            current_batch_id=reactor.current_batch_id,
            total_batches_processed=reactor.total_batches_processed or 0,
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to create reactor: {str(e)}")


@router.put("/reactors/{reactor_id}/status")
def update_reactor_status(
    reactor_id: int,
    new_status: str,
    db: Session = Depends(get_db)
):
    """Update reactor status during production."""
    try:
        reactor = service.update_reactor_status(db, reactor_id, new_status)
        return {"message": f"Reactor updated to {new_status}", "reactor_id": reactor_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ═══════════════════════════════════════════════════════════
# INVENTORY LOT ENDPOINTS (for batch input selection)
# ═══════════════════════════════════════════════════════════

@router.get("/lots/available", response_model=list[LotResponse])
def list_available_lots(db: Session = Depends(get_db)):
    """Get available inventory lots in FIFO order (oldest first)."""
    lots = service.get_available_lots(db)
    
    return [
        LotResponse(
            id=lot.id,
            lot_id=lot.lot_id,
            vendor_id=lot.vendor_id,
            receipt_date=lot.receipt_date,
            received_qty_kg=float(lot.received_qty_kg),
            current_qty_kg=float(lot.current_qty_kg),
            rate_per_kg=float(lot.rate_per_kg),
        )
        for lot in lots
    ]


# ═══════════════════════════════════════════════════════════
# BATCH ENDPOINTS
# ═══════════════════════════════════════════════════════════

@router.get("/batches", response_model=list[BatchResponse])
def list_batches(
    status_filter: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List production batches."""
    query = db.query(ProductionBatch)
    
    if status_filter:
        query = query.filter(ProductionBatch.status == status_filter)
    
    batches = query.order_by(ProductionBatch.created_at.desc()).limit(limit).all()
    
    return [_batch_to_response(b) for b in batches]


@router.get("/batches/{batch_id}", response_model=BatchResponse)
def get_batch(batch_id: int, db: Session = Depends(get_db)):
    """Get batch details."""
    batch = db.query(ProductionBatch).filter(ProductionBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return _batch_to_response(batch)


@router.post("/batches/start", response_model=BatchResponse, status_code=status.HTTP_201_CREATED)
def start_batch(request: StartBatchRequest, db: Session = Depends(get_db)):
    """
    Start a new production batch.
    
    - Validates reactor is available
    - Deducts from inventory lot (FIFO)
    - Sets reactor to LOADING
    """
    try:
        batch = service.start_batch(
            db=db,
            reactor_id=request.reactor_id,
            input_lot_id=request.input_lot_id,
            input_weight_kg=request.input_weight_kg,
            meter_start=request.meter_start,
            started_by=request.started_by,
            recipe_id=request.recipe_id,
        )
        return _batch_to_response(batch)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/batches/{batch_id}/complete", response_model=BatchResponse)
def complete_batch(
    batch_id: int,
    request: CompleteBatchRequest,
    db: Session = Depends(get_db)
):
    """
    Complete a production batch.
    
    REQUIRED: destination_tank_id for oil output
    
    Validates:
    - Mass balance: outputs <= input
    
    Calculates:
    - syn_gas_loss = input - (oil + carbon + steel)
    - Yield percentages
    - Electricity cost
    
    Updates:
    - Tank current_level with oil output
    - Reactor status to IDLE
    """
    try:
        batch = service.complete_batch(
            db=db,
            batch_id=batch_id,
            oil_output_kg=request.oil_output_kg,
            carbon_output_kg=request.carbon_output_kg,
            steel_output_kg=request.steel_output_kg,
            destination_tank_id=request.destination_tank_id,
            meter_end=request.meter_end,
            oil_quality_grade=request.oil_quality_grade,
            carbon_quality_grade=request.carbon_quality_grade,
            quality_notes=request.quality_notes,
            completed_by=request.completed_by,
        )
        return _batch_to_response(batch)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


def _batch_to_response(batch: ProductionBatch) -> BatchResponse:
    """Convert batch model to response."""
    return BatchResponse(
        id=batch.id,
        batch_number=batch.batch_number,
        reactor_id=batch.reactor_id,
        recipe_id=batch.recipe_id,
        status=batch.status,
        current_stage=batch.current_stage,
        current_stage_sequence=batch.current_stage_sequence,
        expected_end_time=str(batch.expected_end_time) if batch.expected_end_time else None,
        input_weight_kg=float(batch.input_weight_kg),
        batch_date=batch.batch_date,
        start_datetime=str(batch.start_datetime) if batch.start_datetime else None,
        end_datetime=str(batch.end_datetime) if batch.end_datetime else None,
        oil_output_kg=float(batch.oil_output_kg) if batch.oil_output_kg else None,
        carbon_output_kg=float(batch.carbon_output_kg) if batch.carbon_output_kg else None,
        steel_output_kg=float(batch.steel_output_kg) if batch.steel_output_kg else None,
        syn_gas_loss_kg=float(batch.syn_gas_loss_kg) if batch.syn_gas_loss_kg else None,
        oil_yield_pct=float(batch.oil_yield_pct) if batch.oil_yield_pct else None,
        carbon_yield_pct=float(batch.carbon_yield_pct) if batch.carbon_yield_pct else None,
        steel_yield_pct=float(batch.steel_yield_pct) if batch.steel_yield_pct else None,
        loss_pct=float(batch.loss_pct) if batch.loss_pct else None,
        electricity_used_kwh=float(batch.electricity_used_kwh) if batch.electricity_used_kwh else None,
        electricity_cost=float(batch.electricity_cost) if batch.electricity_cost else None,
        destination_tank_id=batch.destination_tank_id,
    )


# ═══════════════════════════════════════════════════════════
# RECIPE SCHEMAS
# ═══════════════════════════════════════════════════════════

class RecipeStageInput(BaseModel):
    stage_name: str
    order_sequence: int
    duration_minutes: int = 60
    required_readings: List[str] = []  # ["temp_c", "pressure_bar", "meter_kwh"]
    safe_limits: dict = {}  # {"temp_c": {"min": 0, "max": 450}}
    target_values: dict = {}
    instructions: Optional[str] = None


class RecipeCreateRequest(BaseModel):
    recipe_code: str
    name: str
    description: Optional[str] = None
    tyre_type: Optional[str] = None
    is_default: bool = False
    stages: List[RecipeStageInput] = []


class RecipeResponse(BaseModel):
    id: int
    recipe_code: str
    name: str
    description: Optional[str]
    tyre_type: Optional[str]
    total_duration_minutes: int
    stage_count: int
    is_default: bool
    is_active: bool
    
    class Config:
        from_attributes = True


class LogEntryRequest(BaseModel):
    readings: dict  # {"temp_c": 350, "pressure_bar": 0.2}
    operator_name: str = "Operator"
    notes: Optional[str] = None


class LogEntryResponse(BaseModel):
    id: int
    batch_id: int
    stage_name: str
    log_datetime: str
    readings: dict
    is_within_limits: bool
    alerts: List[str]
    operator_name: Optional[str]
    notes: Optional[str]
    
    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════
# RECIPE ENDPOINTS
# ═══════════════════════════════════════════════════════════

@router.get("/recipes")
def list_recipes(db: Session = Depends(get_db)):
    """List all production recipes."""
    recipes = db.query(BatchRecipe).filter(BatchRecipe.is_active == True).all()
    return [
        RecipeResponse(
            id=r.id,
            recipe_code=r.recipe_code,
            name=r.name,
            description=r.description,
            tyre_type=r.tyre_type,
            total_duration_minutes=r.total_duration_minutes or 0,
            stage_count=r.stage_count or 0,
            is_default=r.is_default,
            is_active=r.is_active,
        )
        for r in recipes
    ]


@router.post("/recipes", status_code=status.HTTP_201_CREATED)
def create_recipe(request: RecipeCreateRequest, db: Session = Depends(get_db)):
    """Create a new recipe with stages."""
    recipe = BatchRecipe(
        recipe_code=request.recipe_code,
        name=request.name,
        description=request.description,
        tyre_type=request.tyre_type,
        is_default=request.is_default,
    )
    db.add(recipe)
    db.flush()
    
    # Add stages
    total_duration = 0
    for stage_input in request.stages:
        stage = RecipeStage(
            recipe_id=recipe.id,
            stage_name=stage_input.stage_name,
            order_sequence=stage_input.order_sequence,
            duration_minutes=stage_input.duration_minutes,
            required_readings=stage_input.required_readings,
            safe_limits=stage_input.safe_limits,
            target_values=stage_input.target_values,
            instructions=stage_input.instructions,
        )
        db.add(stage)
        total_duration += stage_input.duration_minutes
    
    recipe.total_duration_minutes = total_duration
    recipe.stage_count = len(request.stages)
    
    db.commit()
    db.refresh(recipe)
    
    return {"message": "Recipe created", "recipe_id": recipe.id}


@router.get("/recipes/{recipe_id}")
def get_recipe(recipe_id: int, db: Session = Depends(get_db)):
    """Get recipe with all stages."""
    recipe = db.query(BatchRecipe).filter(BatchRecipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    stages = db.query(RecipeStage).filter(
        RecipeStage.recipe_id == recipe_id
    ).order_by(RecipeStage.order_sequence).all()
    
    return {
        "id": recipe.id,
        "recipe_code": recipe.recipe_code,
        "name": recipe.name,
        "description": recipe.description,
        "tyre_type": recipe.tyre_type,
        "total_duration_minutes": recipe.total_duration_minutes,
        "is_default": recipe.is_default,
        "stages": [
            {
                "id": s.id,
                "stage_name": s.stage_name,
                "order_sequence": s.order_sequence,
                "duration_minutes": s.duration_minutes,
                "required_readings": s.required_readings or [],
                "safe_limits": s.safe_limits or {},
                "target_values": s.target_values or {},
                "instructions": s.instructions,
            }
            for s in stages
        ]
    }


# ═══════════════════════════════════════════════════════════
# LOG ENTRY ENDPOINTS
# ═══════════════════════════════════════════════════════════

@router.post("/batches/{batch_id}/log-entry", status_code=status.HTTP_201_CREATED)
def add_log_entry(
    batch_id: int,
    request: LogEntryRequest,
    db: Session = Depends(get_db)
):
    """
    Add an operator log entry for a batch.
    
    Validates readings against safe_limits and returns alerts if out of range.
    """
    batch = db.query(ProductionBatch).filter(ProductionBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    if batch.status == BatchStatus.COMPLETED.value:
        raise HTTPException(status_code=400, detail="Cannot add logs to completed batch")
    
    # Get current stage safe limits
    alerts = []
    is_within_limits = True
    
    if batch.recipe_id and batch.current_stage:
        stage = db.query(RecipeStage).filter(
            RecipeStage.recipe_id == batch.recipe_id,
            RecipeStage.stage_name == batch.current_stage
        ).first()
        
        if stage:
            is_within_limits, alerts = stage.check_reading_limits(request.readings)
    
    log_entry = BatchLogEntry(
        batch_id=batch_id,
        stage_name=batch.current_stage or batch.status,
        stage_sequence=batch.current_stage_sequence,
        readings=request.readings,
        is_within_limits=is_within_limits,
        alerts=alerts,
        operator_name=request.operator_name,
        notes=request.notes,
        entry_type="MANUAL",
    )
    
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    
    return {
        "id": log_entry.id,
        "is_within_limits": is_within_limits,
        "alerts": alerts,
        "message": "Warning: Values out of range!" if alerts else "Log entry recorded"
    }


@router.get("/batches/{batch_id}/logs")
def get_batch_logs(batch_id: int, db: Session = Depends(get_db)):
    """Get all log entries for a batch."""
    logs = db.query(BatchLogEntry).filter(
        BatchLogEntry.batch_id == batch_id
    ).order_by(BatchLogEntry.log_datetime.desc()).all()
    
    return [
        LogEntryResponse(
            id=log.id,
            batch_id=log.batch_id,
            stage_name=log.stage_name,
            log_datetime=str(log.log_datetime),
            readings=log.readings or {},
            is_within_limits=log.is_within_limits,
            alerts=log.alerts or [],
            operator_name=log.operator_name,
            notes=log.notes,
        )
        for log in logs
    ]


# ═══════════════════════════════════════════════════════════
# HOLD / RESUME ENDPOINTS
# ═══════════════════════════════════════════════════════════

@router.put("/batches/{batch_id}/hold")
def hold_batch(
    batch_id: int,
    reason: str = "Maintenance",
    db: Session = Depends(get_db)
):
    """
    Put batch on hold (pauses expected end time countdown).
    
    Use for power cuts or maintenance breaks.
    """
    batch = db.query(ProductionBatch).filter(ProductionBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    if batch.status == BatchStatus.COMPLETED.value:
        raise HTTPException(status_code=400, detail="Cannot hold completed batch")
    
    if batch.status == BatchStatus.ON_HOLD.value:
        raise HTTPException(status_code=400, detail="Batch is already on hold")
    
    batch.hold_datetime = datetime.now()
    batch.hold_reason = reason
    batch.status = BatchStatus.ON_HOLD.value
    
    db.commit()
    
    return {"message": f"Batch {batch.batch_number} is now ON_HOLD", "reason": reason}


@router.put("/batches/{batch_id}/resume")
def resume_batch(batch_id: int, db: Session = Depends(get_db)):
    """
    Resume batch from hold and adjust expected end time.
    """
    batch = db.query(ProductionBatch).filter(ProductionBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    if batch.status != BatchStatus.ON_HOLD.value:
        raise HTTPException(status_code=400, detail="Batch is not on hold")
    
    # Calculate hold duration
    if batch.hold_datetime:
        hold_duration = (datetime.now() - batch.hold_datetime).total_seconds() / 60
        batch.total_hold_minutes = (batch.total_hold_minutes or 0) + int(hold_duration)
        
        # Extend expected end time
        if batch.expected_end_time:
            from datetime import timedelta
            batch.expected_end_time = batch.expected_end_time + timedelta(minutes=int(hold_duration))
    
    batch.status = BatchStatus.IN_PROGRESS.value
    batch.hold_datetime = None
    batch.hold_reason = None
    
    db.commit()
    
    return {"message": f"Batch {batch.batch_number} resumed", "hold_minutes_added": batch.total_hold_minutes}


# ═══════════════════════════════════════════════════════════
# ADVANCE STAGE ENDPOINT (with Safety Interlock)
# ═══════════════════════════════════════════════════════════

@router.put("/batches/{batch_id}/advance-stage")
def advance_stage(batch_id: int, db: Session = Depends(get_db)):
    """
    Advance batch to next stage.
    
    SAFETY INTERLOCK: Cannot advance to UNLOADING if latest temp reading > safe limit.
    """
    batch = db.query(ProductionBatch).filter(ProductionBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    if not batch.recipe_id:
        raise HTTPException(status_code=400, detail="Batch has no recipe assigned")
    
    # Get current and next stage
    current_seq = batch.current_stage_sequence or 0
    next_stage = db.query(RecipeStage).filter(
        RecipeStage.recipe_id == batch.recipe_id,
        RecipeStage.order_sequence == current_seq + 1
    ).first()
    
    if not next_stage:
        raise HTTPException(status_code=400, detail="No more stages. Complete the batch instead.")
    
    # SAFETY INTERLOCK: Check if advancing to Unloading
    if next_stage.is_unloading:
        # Get latest log entry with temp reading
        latest_log = db.query(BatchLogEntry).filter(
            BatchLogEntry.batch_id == batch_id
        ).order_by(BatchLogEntry.log_datetime.desc()).first()
        
        if latest_log and latest_log.readings:
            temp = latest_log.readings.get("temp_c", 0)
            
            # Get safe limit for unloading (default 60°C)
            safe_max = 60
            if next_stage.safe_limits and "temp_c" in next_stage.safe_limits:
                safe_max = next_stage.safe_limits["temp_c"].get("max", 60)
            
            if temp > safe_max:
                raise HTTPException(
                    status_code=400,
                    detail=f"⚠️ SAFETY HAZARD: Temperature {temp}°C exceeds safe limit {safe_max}°C for Unloading. Cool down reactor first."
                )
    
    # Advance to next stage
    batch.current_stage = next_stage.stage_name
    batch.current_stage_sequence = next_stage.order_sequence
    batch.current_stage_start = datetime.now()
    batch.status = BatchStatus.IN_PROGRESS.value  # Ensure batch is marked as in-progress
    
    # Update reactor status based on stage
    stage_to_reactor_status = {
        "loading": ReactorStatus.LOADING.value,
        "heating": ReactorStatus.HEATING.value,
        "distillation": ReactorStatus.DISTILLATION.value,
        "cooling": ReactorStatus.COOLING.value,
        "unloading": ReactorStatus.UNLOADING.value,
    }
    
    reactor = db.query(Reactor).filter(Reactor.id == batch.reactor_id).first()
    if reactor:
        new_status = stage_to_reactor_status.get(next_stage.stage_name.lower(), ReactorStatus.IN_PROGRESS.value if hasattr(ReactorStatus, 'IN_PROGRESS') else reactor.status)
        reactor.status = new_status
    
    db.commit()
    
    return {
        "message": f"Advanced to stage: {next_stage.stage_name}",
        "current_stage": next_stage.stage_name,
        "stage_sequence": next_stage.order_sequence,
        "duration_minutes": next_stage.duration_minutes,
        "required_readings": next_stage.required_readings or []
    }


# ═══════════════════════════════════════════════════════════
# TIMELINE ENDPOINT
# ═══════════════════════════════════════════════════════════

@router.get("/batches/{batch_id}/timeline")
def get_batch_timeline(batch_id: int, db: Session = Depends(get_db)):
    """
    Get batch timeline for UI progress tracking and alerts.
    
    Returns:
        - Current stage progress
        - Time remaining
        - Is nearly done (< 15 mins)
        - Next stage info
    """
    batch = db.query(ProductionBatch).filter(ProductionBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    time_remaining_mins = None
    is_nearly_done = False
    stage_progress_mins = 0
    next_stage = None
    required_readings = []
    
    # Calculate time remaining
    if batch.expected_end_time:
        remaining = (batch.expected_end_time - datetime.now()).total_seconds() / 60
        time_remaining_mins = max(0, int(remaining))
        is_nearly_done = time_remaining_mins <= 15
    
    # Calculate stage progress
    if batch.current_stage_start:
        stage_progress_mins = int((datetime.now() - batch.current_stage_start).total_seconds() / 60)
    
    # Get next stage info
    if batch.recipe_id and batch.current_stage_sequence:
        current_stage = db.query(RecipeStage).filter(
            RecipeStage.recipe_id == batch.recipe_id,
            RecipeStage.order_sequence == batch.current_stage_sequence
        ).first()
        
        if current_stage:
            required_readings = current_stage.required_readings or []
        
        next_stage_obj = db.query(RecipeStage).filter(
            RecipeStage.recipe_id == batch.recipe_id,
            RecipeStage.order_sequence == batch.current_stage_sequence + 1
        ).first()
        
        if next_stage_obj:
            next_stage = {
                "name": next_stage_obj.stage_name,
                "duration_minutes": next_stage_obj.duration_minutes
            }
    
    return {
        "batch_id": batch_id,
        "batch_number": batch.batch_number,
        "current_stage": batch.current_stage,
        "stage_progress_mins": stage_progress_mins,
        "time_remaining_mins": time_remaining_mins,
        "expected_end_time": str(batch.expected_end_time) if batch.expected_end_time else None,
        "is_nearly_done": is_nearly_done,
        "required_readings": required_readings,
        "next_stage": next_stage,
        "status": batch.status
    }


# ═══════════════════════════════════════════════════════════
# PRODUCTION SUMMARY ENDPOINT
# ═══════════════════════════════════════════════════════════

@router.get("/summary")
def get_production_summary(db: Session = Depends(get_db)):
    """
    Get production summary for dashboard widgets.
    
    Returns:
        - Active batches count
        - Total oil in tanks (liters)
        - Total carbon stock (kg) = produced - dispatched
        - Total steel stock (kg) = produced - dispatched
    """
    from sqlalchemy import func
    from models.output_dispatch import CarbonDispatch, SteelDispatch
    
    # Active batches
    active_batches = db.query(func.count(ProductionBatch.id)).filter(
        ProductionBatch.status.in_([
            BatchStatus.LOADING.value,
            BatchStatus.IN_PROGRESS.value,
            BatchStatus.ON_HOLD.value
        ])
    ).scalar() or 0
    
    # Total oil in tanks
    oil_in_tanks = db.query(func.sum(StorageTank.current_level_liters)).filter(
        StorageTank.is_active == True
    ).scalar() or 0
    
    # Carbon: produced - dispatched
    carbon_produced = db.query(func.sum(ProductionBatch.carbon_output_kg)).filter(
        ProductionBatch.status == BatchStatus.COMPLETED.value
    ).scalar() or 0
    
    carbon_dispatched = db.query(func.sum(CarbonDispatch.quantity_kg)).scalar() or 0
    carbon_stock = float(carbon_produced) - float(carbon_dispatched)
    
    # Steel: produced - dispatched
    steel_produced = db.query(func.sum(ProductionBatch.steel_output_kg)).filter(
        ProductionBatch.status == BatchStatus.COMPLETED.value
    ).scalar() or 0
    
    steel_dispatched = db.query(func.sum(SteelDispatch.quantity_kg)).scalar() or 0
    steel_stock = float(steel_produced) - float(steel_dispatched)
    
    return {
        "active_batches": active_batches,
        "oil_in_tanks_liters": float(oil_in_tanks),
        "carbon_stock_kg": max(0, carbon_stock),
        "steel_stock_kg": max(0, steel_stock)
    }
