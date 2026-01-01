"""
GRN (Goods Receipt Note) Pydantic Schemas.
Includes the critical InwardEntry combined schema for the frontend form.
"""
from pydantic import BaseModel, Field, computed_field
from typing import Optional, List
from datetime import date, datetime


class DeductionEntry(BaseModel):
    """Schema for a single deduction entry."""
    type: str = Field(..., description="Deduction type: MUD, WATER, RIMS, etc.")
    weight_kg: float = Field(..., ge=0, description="Deduction weight in kg")
    reason: Optional[str] = Field(None, description="Explanation for deduction")


class GRNBase(BaseModel):
    """Base GRN fields."""
    vendor_id: int
    raw_material_id: Optional[int] = None
    purchase_order_id: Optional[int] = None
    
    receipt_date: date
    material_description: Optional[str] = None
    
    # Rate
    rate_per_kg: float = Field(..., ge=0)
    gst_rate: float = Field(default=5.0, ge=0, le=28)
    
    # Quality
    moisture_content_pct: Optional[float] = Field(None, ge=0, le=100)
    quality_grade: Optional[str] = None
    quality_remarks: Optional[str] = None


class GRNCreate(GRNBase):
    """Schema for creating GRN (separate from weighbridge)."""
    weighbridge_record_id: int
    
    # Deductions
    deduction_1_type: Optional[str] = None
    deduction_1_weight_kg: float = 0
    deduction_1_reason: Optional[str] = None
    
    deduction_2_type: Optional[str] = None
    deduction_2_weight_kg: float = 0
    deduction_2_reason: Optional[str] = None
    
    deduction_3_type: Optional[str] = None
    deduction_3_weight_kg: float = 0
    deduction_3_reason: Optional[str] = None


class InwardEntryCreate(BaseModel):
    """
    Combined schema for Inward Entry Screen.
    This captures both weighbridge and GRN data in one form submission.
    
    Used by the frontend "Inward Entry" screen to record:
    1. Vehicle arrival with weights
    2. Quality assessment
    3. Deductions for mud/water/rims
    4. Auto-calculated payable weight
    """
    # Vehicle & Driver
    vehicle_number: str = Field(..., min_length=4, max_length=20)
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    
    # Vendor & Material
    vendor_id: int
    raw_material_id: Optional[int] = None
    purchase_order_id: Optional[int] = None
    material_description: Optional[str] = None
    
    # Weights
    gross_weight_kg: float = Field(..., gt=0)
    tare_weight_kg: float = Field(..., ge=0)
    
    # Rate & GST
    rate_per_kg: float = Field(..., ge=0)
    gst_rate: float = Field(default=5.0, ge=0, le=28)
    
    # Deductions (simplified list format for frontend)
    deductions: List[DeductionEntry] = []
    
    # Quality
    moisture_content_pct: Optional[float] = Field(None, ge=0, le=100)
    quality_grade: Optional[str] = None
    quality_remarks: Optional[str] = None
    
    # Reference
    vendor_slip_number: Optional[str] = None
    remarks: Optional[str] = None
    
    @computed_field
    @property
    def net_weight_kg(self) -> float:
        """Auto-calculate net weight."""
        return self.gross_weight_kg - self.tare_weight_kg
    
    @computed_field
    @property
    def total_deduction_kg(self) -> float:
        """Sum of all deductions."""
        return sum(d.weight_kg for d in self.deductions)
    
    @computed_field
    @property
    def payable_weight_kg(self) -> float:
        """Net weight minus deductions = what vendor gets paid for."""
        return self.net_weight_kg - self.total_deduction_kg
    
    @computed_field
    @property
    def gross_amount(self) -> float:
        """Taxable amount before GST."""
        return self.payable_weight_kg * self.rate_per_kg


class GRNResponse(BaseModel):
    """Schema for GRN response."""
    id: int
    grn_number: str
    vendor_id: int
    vehicle_number: Optional[str] = None
    
    # Weights
    gross_weight_kg: float
    tare_weight_kg: float
    net_weight_kg: float
    
    # Deductions
    total_deduction_kg: float
    payable_weight_kg: float
    deduction_summary: List[dict] = []
    
    # Financials
    rate_per_kg: float
    gross_amount: float
    cgst_amount: float
    sgst_amount: float
    igst_amount: float
    tds_amount: float
    net_payable_amount: float
    
    # Status
    status: str
    receipt_date: date
    quality_grade: Optional[str] = None
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class GRNCalculationPreview(BaseModel):
    """
    Preview schema for frontend real-time calculations.
    Returns calculated values before saving.
    """
    net_weight_kg: float
    total_deduction_kg: float
    payable_weight_kg: float
    gross_amount: float
    gst_amount: float
    cgst_amount: float
    sgst_amount: float
    net_payable_amount: float
