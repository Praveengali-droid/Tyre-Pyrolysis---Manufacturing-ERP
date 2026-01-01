"""
Production Batch Model - Pyrolysis Production Run.

Tracks input materials, outputs (oil, carbon, steel), electricity,
and enforces mass balance: syn_gas_loss = input - (oil + carbon + steel).
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, Boolean, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
from decimal import Decimal
from enum import Enum


class BatchStatus(str, Enum):
    """Production batch status."""
    LOADING = "LOADING"           # Raw material being loaded
    IN_PROGRESS = "IN_PROGRESS"   # Pyrolysis underway
    COOLING = "COOLING"           # Post-process cooling
    PENDING_QC = "PENDING_QC"     # Awaiting quality check
    COMPLETED = "COMPLETED"       # Finished and recorded
    CANCELLED = "CANCELLED"       # Stopped before completion
    ON_HOLD = "ON_HOLD"           # Paused (power cut, maintenance)


class ProductionBatch(Base):
    """
    Production batch for pyrolysis process.
    
    Critical Business Rules:
    1. syn_gas_loss = input_weight - (oil_output + carbon_output + steel_output)
    2. Batch CANNOT be completed without destination_tank_id
    3. Input is consumed from oldest inventory lot (FIFO)
    4. Electricity cost = (meter_end - meter_start) × rate
    5. Safety interlock: Cannot advance to UNLOADING if temp > safe limit
    """
    __tablename__ = "production_batches"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Batch Identity
    batch_number = Column(String(30), unique=True, nullable=False, index=True)  # BATCH-20251231-001
    
    # Equipment
    reactor_id = Column(Integer, ForeignKey("reactors.id"), nullable=False)
    
    # Recipe (for process tracking)
    recipe_id = Column(Integer, ForeignKey("batch_recipes.id"), nullable=True)
    
    # Status
    status = Column(String(20), default=BatchStatus.LOADING.value)
    
    # Stage Tracking
    current_stage = Column(String(50), nullable=True)  # Current active stage name
    current_stage_sequence = Column(Integer, nullable=True)  # Stage order number
    current_stage_start = Column(DateTime(timezone=True), nullable=True)  # When current stage started
    expected_end_time = Column(DateTime(timezone=True), nullable=True)  # Calculated from recipe
    
    # Hold/Pause tracking
    hold_datetime = Column(DateTime(timezone=True), nullable=True)  # When batch was put on hold
    hold_reason = Column(String(200), nullable=True)
    total_hold_minutes = Column(Integer, default=0)  # Accumulated hold time
    
    # INPUT (from FIFO inventory lot)
    input_lot_id = Column(Integer, ForeignKey("inventory_lots.id"), nullable=False)
    input_weight_kg = Column(Numeric(12, 2), nullable=False)
    
    # TIMING
    batch_date = Column(Date, nullable=False)
    start_datetime = Column(DateTime(timezone=True), nullable=True)
    end_datetime = Column(DateTime(timezone=True), nullable=True)
    
    # ELECTRICITY TRACKING
    meter_start = Column(Numeric(12, 2), nullable=True)  # kWh reading at start
    meter_end = Column(Numeric(12, 2), nullable=True)    # kWh reading at end
    electricity_used_kwh = Column(Numeric(10, 2), nullable=True)  # Calculated
    electricity_rate = Column(Numeric(6, 2), default=8.50)  # ₹/kWh
    electricity_cost = Column(Numeric(12, 2), nullable=True)  # Calculated
    
    # OUTPUTS (recorded on completion)
    oil_output_kg = Column(Numeric(12, 2), nullable=True)
    carbon_output_kg = Column(Numeric(12, 2), nullable=True)
    steel_output_kg = Column(Numeric(12, 2), nullable=True)
    
    # MASS BALANCE (calculated)
    total_output_kg = Column(Numeric(12, 2), nullable=True)
    syn_gas_loss_kg = Column(Numeric(12, 2), nullable=True)  # input - total_output
    
    # YIELD PERCENTAGES (calculated)
    oil_yield_pct = Column(Numeric(5, 2), nullable=True)     # (oil / input) × 100
    carbon_yield_pct = Column(Numeric(5, 2), nullable=True)
    steel_yield_pct = Column(Numeric(5, 2), nullable=True)
    loss_pct = Column(Numeric(5, 2), nullable=True)          # (syn_gas_loss / input) × 100
    
    # OIL DESTINATION (REQUIRED for completion)
    destination_tank_id = Column(Integer, ForeignKey("storage_tanks.id"), nullable=True)
    oil_liters_to_tank = Column(Numeric(12, 2), nullable=True)  # Converted from kg
    
    # QUALITY
    oil_quality_grade = Column(String(10), nullable=True)  # A, B, C
    carbon_quality_grade = Column(String(10), nullable=True)
    quality_notes = Column(String(500), nullable=True)
    
    # AUDIT
    started_by = Column(String(100), nullable=True)
    completed_by = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<ProductionBatch {self.batch_number}: {self.status}>"
    
    def calculate_outputs(self):
        """
        Calculate total output, syn gas loss, and yields.
        Call this before completing the batch.
        """
        oil = float(self.oil_output_kg or 0)
        carbon = float(self.carbon_output_kg or 0)
        steel = float(self.steel_output_kg or 0)
        input_wt = float(self.input_weight_kg)
        
        # Total output
        self.total_output_kg = Decimal(str(oil + carbon + steel))
        
        # Mass balance: syn gas loss = input - outputs
        self.syn_gas_loss_kg = Decimal(str(input_wt - (oil + carbon + steel)))
        
        # Yield percentages
        if input_wt > 0:
            self.oil_yield_pct = Decimal(str((oil / input_wt) * 100))
            self.carbon_yield_pct = Decimal(str((carbon / input_wt) * 100))
            self.steel_yield_pct = Decimal(str((steel / input_wt) * 100))
            self.loss_pct = Decimal(str((float(self.syn_gas_loss_kg) / input_wt) * 100))
    
    def calculate_electricity(self):
        """Calculate electricity used and cost."""
        if self.meter_start and self.meter_end:
            kwh = float(self.meter_end) - float(self.meter_start)
            self.electricity_used_kwh = Decimal(str(max(0, kwh)))
            self.electricity_cost = Decimal(str(kwh * float(self.electricity_rate or 8.50)))
    
    def convert_oil_to_liters(self, density: float = 0.85) -> float:
        """
        Convert oil output from kg to liters.
        Default oil density: 0.85 kg/L
        """
        if not self.oil_output_kg:
            return 0
        liters = float(self.oil_output_kg) / density
        self.oil_liters_to_tank = Decimal(str(liters))
        return liters
    
    @property
    def is_valid_for_completion(self) -> bool:
        """Check if batch can be marked as completed."""
        # Must have destination tank for oil
        if not self.destination_tank_id:
            return False
        
        # Must have outputs recorded
        if self.oil_output_kg is None or self.carbon_output_kg is None or self.steel_output_kg is None:
            return False
        
        # Outputs cannot exceed input (mass balance)
        total = float(self.oil_output_kg) + float(self.carbon_output_kg) + float(self.steel_output_kg)
        if total > float(self.input_weight_kg):
            return False
        
        return True
    
    @property
    def cost_per_kg_oil(self) -> float:
        """Calculate electricity cost per kg of oil produced."""
        if not self.electricity_cost or not self.oil_output_kg:
            return 0
        if float(self.oil_output_kg) == 0:
            return 0
        return float(self.electricity_cost) / float(self.oil_output_kg)
