"""
Goods Receipt Note (GRN) Model - THE CRITICAL PROCUREMENT DOCUMENT.

This is where the complex deduction logic lives:
1. Net Weight = Gross - Tare (physical material received)
2. Total Deduction = Sum of all deductions (mud, water, rims, etc.)
3. Payable Weight = Net Weight - Total Deduction (financial liability)

IMPORTANT DISTINCTION:
- Inventory increases by NET WEIGHT (actual physical material)
- Financial liability is based on PAYABLE WEIGHT (after deductions)

Indian Compliance:
- GST calculated on payable weight × rate
- TDS may apply on certain vendor categories
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, Date, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum
from decimal import Decimal


class DeductionType(str, enum.Enum):
    """
    Common deduction types in scrap tyre procurement.
    These affect payable weight but NOT physical inventory.
    """
    MUD = "MUD"                      # Mud/dirt stuck on tyres
    WATER = "WATER"                  # Water-logged tyres
    RIMS = "RIMS"                    # Steel rims not separated
    SAND = "SAND"                    # Sand/gravel
    FOREIGN_MATERIAL = "FOREIGN_MATERIAL"  # Non-tyre materials
    EXCESS_MOISTURE = "EXCESS_MOISTURE"    # Abnormal water content
    QUALITY_REJECTION = "QUALITY_REJECTION"  # Poor quality portion
    OTHER = "OTHER"


class GRNStatus(str, enum.Enum):
    """GRN workflow status."""
    DRAFT = "DRAFT"                  # Initial entry
    INSPECTED = "INSPECTED"          # Quality check done
    APPROVED = "APPROVED"            # Manager approved
    REJECTED = "REJECTED"            # Material rejected
    PAID = "PAID"                    # Payment done


class GoodsReceiptNote(Base):
    """
    Goods Receipt Note - The master document for material receipt.
    
    Business Logic:
    ═══════════════════════════════════════════════════════════
    1. Weighbridge captures Gross & Tare weights
    2. Inspector assesses quality and identifies deductions
    3. GRN calculates:
       - net_weight_kg = gross_weight - tare_weight
       - total_deduction_kg = deduction_1 + deduction_2 + deduction_3
       - payable_weight_kg = net_weight - total_deduction
       - gross_amount = payable_weight × rate_per_kg
       - GST calculation based on vendor type (intra/inter state)
       - net_payable = gross + GST - TDS
    4. On approval:
       - Inventory increases by NET weight (physical)
       - Accounts payable increases by NET PAYABLE amount
    ═══════════════════════════════════════════════════════════
    """
    __tablename__ = "goods_receipt_notes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    grn_number = Column(String(30), unique=True, nullable=False, index=True)
    
    # References
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"))
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    weighbridge_record_id = Column(Integer, ForeignKey("weighbridge_records.id"))
    raw_material_id = Column(Integer, ForeignKey("raw_materials.id"))
    
    # Receipt Details
    receipt_date = Column(Date, nullable=False)
    receipt_datetime = Column(DateTime(timezone=True), nullable=False)
    material_description = Column(String(200))
    
    # Vehicle Details (copied from weighbridge for reference)
    vehicle_number = Column(String(20))
    driver_name = Column(String(100))
    
    # ═══════════════════════════════════════════════════════════
    # WEIGHTS FROM WEIGHBRIDGE
    # ═══════════════════════════════════════════════════════════
    gross_weight_kg = Column(Numeric(12, 2), nullable=False)
    tare_weight_kg = Column(Numeric(12, 2), nullable=False)
    net_weight_kg = Column(Numeric(12, 2), nullable=False)  # Auto: gross - tare
    
    # ═══════════════════════════════════════════════════════════
    # PROCUREMENT DEDUCTIONS (The Critical Part)
    # ═══════════════════════════════════════════════════════════
    # Deduction 1
    deduction_1_type = Column(String(30))  # From DeductionType enum
    deduction_1_weight_kg = Column(Numeric(10, 2), default=0)
    deduction_1_reason = Column(String(200))
    
    # Deduction 2
    deduction_2_type = Column(String(30))
    deduction_2_weight_kg = Column(Numeric(10, 2), default=0)
    deduction_2_reason = Column(String(200))
    
    # Deduction 3
    deduction_3_type = Column(String(30))
    deduction_3_weight_kg = Column(Numeric(10, 2), default=0)
    deduction_3_reason = Column(String(200))
    
    # Calculated Totals
    total_deduction_kg = Column(Numeric(12, 2), default=0)  # Sum of all deductions
    
    # ═══════════════════════════════════════════════════════════
    # NET PAYABLE WEIGHT (Financial Liability)
    # This is what we pay the vendor for
    # ═══════════════════════════════════════════════════════════
    payable_weight_kg = Column(Numeric(12, 2))  # net_weight - total_deduction
    
    # ═══════════════════════════════════════════════════════════
    # FINANCIAL CALCULATIONS
    # ═══════════════════════════════════════════════════════════
    rate_per_kg = Column(Numeric(10, 2))
    hsn_code = Column(String(10), default="4004")
    gst_rate = Column(Numeric(4, 2), default=5.0)  # Usually 5% for waste
    
    gross_amount = Column(Numeric(14, 2))  # payable_weight × rate
    
    # GST Split (for Indian compliance)
    cgst_amount = Column(Numeric(12, 2), default=0)  # Central GST (intra-state)
    sgst_amount = Column(Numeric(12, 2), default=0)  # State GST (intra-state)
    igst_amount = Column(Numeric(12, 2), default=0)  # Integrated GST (inter-state)
    
    # TDS (Tax Deducted at Source)
    tds_rate = Column(Numeric(4, 2), default=0)
    tds_amount = Column(Numeric(12, 2), default=0)
    
    # Final Amount
    net_payable_amount = Column(Numeric(14, 2))  # gross + GST - TDS
    
    # ═══════════════════════════════════════════════════════════
    # QUALITY ASSESSMENT
    # ═══════════════════════════════════════════════════════════
    moisture_content_pct = Column(Numeric(5, 2))
    quality_grade = Column(String(10))  # A, B, C
    quality_remarks = Column(String(500))
    
    # Inspection
    inspected_by = Column(String(100))
    inspection_datetime = Column(DateTime(timezone=True))
    inspection_photos = Column(String(500))  # Comma-separated paths
    
    # Approval
    status = Column(String(20), default=GRNStatus.DRAFT.value)
    approved_by = Column(String(100))
    approved_datetime = Column(DateTime(timezone=True))
    
    # Inventory Update Flag
    inventory_updated = Column(Boolean, default=False)  # True after stock increase
    
    # Reference Numbers
    vendor_slip_number = Column(String(50))  # Vendor's delivery challan
    remarks = Column(String(500))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<GRN {self.grn_number}: {self.vehicle_number}>"
    
    def calculate_deductions(self) -> Decimal:
        """
        Calculate total deductions from all deduction fields.
        
        Returns:
            Total deduction in kg
        """
        d1 = Decimal(str(self.deduction_1_weight_kg or 0))
        d2 = Decimal(str(self.deduction_2_weight_kg or 0))
        d3 = Decimal(str(self.deduction_3_weight_kg or 0))
        
        self.total_deduction_kg = d1 + d2 + d3
        return self.total_deduction_kg
    
    def calculate_payable_weight(self) -> Decimal:
        """
        Calculate payable weight after deductions.
        
        Formula: payable_weight = net_weight - total_deduction
        
        IMPORTANT: This is what the vendor gets paid for.
        Physical inventory still increases by net_weight.
        """
        net = Decimal(str(self.net_weight_kg or 0))
        deduction = self.calculate_deductions()
        
        self.payable_weight_kg = net - deduction
        return self.payable_weight_kg
    
    def calculate_financials(self, is_interstate: bool = False) -> dict:
        """
        Calculate all financial fields including GST.
        
        Args:
            is_interstate: True if vendor is from different state
                          (determines IGST vs CGST+SGST split)
        
        Returns:
            Dictionary with all calculated amounts
        """
        payable = self.calculate_payable_weight()
        rate = Decimal(str(self.rate_per_kg or 0))
        gst_rate = Decimal(str(self.gst_rate or 0))
        tds_rate = Decimal(str(self.tds_rate or 0))
        
        # Gross amount (taxable value)
        self.gross_amount = payable * rate
        
        # GST calculation
        gst_amount = (self.gross_amount * gst_rate) / Decimal("100")
        
        if is_interstate:
            # Inter-state: Full IGST
            self.igst_amount = gst_amount
            self.cgst_amount = Decimal("0")
            self.sgst_amount = Decimal("0")
        else:
            # Intra-state: Split CGST + SGST
            half_gst = gst_amount / Decimal("2")
            self.cgst_amount = half_gst
            self.sgst_amount = half_gst
            self.igst_amount = Decimal("0")
        
        # TDS calculation (if applicable)
        self.tds_amount = (self.gross_amount * tds_rate) / Decimal("100")
        
        # Net payable to vendor
        total_gst = self.cgst_amount + self.sgst_amount + self.igst_amount
        self.net_payable_amount = self.gross_amount + total_gst - self.tds_amount
        
        return {
            "gross_amount": float(self.gross_amount),
            "cgst": float(self.cgst_amount),
            "sgst": float(self.sgst_amount),
            "igst": float(self.igst_amount),
            "tds": float(self.tds_amount),
            "net_payable": float(self.net_payable_amount),
        }
    
    @property
    def deduction_summary(self) -> list:
        """Get list of non-zero deductions for UI display."""
        deductions = []
        if self.deduction_1_weight_kg and float(self.deduction_1_weight_kg) > 0:
            deductions.append({
                "type": self.deduction_1_type,
                "weight": float(self.deduction_1_weight_kg),
                "reason": self.deduction_1_reason
            })
        if self.deduction_2_weight_kg and float(self.deduction_2_weight_kg) > 0:
            deductions.append({
                "type": self.deduction_2_type,
                "weight": float(self.deduction_2_weight_kg),
                "reason": self.deduction_2_reason
            })
        if self.deduction_3_weight_kg and float(self.deduction_3_weight_kg) > 0:
            deductions.append({
                "type": self.deduction_3_type,
                "weight": float(self.deduction_3_weight_kg),
                "reason": self.deduction_3_reason
            })
        return deductions
