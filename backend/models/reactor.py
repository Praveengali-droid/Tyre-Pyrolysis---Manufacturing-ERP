"""
Reactor Model - Pyrolysis Reactor Equipment.

Tracks reactor status and links to active production batches.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
from enum import Enum


class ReactorStatus(str, Enum):
    """Reactor operational status."""
    IDLE = "IDLE"
    LOADING = "LOADING"
    HEATING = "HEATING"
    DISTILLATION = "DISTILLATION"
    COOLING = "COOLING"
    UNLOADING = "UNLOADING"
    MAINTENANCE = "MAINTENANCE"


class Reactor(Base):
    """
    Pyrolysis reactor unit.
    
    Each reactor can process one batch at a time.
    Status is updated throughout the production cycle.
    """
    __tablename__ = "reactors"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Identity
    reactor_code = Column(String(10), unique=True, nullable=False, index=True)  # R1, R2
    name = Column(String(50), nullable=False)  # Reactor 1
    
    # Capacity
    capacity_kg = Column(Numeric(10, 2), nullable=False)  # Max input per batch
    
    # Status
    status = Column(String(20), default=ReactorStatus.IDLE.value)
    current_batch_id = Column(Integer, ForeignKey("production_batches.id"), nullable=True)
    
    # Operational
    is_active = Column(Boolean, default=True)
    last_maintenance_date = Column(DateTime(timezone=True), nullable=True)
    total_batches_processed = Column(Integer, default=0)
    
    # Maintenance tracking for safety interlock
    batches_since_last_cleaning = Column(Integer, default=0)
    maintenance_frequency = Column(Integer, default=3)  # Must clean every X batches
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Reactor {self.reactor_code}: {self.status}>"
    
    @property
    def is_available(self) -> bool:
        """Check if reactor is available for new batch."""
        return self.status == ReactorStatus.IDLE.value and self.is_active
    
    @property
    def maintenance_due(self) -> bool:
        """Check if maintenance is REQUIRED (safety interlock)."""
        if self.maintenance_frequency and self.maintenance_frequency > 0:
            return self.batches_since_last_cleaning >= self.maintenance_frequency
        return False
    
    @property
    def maintenance_warning(self) -> bool:
        """Check if maintenance is approaching (warning state)."""
        if self.maintenance_frequency and self.maintenance_frequency > 0:
            # Warn when within 1 batch of limit
            return self.batches_since_last_cleaning >= (self.maintenance_frequency - 1)
        return False
    
    @property
    def status_color(self) -> str:
        """Color code for UI display."""
        colors = {
            ReactorStatus.IDLE.value: "green",
            ReactorStatus.LOADING.value: "blue",
            ReactorStatus.HEATING.value: "red",
            ReactorStatus.DISTILLATION.value: "orange",
            ReactorStatus.COOLING.value: "cyan",
            ReactorStatus.UNLOADING.value: "yellow",
            ReactorStatus.MAINTENANCE.value: "gray",
        }
        return colors.get(self.status, "gray")
