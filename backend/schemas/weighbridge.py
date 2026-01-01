"""
Weighbridge Pydantic Schemas.
"""
from pydantic import BaseModel, Field, computed_field
from typing import Optional
from datetime import datetime


class WeighbridgeBase(BaseModel):
    """Base weighbridge fields."""
    vehicle_number: str = Field(..., min_length=4, max_length=20)
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    
    material_type: Optional[str] = None
    weighment_type: str = Field(default="INWARD")
    
    notes: Optional[str] = None


class WeighbridgeCreate(WeighbridgeBase):
    """Schema for creating weighbridge record."""
    gross_weight_kg: Optional[float] = Field(None, ge=0)
    tare_weight_kg: Optional[float] = Field(None, ge=0)
    estimated_deduction_kg: float = Field(default=0, ge=0)
    deduction_reason: Optional[str] = None


class WeighbridgeUpdate(BaseModel):
    """Schema for updating weighbridge (second weighment)."""
    tare_weight_kg: float = Field(..., ge=0)


class WeighbridgeResponse(WeighbridgeBase):
    """Schema for weighbridge response."""
    id: int
    ticket_number: str
    gross_weight_kg: Optional[float] = None
    tare_weight_kg: Optional[float] = None
    net_weight_kg: Optional[float] = None
    estimated_deduction_kg: float = 0
    deduction_reason: Optional[str] = None
    status: str
    first_weight_datetime: Optional[datetime] = None
    second_weight_datetime: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
