"""
Output Dispatch Models - Carbon and Steel sales/dispatch tracking.

Tracks when outputs are sold/dispatched from stock.
Stock = sum(batch outputs) - sum(dispatches)
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, Date, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
from decimal import Decimal


class CarbonDispatch(Base):
    """
    Carbon (Char) dispatch/sales record.
    
    Carbon is produced during pyrolysis and stored on-site.
    This tracks when carbon is sold to buyers.
    """
    __tablename__ = "carbon_dispatches"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    dispatch_code = Column(String(30), unique=True, nullable=False, index=True)  # CD-20260101-001
    dispatch_date = Column(Date, nullable=False)
    
    # Customer Reference
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    
    # Quantity
    quantity_kg = Column(Numeric(12, 2), nullable=False)
    rate_per_kg = Column(Numeric(10, 2), nullable=True)
    total_amount = Column(Numeric(14, 2), nullable=True)
    
    # Vehicle
    vehicle_number = Column(String(20), nullable=True)
    driver_name = Column(String(100), nullable=True)
    
    # Invoice
    invoice_number = Column(String(50), nullable=True)
    payment_status = Column(String(20), default="PENDING")  # PENDING, PAID
    
    # Quality
    quality_grade = Column(String(10), nullable=True)  # A, B, C
    notes = Column(Text, nullable=True)
    
    # Receipt Confirmation
    customer_confirmed = Column(Boolean, default=False)
    
    # Audit
    dispatched_by = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<CarbonDispatch {self.dispatch_code}: {self.quantity_kg}kg>"


class SteelDispatch(Base):
    """
    Steel (wire/scrap) dispatch/sales record.
    
    Steel rims and wire are recovered during pyrolysis.
    This tracks when steel is sold to scrap dealers.
    """
    __tablename__ = "steel_dispatches"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    dispatch_code = Column(String(30), unique=True, nullable=False, index=True)  # SD-20260101-001
    dispatch_date = Column(Date, nullable=False)
    
    # Customer Reference
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    
    # Quantity
    quantity_kg = Column(Numeric(12, 2), nullable=False)
    rate_per_kg = Column(Numeric(10, 2), nullable=True)
    total_amount = Column(Numeric(14, 2), nullable=True)
    
    # Vehicle
    vehicle_number = Column(String(20), nullable=True)
    driver_name = Column(String(100), nullable=True)
    
    # Invoice
    invoice_number = Column(String(50), nullable=True)
    payment_status = Column(String(20), default="PENDING")
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Receipt Confirmation
    customer_confirmed = Column(Boolean, default=False)
    
    # Audit
    dispatched_by = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<SteelDispatch {self.dispatch_code}: {self.quantity_kg}kg>"
