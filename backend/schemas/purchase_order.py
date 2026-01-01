"""
Purchase Order Pydantic Schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime


class POItemCreate(BaseModel):
    """Schema for PO line item creation."""
    raw_material_id: int
    ordered_qty_kg: float = Field(..., gt=0)
    rate_per_kg: float = Field(..., ge=0)
    hsn_code: Optional[str] = "4004"
    gst_rate: float = Field(default=5.0, ge=0, le=28)


class POItemResponse(POItemCreate):
    """Schema for PO line item response."""
    id: int
    received_qty_kg: float = 0
    pending_qty_kg: Optional[float] = None
    line_amount: Optional[float] = None
    gst_amount: Optional[float] = None
    total_amount: Optional[float] = None
    
    class Config:
        from_attributes = True


class PurchaseOrderCreate(BaseModel):
    """Schema for creating purchase order."""
    vendor_id: int
    order_date: date
    expected_delivery_date: Optional[date] = None
    payment_terms: Optional[str] = None
    delivery_terms: Optional[str] = None
    notes: Optional[str] = None
    items: List[POItemCreate] = []


class PurchaseOrderResponse(BaseModel):
    """Schema for purchase order response."""
    id: int
    po_number: str
    vendor_id: int
    order_date: date
    expected_delivery_date: Optional[date] = None
    status: str
    subtotal_amount: Optional[float] = None
    cgst_amount: Optional[float] = None
    sgst_amount: Optional[float] = None
    igst_amount: Optional[float] = None
    total_amount: Optional[float] = None
    payment_terms: Optional[str] = None
    notes: Optional[str] = None
    items: List[POItemResponse] = []
    created_at: datetime
    
    class Config:
        from_attributes = True
