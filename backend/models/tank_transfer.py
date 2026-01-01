"""
Tank Transfer Model - Oil Movement Between Tanks.

Handles transfers from settling tanks to sales tanks,
including water removal during the settling process.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, Boolean
from sqlalchemy.sql import func
from database import Base
from decimal import Decimal
from enum import Enum


class TransferType(str, Enum):
    """Type of tank transfer."""
    SETTLING_TO_STORAGE = "SETTLING_TO_STORAGE"
    STORAGE_TO_SALES = "STORAGE_TO_SALES"
    TANK_TO_TANK = "TANK_TO_TANK"
    DISPATCH = "DISPATCH"  # Outgoing to customer


class TankTransfer(Base):
    """
    Record of oil transfer between tanks.
    
    During settling, water is separated and removed.
    This tracks the net oil transferred after water removal.
    """
    __tablename__ = "tank_transfers"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Transfer Identity
    transfer_number = Column(String(30), unique=True, nullable=False, index=True)  # TRF-20251231-001
    
    # Source & Destination
    source_tank_id = Column(Integer, ForeignKey("storage_tanks.id"), nullable=False)
    destination_tank_id = Column(Integer, ForeignKey("storage_tanks.id"), nullable=True)  # Null for DISPATCH
    
    # Transfer Type
    transfer_type = Column(String(30), default=TransferType.TANK_TO_TANK.value)
    
    # Quantities
    quantity_liters = Column(Numeric(12, 2), nullable=False)  # Net oil transferred
    quantity_kg = Column(Numeric(12, 2), nullable=True)
    
    # Water Removal (for settling transfers)
    water_removed_liters = Column(Numeric(10, 2), default=0)
    water_content_pct = Column(Numeric(5, 2), nullable=True)  # (water / total) × 100
    
    # Timing
    transfer_datetime = Column(DateTime(timezone=True), nullable=False)
    
    # Dispatch Info (for outgoing transfers)
    customer_name = Column(String(100), nullable=True)
    vehicle_number = Column(String(20), nullable=True)
    invoice_number = Column(String(30), nullable=True)
    
    # Status
    is_completed = Column(Boolean, default=True)
    notes = Column(String(500), nullable=True)
    
    # Audit
    transferred_by = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<TankTransfer {self.transfer_number}: {self.quantity_liters}L>"
    
    def calculate_water_percentage(self, gross_liters: float) -> None:
        """
        Calculate water content percentage.
        
        Args:
            gross_liters: Total volume before water removal
        """
        if gross_liters > 0:
            water_pct = (float(self.water_removed_liters or 0) / gross_liters) * 100
            self.water_content_pct = Decimal(str(water_pct))
