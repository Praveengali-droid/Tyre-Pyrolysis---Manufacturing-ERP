"""
Quotation and Sale Order Models - Quote to Order to Dispatch workflow.

Workflow: Quotation (Draft → Sent → Accepted) → Sale Order → Dispatch
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, Date, Boolean, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
from decimal import Decimal
import enum


class QuotationStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SENT = "SENT"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    CONVERTED = "CONVERTED"  # Converted to Sale Order


class SaleOrderStatus(str, enum.Enum):
    CONFIRMED = "CONFIRMED"
    PARTIALLY_DISPATCHED = "PARTIALLY_DISPATCHED"
    DISPATCHED = "DISPATCHED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class Quotation(Base):
    """
    Sales Quotation - Quote sent to customer for approval.
    """
    __tablename__ = "quotations"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Quotation Number
    quotation_number = Column(String(30), unique=True, nullable=False, index=True)  # QT-20260101-001
    quotation_date = Column(Date, nullable=False)
    valid_until = Column(Date, nullable=True)  # Expiry date
    
    # Customer
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    
    # Status
    status = Column(String(20), default=QuotationStatus.DRAFT.value)
    
    # Amounts (calculated from items)
    subtotal = Column(Numeric(14, 2), default=0)
    tax_amount = Column(Numeric(12, 2), default=0)
    discount_amount = Column(Numeric(12, 2), default=0)
    total_amount = Column(Numeric(14, 2), default=0)
    
    # Terms
    payment_terms = Column(String(200), nullable=True)
    delivery_terms = Column(String(200), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Converted to Sale Order
    sale_order_id = Column(Integer, ForeignKey("sale_orders.id"), nullable=True)
    
    # Audit
    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    items = relationship("QuotationItem", back_populates="quotation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Quotation {self.quotation_number}: {self.status}>"


class QuotationItem(Base):
    """Line item in a Quotation."""
    __tablename__ = "quotation_items"
    
    id = Column(Integer, primary_key=True, index=True)
    
    quotation_id = Column(Integer, ForeignKey("quotations.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Item Details
    description = Column(String(200), nullable=True)
    quantity = Column(Numeric(12, 2), nullable=False)
    unit = Column(String(10), default="KG")
    rate = Column(Numeric(10, 2), nullable=False)
    
    # Amounts
    amount = Column(Numeric(14, 2), nullable=False)  # quantity * rate
    tax_rate = Column(Numeric(5, 2), default=18.0)  # GST %
    tax_amount = Column(Numeric(12, 2), default=0)
    total_amount = Column(Numeric(14, 2), nullable=False)  # amount + tax
    
    # Relationship
    quotation = relationship("Quotation", back_populates="items")
    
    def __repr__(self):
        return f"<QuotationItem {self.id}: {self.quantity} @ {self.rate}>"


class SaleOrder(Base):
    """
    Sales Order - Confirmed order from customer (converted from Quotation or direct).
    """
    __tablename__ = "sale_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Order Number
    order_number = Column(String(30), unique=True, nullable=False, index=True)  # SO-20260101-001
    order_date = Column(Date, nullable=False)
    
    # Customer
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    
    # Source (optional - if from quotation)
    quotation_id = Column(Integer, ForeignKey("quotations.id"), nullable=True)
    
    # Status
    status = Column(String(30), default=SaleOrderStatus.CONFIRMED.value)
    
    # Amounts
    subtotal = Column(Numeric(14, 2), default=0)
    tax_amount = Column(Numeric(12, 2), default=0)
    discount_amount = Column(Numeric(12, 2), default=0)
    total_amount = Column(Numeric(14, 2), default=0)
    
    # Delivery
    expected_delivery_date = Column(Date, nullable=True)
    delivery_address = Column(Text, nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Audit
    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    items = relationship("SaleOrderItem", back_populates="sale_order", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<SaleOrder {self.order_number}: {self.status}>"


class SaleOrderItem(Base):
    """Line item in a Sale Order."""
    __tablename__ = "sale_order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    
    sale_order_id = Column(Integer, ForeignKey("sale_orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Item Details
    description = Column(String(200), nullable=True)
    quantity = Column(Numeric(12, 2), nullable=False)
    unit = Column(String(10), default="KG")
    rate = Column(Numeric(10, 2), nullable=False)
    
    # Dispatch tracking
    dispatched_quantity = Column(Numeric(12, 2), default=0)
    pending_quantity = Column(Numeric(12, 2), nullable=True)  # Calculated
    
    # Amounts
    amount = Column(Numeric(14, 2), nullable=False)
    tax_rate = Column(Numeric(5, 2), default=18.0)
    tax_amount = Column(Numeric(12, 2), default=0)
    total_amount = Column(Numeric(14, 2), nullable=False)
    
    # Relationship
    sale_order = relationship("SaleOrder", back_populates="items")
    
    def __repr__(self):
        return f"<SaleOrderItem {self.id}: {self.quantity} @ {self.rate}>"
