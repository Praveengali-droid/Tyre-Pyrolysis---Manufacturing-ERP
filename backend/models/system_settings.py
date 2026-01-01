"""
System Settings Model - Admin-configurable constants.

Stores configurable rates and values used in calculations:
- Electricity rate per kWh
- Labor cost per hour
- Default GST rates
- Other plant-specific constants
"""
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, Text
from sqlalchemy.sql import func
from database import Base


class SystemSetting(Base):
    """
    Key-value store for system-wide configurable settings.
    Admin-only access.
    """
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(String(255), nullable=False)
    value_type = Column(String(20), default="string")  # string, number, boolean, json
    description = Column(Text, nullable=True)
    category = Column(String(50), default="general")  # general, finance, production, sales
    
    # Audit
    updated_by = Column(String(100), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<SystemSetting {self.key}={self.value}>"
    
    @property
    def typed_value(self):
        """Return value cast to its proper type."""
        if self.value_type == "number":
            return float(self.value)
        elif self.value_type == "boolean":
            return self.value.lower() in ("true", "1", "yes")
        elif self.value_type == "integer":
            return int(self.value)
        return self.value


# Default settings to seed
DEFAULT_SETTINGS = [
    # Finance
    {"key": "electricity_rate_per_kwh", "value": "8.0", "value_type": "number", 
     "description": "Electricity cost per kWh in ₹", "category": "finance"},
    {"key": "avg_labor_cost_per_hour", "value": "150", "value_type": "number",
     "description": "Average labor cost per hour in ₹", "category": "finance"},
    {"key": "default_gst_rate", "value": "18", "value_type": "number",
     "description": "Default GST percentage for byproducts", "category": "finance"},
    
    # Production
    {"key": "maintenance_batch_limit", "value": "3", "value_type": "integer",
     "description": "Batches before maintenance required", "category": "production"},
    {"key": "target_oil_yield", "value": "42", "value_type": "number",
     "description": "Target oil yield percentage", "category": "production"},
    {"key": "target_carbon_yield", "value": "35", "value_type": "number",
     "description": "Target carbon yield percentage", "category": "production"},
    {"key": "syngas_loss_threshold", "value": "8", "value_type": "number",
     "description": "Alert threshold for syn-gas loss percentage", "category": "production"},
    
    # Sales
    {"key": "default_payment_terms_days", "value": "30", "value_type": "integer",
     "description": "Default payment terms in days", "category": "sales"},
    {"key": "quotation_validity_days", "value": "15", "value_type": "integer",
     "description": "Default quotation validity period", "category": "sales"},
]
