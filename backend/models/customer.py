"""
Customer Model - Buyers for Oil, Carbon Black, and Steel.
"""
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, Enum
from sqlalchemy.sql import func
import enum

from database import Base


class CustomerType(str, enum.Enum):
    OIL_BUYER = "OIL_BUYER"
    CARBON_BUYER = "CARBON_BUYER"
    STEEL_BUYER = "STEEL_BUYER"
    ALL = "ALL"


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    
    # Basic Info
    customer_code = Column(String(20), unique=True, nullable=False)  # e.g., "CUST-001"
    name = Column(String(100), nullable=False)
    customer_type = Column(String(20), default=CustomerType.ALL.value)
    
    # Contact
    contact_person = Column(String(100))
    phone = Column(String(20))
    email = Column(String(100))
    
    # Address
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    pincode = Column(String(10))
    
    # GST Info
    gst_number = Column(String(20))
    pan_number = Column(String(15))
    
    # Payment Terms
    payment_terms_days = Column(Integer, default=30)  # Net 30, etc.
    credit_limit = Column(Integer, default=0)  # In INR
    
    # Status
    is_active = Column(Boolean, default=True)
    notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Customer {self.customer_code}: {self.name}>"
