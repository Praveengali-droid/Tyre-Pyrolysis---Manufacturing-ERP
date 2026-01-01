"""
Predictive Maintenance Models - Schedules, Logs, and Safety Interlocks.

Safety: Reactors must not run without proper cleaning maintenance.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, Date, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
from decimal import Decimal


class MaintenanceSchedule(Base):
    """
    Defines recurring maintenance tasks for equipment.
    e.g. Reactor carbon cleaning every 3 batches or 30 days.
    """
    __tablename__ = "maintenance_schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Equipment reference (for now, just reactor)
    reactor_id = Column(Integer, ForeignKey("reactors.id"), nullable=True)
    equipment_type = Column(String(50), default="REACTOR")  # REACTOR, TANK, etc.
    
    # Task details
    task_name = Column(String(100), nullable=False)  # e.g. "Carbon Cleaning"
    task_description = Column(Text, nullable=True)
    
    # Frequency triggers (either can trigger)
    frequency_batches = Column(Integer, nullable=True)  # Every X batches
    frequency_days = Column(Integer, nullable=True)     # Every Y days
    
    # Warning thresholds (when to show yellow warning)
    warning_batches = Column(Integer, nullable=True)    # Show warning at X-1 batches
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    logs = relationship("MaintenanceLog", back_populates="schedule")
    
    def __repr__(self):
        return f"<MaintenanceSchedule {self.task_name}>"


class MaintenanceLog(Base):
    """
    Tracks when a maintenance task was actually performed.
    Completing a log resets the reactor's maintenance counter.
    """
    __tablename__ = "maintenance_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Link to schedule and equipment
    schedule_id = Column(Integer, ForeignKey("maintenance_schedules.id"), nullable=False)
    reactor_id = Column(Integer, ForeignKey("reactors.id"), nullable=True)
    
    # When performed
    performed_date = Column(DateTime(timezone=True), server_default=func.now())
    performed_by = Column(String(100), nullable=True)
    
    # Details
    notes = Column(Text, nullable=True)
    photo_path = Column(String(500), nullable=True)  # Optional proof photo
    
    # Batch count at time of maintenance (for records)
    batches_at_maintenance = Column(Integer, default=0)
    
    # Auto-reset counter
    counter_reset = Column(Boolean, default=True)  # Did this reset the counter?
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    schedule = relationship("MaintenanceSchedule", back_populates="logs")
    
    def __repr__(self):
        return f"<MaintenanceLog {self.id}: {self.schedule_id} by {self.performed_by}>"


class RequestType(str):
    """Types of maintenance requests."""
    BREAKDOWN = "BREAKDOWN"      # Equipment failed
    PREVENTIVE = "PREVENTIVE"    # Scheduled maintenance
    CORRECTIVE = "CORRECTIVE"    # Fix before it fails
    INSPECTION = "INSPECTION"    # Routine check


class RequestPriority(str):
    """Priority levels for requests."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RequestStatus(str):
    """Status flow for maintenance requests."""
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    ON_HOLD = "ON_HOLD"          # Waiting for parts
    COMPLETED = "COMPLETED"
    DEFERRED = "DEFERRED"        # Postponed
    CANCELLED = "CANCELLED"


class MaintenanceRequest(Base):
    """
    Manual maintenance request created by operators.
    Tracks issues, repairs, and work orders.
    """
    __tablename__ = "maintenance_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Request number
    request_number = Column(String(30), unique=True, nullable=False)  # REQ-YYYYMMDD-XXX
    
    # Equipment reference
    reactor_id = Column(Integer, ForeignKey("reactors.id"), nullable=True)
    equipment_type = Column(String(50), default="REACTOR")  # REACTOR, TANK, PUMP, OTHER
    equipment_name = Column(String(100), nullable=True)     # Free text for other equipment
    
    # Request details
    request_type = Column(String(20), default="BREAKDOWN")
    priority = Column(String(20), default="MEDIUM")
    status = Column(String(20), default="OPEN")
    
    # Description
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Requester
    requested_by = Column(String(100), nullable=True)
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Assignment
    assigned_to = Column(String(100), nullable=True)
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    
    # Resolution
    resolution_notes = Column(Text, nullable=True)
    resolved_by = Column(String(100), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Time tracking
    downtime_hours = Column(Numeric(8, 2), nullable=True)
    labor_hours = Column(Numeric(8, 2), nullable=True)
    
    # Cost tracking
    parts_cost = Column(Numeric(12, 2), default=0)
    labor_cost = Column(Numeric(12, 2), default=0)
    total_cost = Column(Numeric(12, 2), default=0)
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<MaintenanceRequest {self.request_number}: {self.title}>"


class SparePart(Base):
    """
    Master list of spare parts used in maintenance.
    """
    __tablename__ = "spare_parts"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Part identification
    part_code = Column(String(30), unique=True, nullable=False)  # e.g., SP001
    part_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)  # BEARING, SEAL, GASKET, MOTOR, ELECTRICAL, OTHER
    
    # Equipment association
    equipment_type = Column(String(50), nullable=True)  # REACTOR, TANK, PUMP, GENERAL
    
    # Inventory management
    unit = Column(String(20), default="PCS")  # PCS, SET, KG, LTR
    reorder_level = Column(Integer, default=2)  # Alert when stock falls below
    reorder_quantity = Column(Integer, default=5)  # Suggested reorder qty
    
    # Pricing
    current_price = Column(Numeric(12, 2), default=0)
    last_purchase_price = Column(Numeric(12, 2), nullable=True)
    
    # Supplier info
    preferred_vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=True)
    vendor_part_number = Column(String(50), nullable=True)
    lead_time_days = Column(Integer, default=7)
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Stock (will be maintained in SparePartsStock)
    stock = relationship("SparePartsStock", back_populates="part", uselist=False)
    
    def __repr__(self):
        return f"<SparePart {self.part_code}: {self.part_name}>"


class SparePartsStock(Base):
    """
    Current stock levels for spare parts.
    Separate from SparePart master for better tracking.
    """
    __tablename__ = "spare_parts_stock"
    
    id = Column(Integer, primary_key=True, index=True)
    part_id = Column(Integer, ForeignKey("spare_parts.id"), unique=True, nullable=False)
    
    # Quantities
    current_qty = Column(Integer, default=0)
    reserved_qty = Column(Integer, default=0)  # Reserved for scheduled jobs
    available_qty = Column(Integer, default=0)  # current - reserved
    
    # Valuation
    total_value = Column(Numeric(12, 2), default=0)  # current_qty * avg_price
    
    # Location
    storage_location = Column(String(100), nullable=True)  # BIN-A1, SHELF-3
    
    # Alerts
    is_below_reorder = Column(Boolean, default=False)
    
    # Timestamps
    last_received_at = Column(DateTime(timezone=True), nullable=True)
    last_issued_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    part = relationship("SparePart", back_populates="stock")
    
    def __repr__(self):
        return f"<SparePartsStock Part:{self.part_id} Qty:{self.current_qty}>"


class PartsUsage(Base):
    """
    Track parts used in maintenance requests.
    Links MaintenanceRequest to SparePart consumption.
    """
    __tablename__ = "parts_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("maintenance_requests.id"), nullable=True)
    part_id = Column(Integer, ForeignKey("spare_parts.id"), nullable=False)
    
    # Usage
    quantity = Column(Integer, default=1)
    unit_price = Column(Numeric(12, 2), default=0)  # Price at time of usage
    total_price = Column(Numeric(12, 2), default=0)
    
    # Timestamps
    used_at = Column(DateTime(timezone=True), server_default=func.now())
    used_by = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<PartsUsage Req:{self.request_id} Part:{self.part_id} Qty:{self.quantity}>"
