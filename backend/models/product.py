"""
Product Model - Sellable products (Oil, Carbon, Steel, Other)
"""
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, Numeric, Enum
from sqlalchemy.sql import func
import enum
from database import Base


class ProductType(str, enum.Enum):
    OIL = "OIL"
    CARBON = "CARBON"
    STEEL = "STEEL"
    OTHER = "OTHER"


class Product(Base):
    """
    Product master for sales - Oil, Carbon Black, Steel Scrap, etc.
    """
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic Info
    product_code = Column(String(20), unique=True, nullable=False)  # PROD-001
    name = Column(String(100), nullable=False)  # e.g., "Pyrolysis Oil"
    product_type = Column(String(20), nullable=False)  # OIL, CARBON, STEEL, OTHER
    
    # GST Info
    hsn_code = Column(String(10), nullable=True)  # HSN code for invoicing
    gst_rate = Column(Numeric(5, 2), default=18.0)  # GST percentage
    
    # Unit of Measure
    unit = Column(String(10), default="KG")  # KG, LITERS, NOS
    
    # Pricing
    default_rate = Column(Numeric(10, 2), nullable=True)  # Default selling rate
    
    # Stock (for non-tank products)
    # For OIL: stock is tracked in storage_tanks
    # For CARBON/STEEL: tracked via batch outputs - dispatches
    current_stock = Column(Numeric(12, 2), default=0)
    min_stock_alert = Column(Numeric(12, 2), default=0)
    
    # Description
    description = Column(Text, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Product {self.product_code}: {self.name}>"
