"""
Raw Material Pydantic Schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class RawMaterialBase(BaseModel):
    """Base raw material fields."""
    name: str = Field(..., min_length=2, max_length=100)
    material_type: str = Field(default="MIXED")
    
    # HSN
    hsn_code: str = Field(default="4004")
    gst_rate: float = Field(default=5.0, ge=0, le=28)
    
    # Stock
    minimum_stock_kg: float = Field(default=0, ge=0)
    
    # Quality Parameters
    average_rubber_content: Optional[float] = Field(None, ge=0, le=100)
    average_steel_content: Optional[float] = Field(None, ge=0, le=100)
    average_carbon_content: Optional[float] = Field(None, ge=0, le=100)
    moisture_content_max: Optional[float] = Field(None, ge=0, le=100)
    
    # Pricing
    standard_rate_per_kg: Optional[float] = Field(None, ge=0)
    
    # Storage
    storage_location: Optional[str] = None


class RawMaterialCreate(RawMaterialBase):
    """Schema for creating raw material."""
    pass


class RawMaterialResponse(RawMaterialBase):
    """Schema for raw material response."""
    id: int
    material_code: str
    current_stock_kg: float
    is_active: bool
    is_low_stock: bool = False
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
