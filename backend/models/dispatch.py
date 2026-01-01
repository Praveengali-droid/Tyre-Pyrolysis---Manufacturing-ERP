"""
Sales Dispatch and Invoice Models - Physical movement and billing.

Workflow: SaleOrder → Dispatch (partial shipments) → Invoice (on demand)
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, Date, Boolean, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
from decimal import Decimal
import enum


class DispatchStatus(str, enum.Enum):
    PENDING = "PENDING"       # Dispatch created, truck loaded
    SHIPPED = "SHIPPED"       # Left the gate, stock deducted
    DELIVERED = "DELIVERED"   # Customer confirmed receipt
    CANCELLED = "CANCELLED"


class SalesDispatch(Base):
    """
    Sales Dispatch - Physical shipment from a Sale Order.
    One SO can have multiple dispatches (partial shipments).
    """
    __tablename__ = "sales_dispatches"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Dispatch Number - DC-YYYYMMDD-XXX
    dispatch_number = Column(String(30), unique=True, nullable=False, index=True)
    dispatch_date = Column(Date, nullable=False)
    
    # Parent Sale Order
    sale_order_id = Column(Integer, ForeignKey("sale_orders.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    
    # Status
    status = Column(String(20), default=DispatchStatus.PENDING.value)
    
    # Truck Details
    truck_number = Column(String(20), nullable=True)
    driver_name = Column(String(100), nullable=True)
    driver_phone = Column(String(15), nullable=True)
    
    # Gate Pass
    gate_pass_number = Column(String(30), nullable=True)
    gate_pass_time = Column(DateTime(timezone=True), nullable=True)
    is_returnable = Column(Boolean, default=False)  # For pallets/drums
    
    # E-Way Bill (GST transport document)
    eway_bill_number = Column(String(20), nullable=True)
    
    # Totals (calculated from items)
    total_quantity = Column(Numeric(12, 2), default=0)
    total_amount = Column(Numeric(14, 2), default=0)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Audit
    shipped_at = Column(DateTime(timezone=True), nullable=True)
    shipped_by = Column(String(100), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    items = relationship("SalesDispatchItem", back_populates="dispatch", cascade="all, delete-orphan")
    invoice = relationship("SalesInvoice", back_populates="dispatch", uselist=False)
    
    def __repr__(self):
        return f"<SalesDispatch {self.dispatch_number}: {self.status}>"


class SalesDispatchItem(Base):
    """Line item in a Dispatch - which items from SO are in this truck."""
    __tablename__ = "sales_dispatch_items"
    
    id = Column(Integer, primary_key=True, index=True)
    
    dispatch_id = Column(Integer, ForeignKey("sales_dispatches.id"), nullable=False)
    sale_order_item_id = Column(Integer, ForeignKey("sale_order_items.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Item Details
    description = Column(String(200), nullable=True)
    quantity = Column(Numeric(12, 2), nullable=False)  # Quantity in this truck
    unit = Column(String(10), default="KG")
    rate = Column(Numeric(10, 2), nullable=False)
    
    # Amounts (for this dispatch)
    amount = Column(Numeric(14, 2), nullable=False)
    hsn_code = Column(String(10), nullable=True)
    tax_rate = Column(Numeric(5, 2), default=18.0)
    tax_amount = Column(Numeric(12, 2), default=0)
    total_amount = Column(Numeric(14, 2), nullable=False)
    
    # Relationship
    dispatch = relationship("SalesDispatch", back_populates="items")
    
    def __repr__(self):
        return f"<SalesDispatchItem {self.id}: {self.quantity} units>"


class SalesInvoice(Base):
    """
    Tax Invoice - Generated separately after dispatch is created.
    One invoice per dispatch (can generate later for accountant).
    Follows Indian GST invoice format.
    """
    __tablename__ = "sales_invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Invoice Number - INV/YY-YY/XXX (e.g., INV/25-26/001)
    invoice_number = Column(String(30), unique=True, nullable=False, index=True)
    invoice_date = Column(Date, nullable=False)
    
    # Linked Dispatch
    dispatch_id = Column(Integer, ForeignKey("sales_dispatches.id"), nullable=False, unique=True)
    sale_order_id = Column(Integer, ForeignKey("sale_orders.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    
    # Seller Details (from company config)
    seller_name = Column(String(200), default="Tyre Pyrolysis Industries Pvt Ltd")
    seller_gstin = Column(String(20), nullable=True)
    seller_address = Column(Text, nullable=True)
    seller_state = Column(String(50), nullable=True)
    seller_state_code = Column(String(5), nullable=True)
    
    # Buyer Details (from customer)
    buyer_name = Column(String(200), nullable=True)
    buyer_gstin = Column(String(20), nullable=True)
    buyer_address = Column(Text, nullable=True)
    buyer_state = Column(String(50), nullable=True)
    buyer_state_code = Column(String(5), nullable=True)
    
    # Place of Supply (for IGST vs CGST+SGST)
    place_of_supply = Column(String(50), nullable=True)
    is_inter_state = Column(Boolean, default=False)  # If true, charge IGST; else CGST+SGST
    
    # Amounts
    subtotal = Column(Numeric(14, 2), default=0)
    cgst_amount = Column(Numeric(12, 2), default=0)  # Central GST
    sgst_amount = Column(Numeric(12, 2), default=0)  # State GST
    igst_amount = Column(Numeric(12, 2), default=0)  # Integrated GST (inter-state)
    total_tax = Column(Numeric(12, 2), default=0)
    grand_total = Column(Numeric(14, 2), default=0)
    amount_in_words = Column(String(500), nullable=True)
    
    # Payment
    payment_terms = Column(String(200), nullable=True)
    due_date = Column(Date, nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Audit
    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    dispatch = relationship("SalesDispatch", back_populates="invoice")
    
    def __repr__(self):
        return f"<SalesInvoice {self.invoice_number}>"
