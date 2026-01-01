"""
Sales Returns and Credit Notes Models.

Workflow: Return Request → Received → QC Check → (Pass/Fail) → Stock Update + Credit Note
Safety: Returned goods go to Quarantine first, not main inventory.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, Date, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
from decimal import Decimal
import enum


class ReturnStatus(str, enum.Enum):
    PENDING = "PENDING"       # Return requested, not yet received
    RECEIVED = "RECEIVED"     # Goods received, in quarantine
    QC_PASS = "QC_PASS"       # Quality passed, moved to main stock
    QC_FAIL = "QC_FAIL"       # Quality failed, moved to scrap
    CANCELLED = "CANCELLED"


class SalesReturn(Base):
    """
    Sales Return (RMA) - Customer returns goods.
    Linked to original Invoice for financial tracking.
    """
    __tablename__ = "sales_returns"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Return Number - RMA-YYYYMMDD-XXX
    return_number = Column(String(30), unique=True, nullable=False, index=True)
    return_date = Column(Date, nullable=False)
    
    # Link to original documents
    invoice_id = Column(Integer, ForeignKey("sales_invoices.id"), nullable=False)
    dispatch_id = Column(Integer, ForeignKey("sales_dispatches.id"), nullable=True)
    sale_order_id = Column(Integer, ForeignKey("sale_orders.id"), nullable=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    
    # Status
    status = Column(String(20), default=ReturnStatus.PENDING.value)
    
    # Return reason
    reason = Column(Text, nullable=True)
    reason_category = Column(String(50), nullable=True)  # QUALITY, DAMAGE, WRONG_PRODUCT, OTHER
    
    # Totals
    total_quantity = Column(Numeric(12, 2), default=0)
    total_amount = Column(Numeric(14, 2), default=0)
    
    # Quarantine tracking
    quarantine_location = Column(String(50), default="QUARANTINE")
    
    # QC Details
    qc_by = Column(String(100), nullable=True)
    qc_date = Column(DateTime(timezone=True), nullable=True)
    qc_notes = Column(Text, nullable=True)
    
    # Audit
    received_at = Column(DateTime(timezone=True), nullable=True)
    received_by = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    items = relationship("SalesReturnItem", back_populates="sales_return", cascade="all, delete-orphan")
    credit_note = relationship("CreditNote", back_populates="sales_return", uselist=False)
    
    def __repr__(self):
        return f"<SalesReturn {self.return_number}: {self.status}>"


class SalesReturnItem(Base):
    """Line item in a Sales Return."""
    __tablename__ = "sales_return_items"
    
    id = Column(Integer, primary_key=True, index=True)
    
    sales_return_id = Column(Integer, ForeignKey("sales_returns.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Original dispatch item reference
    dispatch_item_id = Column(Integer, ForeignKey("sales_dispatch_items.id"), nullable=True)
    
    # Item Details
    description = Column(String(200), nullable=True)
    quantity = Column(Numeric(12, 2), nullable=False)  # Quantity being returned
    unit = Column(String(10), default="KG")
    rate = Column(Numeric(10, 2), nullable=False)
    
    # Amounts (for credit note calculation)
    amount = Column(Numeric(14, 2), nullable=False)
    hsn_code = Column(String(10), nullable=True)
    tax_rate = Column(Numeric(5, 2), default=18.0)
    tax_amount = Column(Numeric(12, 2), default=0)
    total_amount = Column(Numeric(14, 2), nullable=False)
    
    # QC result per item
    qc_status = Column(String(20), nullable=True)  # PASS, FAIL
    qc_notes = Column(Text, nullable=True)
    
    # Stock destination after QC
    destination = Column(String(20), nullable=True)  # MAIN_STOCK, SCRAP
    
    # Relationship
    sales_return = relationship("SalesReturn", back_populates="items")
    
    def __repr__(self):
        return f"<SalesReturnItem {self.id}: {self.quantity} units>"


class CreditNote(Base):
    """
    Credit Note - Financial document reversing invoice value.
    Generated after QC is complete.
    """
    __tablename__ = "credit_notes"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Credit Note Number - CN-YYYY-XXXX
    credit_note_number = Column(String(30), unique=True, nullable=False, index=True)
    credit_note_date = Column(Date, nullable=False)
    
    # Link to return and original invoice
    sales_return_id = Column(Integer, ForeignKey("sales_returns.id"), nullable=False, unique=True)
    original_invoice_id = Column(Integer, ForeignKey("sales_invoices.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    
    # Reason
    reason = Column(Text, nullable=True)
    
    # Seller Details (copy from original)
    seller_name = Column(String(200), nullable=True)
    seller_gstin = Column(String(20), nullable=True)
    seller_address = Column(Text, nullable=True)
    seller_state = Column(String(50), nullable=True)
    seller_state_code = Column(String(5), nullable=True)
    
    # Buyer Details
    buyer_name = Column(String(200), nullable=True)
    buyer_gstin = Column(String(20), nullable=True)
    buyer_address = Column(Text, nullable=True)
    buyer_state = Column(String(50), nullable=True)
    buyer_state_code = Column(String(5), nullable=True)
    
    # Place of Supply
    place_of_supply = Column(String(50), nullable=True)
    is_inter_state = Column(Boolean, default=False)
    
    # Reversed Amounts (credited back to customer)
    subtotal = Column(Numeric(14, 2), default=0)
    cgst_amount = Column(Numeric(12, 2), default=0)
    sgst_amount = Column(Numeric(12, 2), default=0)
    igst_amount = Column(Numeric(12, 2), default=0)
    total_tax = Column(Numeric(12, 2), default=0)
    grand_total = Column(Numeric(14, 2), default=0)
    amount_in_words = Column(String(500), nullable=True)
    
    # Audit
    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    sales_return = relationship("SalesReturn", back_populates="credit_note")
    
    def __repr__(self):
        return f"<CreditNote {self.credit_note_number}>"
