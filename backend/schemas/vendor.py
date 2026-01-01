"""
Vendor Pydantic Schemas - Request/Response validation.
Includes GSTIN validation pattern for Indian compliance.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime, date
import re


class VendorBase(BaseModel):
    """Base vendor fields shared across schemas."""
    name: str = Field(..., min_length=2, max_length=100)
    vendor_type: str = Field(default="DOMESTIC")
    
    # Contact
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    
    # Address
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "India"
    pincode: Optional[str] = None
    
    # GST Compliance
    gst_number: Optional[str] = Field(None, description="15-character GSTIN")
    gst_vendor_type: str = Field(default="REGULAR")
    pan_number: Optional[str] = Field(None, description="10-character PAN")
    
    # EPR Compliance
    epc_license_number: Optional[str] = None
    epc_validity_date: Optional[date] = None
    is_epr_compliant: bool = False
    
    # Banking
    bank_account_number: Optional[str] = None
    bank_ifsc_code: Optional[str] = None
    bank_name: Optional[str] = None
    
    # Terms
    credit_days: int = 0
    credit_limit: float = 0
    
    notes: Optional[str] = None
    
    @field_validator('gst_number')
    @classmethod
    def validate_gstin(cls, v):
        """
        Validate GSTIN format.
        Format: 2-digit state code + 10-char PAN + entity code + Z + check digit
        Example: 27AAPFU0939F1ZV
        """
        if v is None or v == "":
            return v
        
        # Remove spaces
        v = v.strip().upper()
        
        # Check length
        if len(v) != 15:
            raise ValueError('GSTIN must be exactly 15 characters')
        
        # Basic pattern: 2 digits + 10 alphanumeric + 1 alphanumeric + Z + 1 alphanumeric
        pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9A-Z]Z[0-9A-Z]$'
        if not re.match(pattern, v):
            raise ValueError('Invalid GSTIN format')
        
        return v
    
    @field_validator('pan_number')
    @classmethod
    def validate_pan(cls, v):
        """
        Validate PAN format.
        Format: 5 letters + 4 digits + 1 letter
        Example: ABCDE1234F
        """
        if v is None or v == "":
            return v
        
        v = v.strip().upper()
        
        if len(v) != 10:
            raise ValueError('PAN must be exactly 10 characters')
        
        pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]$'
        if not re.match(pattern, v):
            raise ValueError('Invalid PAN format')
        
        return v


class VendorCreate(VendorBase):
    """Schema for creating a new vendor."""
    pass


class VendorUpdate(BaseModel):
    """Schema for updating vendor - all fields optional."""
    name: Optional[str] = None
    vendor_type: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address_line1: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    gst_number: Optional[str] = None
    gst_vendor_type: Optional[str] = None
    epc_license_number: Optional[str] = None
    epc_validity_date: Optional[date] = None
    is_epr_compliant: Optional[bool] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class VendorResponse(BaseModel):
    """Schema for vendor response - no validation on output data."""
    id: int
    vendor_code: str
    name: str
    vendor_type: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    pincode: Optional[str] = None
    gst_number: Optional[str] = None  # No validation on response
    gst_vendor_type: Optional[str] = None
    pan_number: Optional[str] = None
    epc_license_number: Optional[str] = None
    epc_validity_date: Optional[date] = None
    is_epr_compliant: bool = False
    bank_account_number: Optional[str] = None
    bank_ifsc_code: Optional[str] = None
    bank_name: Optional[str] = None
    credit_days: Optional[int] = 0
    credit_limit: Optional[float] = 0
    notes: Optional[str] = None
    is_active: bool = True
    epr_status: str = "NON_COMPLIANT"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class VendorList(BaseModel):
    """Schema for vendor list response."""
    items: list[VendorResponse]
    total: int
    page: int
    page_size: int
