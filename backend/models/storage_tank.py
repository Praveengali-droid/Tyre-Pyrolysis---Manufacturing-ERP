"""
Storage Tank Model - Oil Storage Tank Farm.

Tracks tank capacity, current levels, and material types.
Oil output from production batches is assigned to tanks.
"""
from sqlalchemy import Column, Integer, String, DateTime, Numeric, Boolean
from sqlalchemy.sql import func
from database import Base
from decimal import Decimal
from enum import Enum


class TankType(str, Enum):
    """Type of storage tank."""
    SETTLING = "SETTLING"   # Initial collection, water separation
    STORAGE = "STORAGE"     # Intermediate storage
    SALES = "SALES"         # Ready for dispatch


class MaterialType(str, Enum):
    """Type of material stored in tank."""
    LIGHT_OIL = "LIGHT_OIL"
    HEAVY_OIL = "HEAVY_OIL"
    MIXED_OIL = "MIXED_OIL"


class StorageTank(Base):
    """
    Oil storage tank for tank farm management.
    
    Tracks current fill level and material type.
    Production batches add oil to tanks.
    Tank transfers move oil between tanks (with water removal).
    """
    __tablename__ = "storage_tanks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Identity
    tank_code = Column(String(20), unique=True, nullable=False, index=True)  # T1, SETTLING-1
    name = Column(String(50), nullable=False)  # Main Oil Tank
    
    # Classification
    tank_type = Column(String(20), default=TankType.STORAGE.value)
    material_type = Column(String(20), default=MaterialType.MIXED_OIL.value)
    
    # Capacity & Level (in liters)
    capacity_liters = Column(Numeric(12, 2), nullable=False)
    current_level_liters = Column(Numeric(12, 2), default=0)
    
    # Weight tracking (oil density ~0.85 kg/L)
    current_weight_kg = Column(Numeric(12, 2), default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_full = Column(Boolean, default=False)
    
    # Timestamps
    last_filled_at = Column(DateTime(timezone=True), nullable=True)
    last_emptied_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<StorageTank {self.tank_code}: {self.fill_percentage:.1f}%>"
    
    @property
    def fill_percentage(self) -> float:
        """Percentage of tank capacity filled."""
        if not self.capacity_liters or float(self.capacity_liters) == 0:
            return 0
        return (float(self.current_level_liters or 0) / float(self.capacity_liters)) * 100
    
    @property
    def available_capacity_liters(self) -> float:
        """Remaining capacity in liters."""
        return float(self.capacity_liters) - float(self.current_level_liters or 0)
    
    def add_oil(self, liters: float, weight_kg: float = None) -> bool:
        """
        Add oil to tank.
        
        Args:
            liters: Volume to add
            weight_kg: Weight in kg (calculated from density if not provided)
            
        Returns:
            True if successful, False if would overflow
        """
        if liters > self.available_capacity_liters:
            return False
        
        self.current_level_liters = Decimal(str(float(self.current_level_liters or 0) + liters))
        
        if weight_kg:
            self.current_weight_kg = Decimal(str(float(self.current_weight_kg or 0) + weight_kg))
        else:
            # Assume density 0.85 kg/L for oil
            self.current_weight_kg = Decimal(str(float(self.current_weight_kg or 0) + (liters * 0.85)))
        
        # Check if now full (>95% = full)
        if self.fill_percentage >= 95:
            self.is_full = True
        
        return True
    
    def remove_oil(self, liters: float) -> float:
        """
        Remove oil from tank.
        
        Args:
            liters: Volume to remove
            
        Returns:
            Actual volume removed (may be less if tank doesn't have enough)
        """
        available = float(self.current_level_liters or 0)
        to_remove = min(liters, available)
        
        self.current_level_liters = Decimal(str(available - to_remove))
        
        # Update weight proportionally
        if available > 0:
            weight_ratio = to_remove / available
            weight_to_remove = float(self.current_weight_kg or 0) * weight_ratio
            self.current_weight_kg = Decimal(str(float(self.current_weight_kg or 0) - weight_to_remove))
        
        self.is_full = False
        
        return to_remove
