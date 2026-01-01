"""
Vendor Model - Tracks suppliers of scrap tyres.
Includes Indian GST and EPR (Extended Producer Responsibility) compliance fields.

Indian Compliance Notes:
- GSTIN: 15-character alphanumeric (e.g., 27AAPFU0939F1ZV)
- Format: [State Code][PAN][Entity Number][Z][Check Digit]
- EPC License: Authorization from CPCB/SPCB for waste tyre handling
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, Date, Enum as SQLEnum
from sqlalchemy.sql import func
from database import Base
import enum


class VendorType(str, enum.Enum):
    """Vendor classification."""
    DOMESTIC = "DOMESTIC"
    INTERNATIONAL = "INTERNATIONAL"


class GSTVendorType(str, enum.Enum):
    """
    GST registration types as per Indian GST law.
    This affects input tax credit eligibility.
    """
    REGULAR = "REGULAR"          # Normal registered dealer - full ITC available
    COMPOSITION = "COMPOSITION"  # Composition scheme - no ITC, 1-5% tax
    UNREGISTERED = "UNREGISTERED"  # Below threshold - reverse charge may apply
    SEZ = "SEZ"                  # Special Economic Zone - zero-rated


class Vendor(Base):
    """
    Vendor/Supplier master table.
    
    Critical for:
    - Scrap tyre procurement (primary raw material)
    - EPR compliance tracking (mandatory for waste processors)
    - GST input tax credit management
    """
    __tablename__ = "vendors"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    vendor_code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    vendor_type = Column(String(20), nullable=False, default=VendorType.DOMESTIC.value)
    
    # Contact Information
    contact_person = Column(String(100))
    phone = Column(String(20))
    email = Column(String(100))
    
    # Address
    address_line1 = Column(String(200))
    address_line2 = Column(String(200))
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100), default="India")
    pincode = Column(String(10))
    
    # ═══════════════════════════════════════════════════════════
    # INDIAN GST COMPLIANCE
    # ═══════════════════════════════════════════════════════════
    gst_number = Column(String(20), index=True)  # GSTIN - 15 chars
    gst_vendor_type = Column(String(30), default=GSTVendorType.REGULAR.value)
    pan_number = Column(String(15))  # PAN - 10 chars (AAAAA0000A format)
    
    # ═══════════════════════════════════════════════════════════
    # EPR COMPLIANCE (Extended Producer Responsibility)
    # Mandatory for entities handling waste tyres in India
    # ═══════════════════════════════════════════════════════════
    epc_license_number = Column(String(30))  # EPC Authorization from CPCB/SPCB
    epc_validity_date = Column(Date)  # License expiry date
    is_epr_compliant = Column(Boolean, default=False)  # Quick compliance flag
    
    # Banking Details
    bank_account_number = Column(String(30))
    bank_ifsc_code = Column(String(15))
    bank_name = Column(String(100))
    
    # For International Vendors
    import_export_code = Column(String(20))  # IEC for international trade
    currency = Column(String(3), default="INR")
    
    # Status & Rating
    is_active = Column(Boolean, default=True)
    rating = Column(Integer)  # 1-5 stars
    notes = Column(String(500))
    
    # Credit Terms
    credit_days = Column(Integer, default=0)  # Payment terms (e.g., 30 days)
    credit_limit = Column(Numeric(14, 2), default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Vendor {self.vendor_code}: {self.name}>"
    
    @property
    def is_gst_registered(self) -> bool:
        """Check if vendor has valid GST registration."""
        return bool(self.gst_number and len(self.gst_number) == 15)
    
    @property
    def epr_status(self) -> str:
        """Get EPR compliance status for UI display."""
        if self.is_epr_compliant and self.epc_license_number:
            return "COMPLIANT"
        elif self.epc_license_number and not self.is_epr_compliant:
            return "PENDING_VERIFICATION"
        else:
            return "NON_COMPLIANT"
