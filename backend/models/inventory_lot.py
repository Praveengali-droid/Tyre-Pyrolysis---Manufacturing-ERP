"""
Inventory Lot Model - FIFO Batch Tracking for Raw Materials.

Each GRN receipt creates a new lot. When consuming material for production,
the system should consume from the oldest lot first (FIFO).

Lot ID Format: YYYYMMDD-VND-XXXX (Date + Vendor Code)
Example: 20251231-VND-0001
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, Date, Boolean
from sqlalchemy.sql import func
from database import Base
from decimal import Decimal


class InventoryLot(Base):
    """
    Inventory lot for FIFO tracking.
    
    Each approved GRN creates one lot. The lot tracks:
    - Original received quantity
    - Current remaining quantity (decreases as consumed)
    - Cost per kg at time of receipt
    - Link back to source GRN for traceability
    
    FIFO Consumption:
    When production consumes material, query lots ordered by receipt_date ASC
    and consume from oldest first.
    """
    __tablename__ = "inventory_lots"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Lot ID: YYYYMMDD-VND-XXXX format
    lot_id = Column(String(30), unique=True, nullable=False, index=True)
    
    # References
    grn_id = Column(Integer, ForeignKey("goods_receipt_notes.id"), nullable=False)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    raw_material_id = Column(Integer, ForeignKey("raw_materials.id"), nullable=False)
    
    # Receipt Info
    receipt_date = Column(Date, nullable=False, index=True)  # For FIFO ordering
    vehicle_number = Column(String(20))
    
    # Quantities
    received_qty_kg = Column(Numeric(12, 2), nullable=False)  # Original qty from GRN
    current_qty_kg = Column(Numeric(12, 2), nullable=False)   # Remaining after consumption
    consumed_qty_kg = Column(Numeric(12, 2), default=0)       # Total consumed so far
    
    # Cost (for weighted average and costing)
    rate_per_kg = Column(Numeric(10, 2), nullable=False)      # Purchase rate
    total_cost = Column(Numeric(14, 2))                       # received_qty × rate
    
    # Status
    is_exhausted = Column(Boolean, default=False)  # True when current_qty = 0
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<InventoryLot {self.lot_id}: {self.current_qty_kg}kg remaining>"
    
    def consume(self, qty_kg: float) -> float:
        """
        Consume material from this lot.
        
        Args:
            qty_kg: Quantity to consume
            
        Returns:
            Actual quantity consumed (may be less if lot doesn't have enough)
        """
        available = float(self.current_qty_kg or 0)
        to_consume = min(qty_kg, available)
        
        self.current_qty_kg = Decimal(str(available - to_consume))
        self.consumed_qty_kg = Decimal(str(float(self.consumed_qty_kg or 0) + to_consume))
        
        if self.current_qty_kg <= 0:
            self.is_exhausted = True
            self.current_qty_kg = Decimal("0")
        
        return to_consume
    
    @property
    def remaining_percentage(self) -> float:
        """Percentage of lot remaining."""
        if not self.received_qty_kg or float(self.received_qty_kg) == 0:
            return 0
        return (float(self.current_qty_kg) / float(self.received_qty_kg)) * 100
