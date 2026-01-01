"""
Weighbridge Record Model - Captures weight measurements.
Used for both inward (procurement) and outward (sales dispatch) movements.

Physical Process:
1. Truck arrives fully loaded → Gross Weight captured
2. Truck leaves empty → Tare Weight captured
3. Net Weight = Gross - Tare (actual material weight)
"""
from sqlalchemy import Column, Integer, String, DateTime, Numeric
from sqlalchemy.sql import func
from database import Base
import enum


class WeighmentType(str, enum.Enum):
    """Direction of material movement."""
    INWARD = "INWARD"    # Procurement (raw materials in)
    OUTWARD = "OUTWARD"  # Sales (byproducts out)


class WeighbridgeRecord(Base):
    """
    Weighbridge/Toll record for weight capture.
    
    This is the first data entry point when a truck arrives.
    GRN references this record for weight data.
    """
    __tablename__ = "weighbridge_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_number = Column(String(30), unique=True, nullable=False, index=True)
    
    # Vehicle Details
    vehicle_number = Column(String(20), nullable=False, index=True)
    driver_name = Column(String(100))
    driver_phone = Column(String(20))
    driver_license = Column(String(30))
    
    # Weight Measurements
    gross_weight_kg = Column(Numeric(12, 2))  # Loaded truck weight
    tare_weight_kg = Column(Numeric(12, 2))   # Empty truck weight
    net_weight_kg = Column(Numeric(12, 2))    # Calculated: gross - tare
    
    # Preliminary Deductions (quick estimate at weighbridge)
    # Detailed deductions are captured in GRN
    estimated_deduction_kg = Column(Numeric(10, 2), default=0)
    deduction_reason = Column(String(100))  # Quick note: "Muddy load", "Wet tyres"
    
    # Weighment Type & Timing
    weighment_type = Column(String(20), default=WeighmentType.INWARD.value)
    material_type = Column(String(50))  # What's being weighed
    first_weight_datetime = Column(DateTime(timezone=True))  # Gross weight time
    second_weight_datetime = Column(DateTime(timezone=True))  # Tare weight time
    
    # Reference Links (filled after GRN/Dispatch Note creation)
    reference_type = Column(String(20))  # 'PURCHASE_ORDER', 'SALES_ORDER', 'GRN'
    reference_id = Column(Integer)
    
    # Operator
    operator_name = Column(String(100))
    
    # Status
    status = Column(String(20), default="PENDING")  # PENDING, COMPLETED, CANCELLED
    notes = Column(String(500))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<WeighbridgeRecord {self.ticket_number}: {self.vehicle_number}>"
    
    def calculate_net_weight(self) -> float:
        """
        Calculate net weight from gross and tare.
        Call this after both weights are captured.
        """
        if self.gross_weight_kg and self.tare_weight_kg:
            self.net_weight_kg = float(self.gross_weight_kg) - float(self.tare_weight_kg)
        return float(self.net_weight_kg or 0)
