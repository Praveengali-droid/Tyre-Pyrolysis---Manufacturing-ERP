"""
Raw Material Model - Tracks scrap tyres inventory.
Primary input material for pyrolysis process.

HSN Codes Reference:
- 4004: Waste, parings and scrap of rubber (waste tyres)
- 4012: Retreaded or used pneumatic tyres
- 40040000: Waste/scrap rubber (specific 8-digit)
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric
from sqlalchemy.sql import func
from database import Base
import enum


class MaterialType(str, enum.Enum):
    """Types of scrap tyres by vehicle category."""
    TRUCK_TYRE = "TRUCK_TYRE"
    CAR_TYRE = "CAR_TYRE"
    TWO_WHEELER = "TWO_WHEELER"
    OTR = "OTR"  # Off-The-Road (mining, agriculture)
    MIXED = "MIXED"


class RawMaterial(Base):
    """
    Raw material master table.
    
    In pyrolysis context, this primarily tracks different grades
    of scrap tyres which are the input to the reactor.
    
    Quality parameters affect yield:
    - Higher rubber content → More oil yield
    - Higher steel content → More steel wire output
    - Moisture affects heating efficiency
    """
    __tablename__ = "raw_materials"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    material_code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    material_type = Column(String(50), nullable=False, default=MaterialType.MIXED.value)
    
    # ═══════════════════════════════════════════════════════════
    # INDIAN GST/HSN COMPLIANCE
    # HSN code determines applicable GST rate
    # ═══════════════════════════════════════════════════════════
    hsn_code = Column(String(10), nullable=False, default="4004")  # Default: Waste rubber
    gst_rate = Column(Numeric(4, 2), default=5.00)  # Typically 5% for waste materials
    
    # Inventory (Physical Stock)
    current_stock_kg = Column(Numeric(12, 2), default=0)
    minimum_stock_kg = Column(Numeric(12, 2), default=0)  # Reorder level
    
    # Quality Parameters (Expected averages)
    average_rubber_content = Column(Numeric(5, 2))  # % of rubber in tyre
    average_steel_content = Column(Numeric(5, 2))   # % of steel wire
    average_carbon_content = Column(Numeric(5, 2))  # % of carbon black
    moisture_content_max = Column(Numeric(5, 2))    # Maximum acceptable moisture %
    
    # Pricing
    standard_rate_per_kg = Column(Numeric(10, 2))  # Standard procurement rate
    
    # Storage
    storage_location = Column(String(50))  # Warehouse/Yard section
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<RawMaterial {self.material_code}: {self.name}>"
    
    @property
    def is_low_stock(self) -> bool:
        """Check if stock is below minimum level."""
        return self.current_stock_kg < self.minimum_stock_kg
    
    def adjust_stock(self, quantity_kg: float, is_addition: bool = True) -> float:
        """
        Adjust stock level. Used after GRN approval.
        
        Args:
            quantity_kg: Amount to add/subtract
            is_addition: True for inward, False for consumption
            
        Returns:
            New stock level
        """
        if is_addition:
            self.current_stock_kg += quantity_kg
        else:
            self.current_stock_kg -= quantity_kg
        return float(self.current_stock_kg)
