"""
Purchase Order Model - Tracks orders placed with vendors.
Links vendors to expected material receipts.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum


class POStatus(str, enum.Enum):
    """Purchase Order status workflow."""
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED"
    RECEIVED = "RECEIVED"
    CANCELLED = "CANCELLED"


class PurchaseOrder(Base):
    """
    Purchase Order header table.
    
    Workflow:
    1. DRAFT: Created, can be edited
    2. CONFIRMED: Sent to vendor, locked
    3. PARTIALLY_RECEIVED: Some GRNs created
    4. RECEIVED: All items received
    5. CANCELLED: Order cancelled
    """
    __tablename__ = "purchase_orders"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    po_number = Column(String(30), unique=True, nullable=False, index=True)
    
    # Vendor Reference
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    
    # Dates
    order_date = Column(Date, nullable=False)
    expected_delivery_date = Column(Date)
    
    # Status
    status = Column(String(20), default=POStatus.DRAFT.value)
    
    # Amounts (calculated from items)
    subtotal_amount = Column(Numeric(14, 2), default=0)
    cgst_amount = Column(Numeric(12, 2), default=0)
    sgst_amount = Column(Numeric(12, 2), default=0)
    igst_amount = Column(Numeric(12, 2), default=0)
    total_amount = Column(Numeric(14, 2), default=0)
    
    # Terms
    payment_terms = Column(String(100))
    delivery_terms = Column(String(100))
    
    notes = Column(String(500))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    items = relationship("PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<PurchaseOrder {self.po_number}>"


class PurchaseOrderItem(Base):
    """
    Purchase Order line items.
    Each item represents a raw material being ordered.
    """
    __tablename__ = "purchase_order_items"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False)
    raw_material_id = Column(Integer, ForeignKey("raw_materials.id"), nullable=False)
    
    # Quantity
    ordered_qty_kg = Column(Numeric(12, 2), nullable=False)
    received_qty_kg = Column(Numeric(12, 2), default=0)
    pending_qty_kg = Column(Numeric(12, 2))  # ordered - received
    
    # Pricing
    rate_per_kg = Column(Numeric(10, 2), nullable=False)
    hsn_code = Column(String(10))
    gst_rate = Column(Numeric(4, 2), default=5.0)
    
    # Line Total
    line_amount = Column(Numeric(12, 2))  # qty * rate
    gst_amount = Column(Numeric(10, 2))
    total_amount = Column(Numeric(12, 2))  # line + gst
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="items")
    
    def __repr__(self):
        return f"<POItem PO:{self.purchase_order_id} Material:{self.raw_material_id}>"
