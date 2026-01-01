"""
Tank Farm API Router - Endpoints for storage tanks and transfers.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from decimal import Decimal

from database import get_db
from models.storage_tank import StorageTank, TankType, MaterialType
from models.tank_transfer import TankTransfer, TransferType


router = APIRouter(prefix="/tank-farm", tags=["Tank Farm"])


# ═══════════════════════════════════════════════════════════
# SCHEMAS
# ═══════════════════════════════════════════════════════════

class TankResponse(BaseModel):
    id: int
    tank_code: str
    name: str
    tank_type: str
    material_type: str
    capacity_liters: float
    current_level_liters: float
    current_weight_kg: float
    fill_percentage: float
    available_capacity_liters: float
    is_active: bool
    is_full: bool
    
    class Config:
        from_attributes = True


class CreateTankRequest(BaseModel):
    tank_code: str
    name: str
    tank_type: str = TankType.STORAGE.value
    material_type: str = MaterialType.MIXED_OIL.value
    capacity_liters: float


class TransferRequest(BaseModel):
    source_tank_id: int
    destination_tank_id: Optional[int] = None  # None for dispatch
    quantity_liters: float
    water_removed_liters: float = 0
    transfer_type: str = TransferType.TANK_TO_TANK.value
    customer_name: Optional[str] = None
    vehicle_number: Optional[str] = None
    invoice_number: Optional[str] = None
    notes: Optional[str] = None
    transferred_by: str = "Operator"


class TransferResponse(BaseModel):
    id: int
    transfer_number: str
    source_tank_id: int
    destination_tank_id: Optional[int]
    quantity_liters: float
    water_removed_liters: float
    water_content_pct: Optional[float]
    transfer_type: str
    transfer_datetime: str
    is_completed: bool
    
    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════
# TANK ENDPOINTS
# ═══════════════════════════════════════════════════════════

@router.get("/tanks", response_model=list[TankResponse])
def list_tanks(db: Session = Depends(get_db)):
    """List all storage tanks with current levels."""
    tanks = db.query(StorageTank).filter(StorageTank.is_active == True).order_by(StorageTank.tank_code).all()
    
    return [_tank_to_response(t) for t in tanks]


@router.post("/tanks", response_model=TankResponse, status_code=status.HTTP_201_CREATED)
def create_tank(request: CreateTankRequest, db: Session = Depends(get_db)):
    """Create a new storage tank."""
    tank = StorageTank(
        tank_code=request.tank_code,
        name=request.name,
        tank_type=request.tank_type,
        material_type=request.material_type,
        capacity_liters=Decimal(str(request.capacity_liters)),
        current_level_liters=Decimal("0"),
        current_weight_kg=Decimal("0"),
    )
    db.add(tank)
    db.commit()
    db.refresh(tank)
    
    return _tank_to_response(tank)


@router.get("/tanks/{tank_id}", response_model=TankResponse)
def get_tank(tank_id: int, db: Session = Depends(get_db)):
    """Get tank details."""
    tank = db.query(StorageTank).filter(StorageTank.id == tank_id).first()
    if not tank:
        raise HTTPException(status_code=404, detail="Tank not found")
    return _tank_to_response(tank)


# ═══════════════════════════════════════════════════════════
# TRANSFER ENDPOINTS
# ═══════════════════════════════════════════════════════════

def generate_transfer_number(db: Session) -> str:
    """Generate transfer number: TRF-YYYYMMDD-XXX"""
    from datetime import date
    today = date.today().strftime("%Y%m%d")
    prefix = f"TRF-{today}-"
    
    last = db.query(TankTransfer).filter(
        TankTransfer.transfer_number.like(f"{prefix}%")
    ).order_by(TankTransfer.id.desc()).first()
    
    if last:
        try:
            seq = int(last.transfer_number.split("-")[-1]) + 1
        except:
            seq = 1
    else:
        seq = 1
    
    return f"{prefix}{seq:03d}"


@router.get("/transfers", response_model=list[TransferResponse])
def list_transfers(limit: int = 50, db: Session = Depends(get_db)):
    """List recent tank transfers."""
    transfers = db.query(TankTransfer).order_by(TankTransfer.created_at.desc()).limit(limit).all()
    return [_transfer_to_response(t) for t in transfers]


@router.post("/transfers", response_model=TransferResponse, status_code=status.HTTP_201_CREATED)
def create_transfer(request: TransferRequest, db: Session = Depends(get_db)):
    """
    Transfer oil between tanks.
    
    For settling transfers, water is removed and tracked.
    For dispatch, destination_tank_id is null.
    """
    # Validate source tank
    source = db.query(StorageTank).filter(StorageTank.id == request.source_tank_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source tank not found")
    
    # Check source has enough
    gross_qty = request.quantity_liters + request.water_removed_liters
    if float(source.current_level_liters) < gross_qty:
        raise HTTPException(
            status_code=400, 
            detail=f"Insufficient quantity in source tank. Available: {source.current_level_liters}L"
        )
    
    # Validate destination tank (if not dispatch)
    dest = None
    if request.destination_tank_id:
        dest = db.query(StorageTank).filter(StorageTank.id == request.destination_tank_id).first()
        if not dest:
            raise HTTPException(status_code=404, detail="Destination tank not found")
        
        if request.quantity_liters > dest.available_capacity_liters:
            raise HTTPException(
                status_code=400,
                detail=f"Destination tank cannot accept {request.quantity_liters}L. Available: {dest.available_capacity_liters}L"
            )
    
    # Create transfer record
    transfer = TankTransfer(
        transfer_number=generate_transfer_number(db),
        source_tank_id=request.source_tank_id,
        destination_tank_id=request.destination_tank_id,
        transfer_type=request.transfer_type,
        quantity_liters=Decimal(str(request.quantity_liters)),
        quantity_kg=Decimal(str(request.quantity_liters * 0.85)),  # Approximate
        water_removed_liters=Decimal(str(request.water_removed_liters)),
        transfer_datetime=datetime.now(),
        customer_name=request.customer_name,
        vehicle_number=request.vehicle_number,
        invoice_number=request.invoice_number,
        notes=request.notes,
        transferred_by=request.transferred_by,
        is_completed=True,
    )
    
    # Calculate water percentage
    transfer.calculate_water_percentage(gross_qty)
    
    # Update tank levels
    source.remove_oil(gross_qty)  # Remove gross (includes water)
    
    if dest:
        dest.add_oil(request.quantity_liters)  # Add net oil only
        dest.last_filled_at = datetime.now()
    
    source.last_emptied_at = datetime.now()
    
    db.add(transfer)
    db.commit()
    db.refresh(transfer)
    
    return _transfer_to_response(transfer)


# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════

def _tank_to_response(tank: StorageTank) -> TankResponse:
    return TankResponse(
        id=tank.id,
        tank_code=tank.tank_code,
        name=tank.name,
        tank_type=tank.tank_type,
        material_type=tank.material_type,
        capacity_liters=float(tank.capacity_liters),
        current_level_liters=float(tank.current_level_liters or 0),
        current_weight_kg=float(tank.current_weight_kg or 0),
        fill_percentage=tank.fill_percentage,
        available_capacity_liters=tank.available_capacity_liters,
        is_active=tank.is_active,
        is_full=tank.is_full,
    )


def _transfer_to_response(transfer: TankTransfer) -> TransferResponse:
    return TransferResponse(
        id=transfer.id,
        transfer_number=transfer.transfer_number,
        source_tank_id=transfer.source_tank_id,
        destination_tank_id=transfer.destination_tank_id,
        quantity_liters=float(transfer.quantity_liters),
        water_removed_liters=float(transfer.water_removed_liters or 0),
        water_content_pct=float(transfer.water_content_pct) if transfer.water_content_pct else None,
        transfer_type=transfer.transfer_type,
        transfer_datetime=str(transfer.transfer_datetime),
        is_completed=transfer.is_completed,
    )
