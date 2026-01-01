"""
Batch Log Entry Model - Operator readings during production.

Records temperature, pressure, and other parameters at specific
times during each stage of production.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text, JSON
from sqlalchemy.sql import func
from database import Base


class BatchLogEntry(Base):
    """
    Operator log entry for a production batch.
    
    Operators record readings (Temp, Pressure, Meter) at regular
    intervals during each stage. The system validates against
    safe_limits and flags out-of-range values.
    """
    __tablename__ = "batch_log_entries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Parent batch
    batch_id = Column(Integer, ForeignKey("production_batches.id"), nullable=False)
    
    # Stage context
    stage_name = Column(String(50), nullable=False)  # Which stage this log is for
    stage_sequence = Column(Integer, nullable=True)  # Stage order number
    
    # Timing
    log_datetime = Column(DateTime(timezone=True), server_default=func.now())
    
    # Readings (IoT-ready JSON)
    # Example: {"temp_c": 350.5, "pressure_bar": 0.25, "meter_kwh": 12650.75}
    readings = Column(JSON, nullable=False, default=dict)
    
    # Validation results
    is_within_limits = Column(Boolean, default=True)
    alerts = Column(JSON, default=list)  # ["Pressure high: 1.2 > 1.0"]
    
    # Operator info
    operator_name = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Entry type
    entry_type = Column(String(30), default="MANUAL")  # MANUAL, AUTO, IOT
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<BatchLogEntry {self.batch_id}:{self.stage_name} at {self.log_datetime}>"
    
    @property
    def temp_c(self) -> float:
        """Get temperature reading if available."""
        return self.readings.get("temp_c", 0) if self.readings else 0
    
    @property
    def pressure_bar(self) -> float:
        """Get pressure reading if available."""
        return self.readings.get("pressure_bar", 0) if self.readings else 0
    
    @property
    def meter_kwh(self) -> float:
        """Get electricity meter reading if available."""
        return self.readings.get("meter_kwh", 0) if self.readings else 0
    
    @property
    def has_alerts(self) -> bool:
        """Check if this entry has any alerts."""
        return bool(self.alerts and len(self.alerts) > 0)
