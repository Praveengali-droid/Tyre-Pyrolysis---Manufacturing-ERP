"""
Production Service Layer - Business Logic for Batches.

Contains critical logic for:
1. Starting batches (FIFO inventory consumption)
2. Completing batches (mass balance, tank updates)
3. Electricity cost calculations
"""
from sqlalchemy.orm import Session
from datetime import datetime, date
from decimal import Decimal

from models.reactor import Reactor, ReactorStatus
from models.storage_tank import StorageTank
from models.production_batch import ProductionBatch, BatchStatus
from models.inventory_lot import InventoryLot
from config import get_settings

settings = get_settings()


def generate_batch_number(db: Session) -> str:
    """Generate batch number: BATCH-YYYYMMDD-XXX"""
    today = date.today().strftime("%Y%m%d")
    prefix = f"BATCH-{today}-"
    
    last = db.query(ProductionBatch).filter(
        ProductionBatch.batch_number.like(f"{prefix}%")
    ).order_by(ProductionBatch.id.desc()).first()
    
    if last:
        try:
            seq = int(last.batch_number.split("-")[-1]) + 1
        except:
            seq = 1
    else:
        seq = 1
    
    return f"{prefix}{seq:03d}"


def get_available_lots(db: Session, limit: int = 20):
    """
    Get available inventory lots in FIFO order (oldest first).
    Only returns lots with remaining quantity.
    """
    lots = db.query(InventoryLot).filter(
        InventoryLot.is_active == True,
        InventoryLot.is_exhausted == False,
        InventoryLot.current_qty_kg > 0
    ).order_by(InventoryLot.receipt_date.asc()).limit(limit).all()
    
    return lots


def start_batch(
    db: Session,
    reactor_id: int,
    input_lot_id: int,
    input_weight_kg: float,
    meter_start: float,
    started_by: str = "Operator",
    recipe_id: int = None
) -> ProductionBatch:
    """
    Start a new production batch.
    
    1. Validates reactor is available
    2. Deducts input from inventory lot (FIFO)
    3. Sets reactor to LOADING status
    4. Creates batch record with recipe if provided
    
    Args:
        reactor_id: Reactor to use
        input_lot_id: Inventory lot to consume from
        input_weight_kg: Amount to consume
        meter_start: Electricity meter reading at start
        started_by: Operator name
        recipe_id: Optional recipe for stage tracking
        
    Raises:
        ValueError: If reactor unavailable or insufficient lot qty
    """
    from models.batch_recipe import BatchRecipe
    from models.recipe_stage import RecipeStage
    from datetime import timedelta
    from models.maintenance import MaintenanceRequest
    
    # 1. Validate reactor
    reactor = db.query(Reactor).filter(Reactor.id == reactor_id).first()
    if not reactor:
        raise ValueError(f"Reactor {reactor_id} not found")
    
    if not reactor.is_available:
        raise ValueError(f"Reactor {reactor.reactor_code} is not available (status: {reactor.status})")
    
    # SAFETY INTERLOCK: Check maintenance due
    if reactor.maintenance_due:
        raise ValueError(
            f"SAFETY LOCK: Maintenance Due! Reactor {reactor.reactor_code} has run "
            f"{reactor.batches_since_last_cleaning} batches since last cleaning "
            f"(limit: {reactor.maintenance_frequency}). Complete Carbon Cleaning maintenance first."
        )
    
    # SAFETY INTERLOCK: Check for unresolved CRITICAL BREAKDOWN requests
    critical_breakdown = db.query(MaintenanceRequest).filter(
        MaintenanceRequest.reactor_id == reactor_id,
        MaintenanceRequest.request_type == "BREAKDOWN",
        MaintenanceRequest.priority.in_(["CRITICAL", "HIGH"]),
        MaintenanceRequest.status.in_(["OPEN", "IN_PROGRESS", "ON_HOLD"])
    ).first()
    
    if critical_breakdown:
        raise ValueError(
            f"SAFETY LOCK: Active Breakdown! Reactor {reactor.reactor_code} has unresolved "
            f"{critical_breakdown.priority} breakdown request: '{critical_breakdown.title}' "
            f"(Status: {critical_breakdown.status}). Resolve maintenance request before starting batch."
        )
    
    if input_weight_kg > float(reactor.capacity_kg):
        raise ValueError(f"Input {input_weight_kg}kg exceeds reactor capacity {reactor.capacity_kg}kg")
    
    # 2. Validate and consume from lot
    lot = db.query(InventoryLot).filter(InventoryLot.id == input_lot_id).first()
    if not lot:
        raise ValueError(f"Inventory lot {input_lot_id} not found")
    
    if float(lot.current_qty_kg) < input_weight_kg:
        raise ValueError(f"Insufficient qty in lot. Available: {lot.current_qty_kg}kg, Requested: {input_weight_kg}kg")
    
    # Consume from lot
    lot.consume(input_weight_kg)
    
    # 3. Update reactor status
    reactor.status = ReactorStatus.LOADING.value
    
    # 4. Get recipe info if provided
    first_stage = None
    expected_end = None
    
    if recipe_id:
        recipe = db.query(BatchRecipe).filter(BatchRecipe.id == recipe_id).first()
        if recipe:
            # Get first stage
            first_stage = db.query(RecipeStage).filter(
                RecipeStage.recipe_id == recipe_id
            ).order_by(RecipeStage.order_sequence).first()
            
            # Calculate expected end time
            if recipe.total_duration_minutes:
                expected_end = datetime.now() + timedelta(minutes=recipe.total_duration_minutes)
    
    # 5. Create batch
    batch = ProductionBatch(
        batch_number=generate_batch_number(db),
        reactor_id=reactor_id,
        recipe_id=recipe_id,
        status=BatchStatus.LOADING.value,
        input_lot_id=input_lot_id,
        input_weight_kg=Decimal(str(input_weight_kg)),
        batch_date=date.today(),
        start_datetime=datetime.now(),
        meter_start=Decimal(str(meter_start)),
        electricity_rate=Decimal(str(settings.DEFAULT_ELECTRICITY_RATE)),
        started_by=started_by,
        current_stage=first_stage.stage_name if first_stage else "Loading",
        current_stage_sequence=first_stage.order_sequence if first_stage else 1,
        current_stage_start=datetime.now(),
        expected_end_time=expected_end,
    )
    
    db.add(batch)
    db.flush()
    
    # Link reactor to batch
    reactor.current_batch_id = batch.id
    
    db.commit()
    db.refresh(batch)
    
    return batch


def update_reactor_status(db: Session, reactor_id: int, new_status: str) -> Reactor:
    """Update reactor status during production."""
    reactor = db.query(Reactor).filter(Reactor.id == reactor_id).first()
    if not reactor:
        raise ValueError(f"Reactor {reactor_id} not found")
    
    reactor.status = new_status
    db.commit()
    db.refresh(reactor)
    
    return reactor


def complete_batch(
    db: Session,
    batch_id: int,
    oil_output_kg: float,
    carbon_output_kg: float,
    steel_output_kg: float,
    destination_tank_id: int,
    meter_end: float,
    oil_quality_grade: str = None,
    carbon_quality_grade: str = None,
    quality_notes: str = None,
    completed_by: str = "Operator"
) -> ProductionBatch:
    """
    Complete a production batch.
    
    Critical validations:
    1. Destination tank MUST be provided for oil
    2. Total outputs cannot exceed input (mass balance)
    3. Syn gas loss is calculated automatically
    
    Actions:
    1. Validate mass balance
    2. Calculate syn gas loss
    3. Calculate electricity used
    4. Add oil to destination tank
    5. Set reactor to IDLE
    6. Mark batch COMPLETED
    
    Raises:
        ValueError: If validation fails
    """
    batch = db.query(ProductionBatch).filter(ProductionBatch.id == batch_id).first()
    if not batch:
        raise ValueError(f"Batch {batch_id} not found")
    
    if batch.status == BatchStatus.COMPLETED.value:
        raise ValueError("Batch is already completed")
    
    # 1. Validate destination tank
    if not destination_tank_id:
        raise ValueError("Destination tank ID is REQUIRED to complete batch")
    
    tank = db.query(StorageTank).filter(StorageTank.id == destination_tank_id).first()
    if not tank:
        raise ValueError(f"Destination tank {destination_tank_id} not found")
    
    # 2. Validate mass balance
    total_output = oil_output_kg + carbon_output_kg + steel_output_kg
    input_weight = float(batch.input_weight_kg)
    
    if total_output > input_weight:
        raise ValueError(
            f"Mass balance violation: Outputs ({total_output}kg) exceed input ({input_weight}kg)"
        )
    
    # 3. Record outputs
    batch.oil_output_kg = Decimal(str(oil_output_kg))
    batch.carbon_output_kg = Decimal(str(carbon_output_kg))
    batch.steel_output_kg = Decimal(str(steel_output_kg))
    batch.destination_tank_id = destination_tank_id
    batch.meter_end = Decimal(str(meter_end))
    
    # 4. Calculate derived values
    batch.calculate_outputs()  # syn_gas_loss, yields
    batch.calculate_electricity()  # kWh, cost
    oil_liters = batch.convert_oil_to_liters()  # kg to liters
    
    # 5. Add oil to tank
    if oil_liters > 0:
        if not tank.add_oil(oil_liters, oil_output_kg):
            raise ValueError(f"Tank {tank.tank_code} cannot accept {oil_liters}L (capacity issue)")
        tank.last_filled_at = datetime.now()
    
    # 6. Update quality info
    batch.oil_quality_grade = oil_quality_grade
    batch.carbon_quality_grade = carbon_quality_grade
    batch.quality_notes = quality_notes
    batch.completed_by = completed_by
    batch.end_datetime = datetime.now()
    batch.status = BatchStatus.COMPLETED.value
    batch.current_stage = "Completed"  # Mark stage as completed
    
    # 7. Free up reactor and INCREMENT MAINTENANCE COUNTER
    reactor = db.query(Reactor).filter(Reactor.id == batch.reactor_id).first()
    if reactor:
        reactor.status = ReactorStatus.IDLE.value
        reactor.current_batch_id = None
        reactor.total_batches_processed = (reactor.total_batches_processed or 0) + 1
        # Increment maintenance counter (for safety interlock)
        reactor.batches_since_last_cleaning = (reactor.batches_since_last_cleaning or 0) + 1
    
    db.commit()
    db.refresh(batch)
    
    return batch
