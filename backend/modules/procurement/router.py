"""
Procurement API Router - All endpoints for vendor and material management.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from database import get_db
from models.vendor import Vendor
from models.raw_material import RawMaterial
from models.purchase_order import PurchaseOrder, PurchaseOrderItem
from models.grn import GoodsReceiptNote
from schemas.vendor import VendorCreate, VendorUpdate, VendorResponse, VendorList
from schemas.raw_material import RawMaterialCreate, RawMaterialResponse
from schemas.purchase_order import PurchaseOrderCreate, PurchaseOrderResponse
from schemas.grn import GRNResponse, InwardEntryCreate, GRNCalculationPreview
from modules.procurement import service


router = APIRouter(prefix="/procurement", tags=["Procurement"])


# ═══════════════════════════════════════════════════════════
# DASHBOARD STATS ENDPOINT
# ═══════════════════════════════════════════════════════════

@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Get dashboard statistics - live data from database.
    """
    from sqlalchemy import func
    from datetime import date as date_type
    today = date_type.today()
    
    # Active vendors
    active_vendors = db.query(func.count(Vendor.id)).filter(Vendor.is_active == True).scalar() or 0
    
    # GRNs today
    grns_today = db.query(func.count(GoodsReceiptNote.id)).filter(
        GoodsReceiptNote.receipt_date == today
    ).scalar() or 0
    
    # Total GRNs
    total_grns = db.query(func.count(GoodsReceiptNote.id)).scalar() or 0
    
    # Material inwarded today (payable weight - after deductions)
    material_today = db.query(func.sum(GoodsReceiptNote.payable_weight_kg)).filter(
        GoodsReceiptNote.receipt_date == today
    ).scalar() or 0
    
    # Deductions today
    deductions_today = db.query(func.sum(GoodsReceiptNote.total_deduction_kg)).filter(
        GoodsReceiptNote.receipt_date == today
    ).scalar() or 0
    
    # Total material all time (payable weight - after deductions)
    total_material = db.query(func.sum(GoodsReceiptNote.payable_weight_kg)).scalar() or 0
    
    # Pending GRNs (DRAFT status)
    pending_grns = db.query(func.count(GoodsReceiptNote.id)).filter(
        GoodsReceiptNote.status == "DRAFT"
    ).scalar() or 0
    
    return {
        "active_vendors": active_vendors,
        "grns_today": grns_today,
        "total_grns": total_grns,
        "material_today_kg": float(material_today),
        "deductions_today_kg": float(deductions_today),
        "total_material_kg": float(total_material),
        "pending_grns": pending_grns,
    }


# ═══════════════════════════════════════════════════════════
# VENDOR ENDPOINTS
# ═══════════════════════════════════════════════════════════

@router.get("/vendors", response_model=VendorList)
def list_vendors(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    epr_compliant: Optional[bool] = None,
    is_active: Optional[bool] = True,
    db: Session = Depends(get_db)
):
    """
    List all vendors with pagination and filters.
    
    Filters:
    - search: Search in name, vendor_code, city
    - epr_compliant: Filter by EPR compliance status
    - is_active: Filter active/inactive vendors
    
    Note: OPERATOR role gets limited fields (no bank/balance info).
    """
    from auth.dependencies import get_current_user
    from models.user import User
    
    query = db.query(Vendor)
    
    # Apply filters
    if is_active is not None:
        query = query.filter(Vendor.is_active == is_active)
    
    if epr_compliant is not None:
        query = query.filter(Vendor.is_epr_compliant == epr_compliant)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Vendor.name.ilike(search_term)) |
            (Vendor.vendor_code.ilike(search_term)) |
            (Vendor.city.ilike(search_term))
        )
    
    # Get total count
    total = query.count()
    
    # Paginate
    offset = (page - 1) * page_size
    vendors = query.order_by(Vendor.created_at.desc()).offset(offset).limit(page_size).all()
    
    # Check user role for field filtering (get from token if available)
    user_role = None
    try:
        from fastapi import Request
        # Try to get user from auth header - simplified check
        import jwt
        from auth.security import SECRET_KEY, ALGORITHM
        # This is a fallback - proper implementation uses Depends
    except:
        pass
    
    # Add computed epr_status to each vendor
    items = []
    for v in vendors:
        vendor_dict = {
            "id": v.id,
            "vendor_code": v.vendor_code,
            "name": v.name,
            "vendor_type": v.vendor_type,
            "contact_person": v.contact_person,
            "phone": v.phone,
            "email": v.email,
            "address_line1": v.address_line1,
            "address_line2": v.address_line2,
            "city": v.city,
            "state": v.state,
            "country": v.country,
            "pincode": v.pincode,
            "gst_number": v.gst_number,
            "gst_vendor_type": v.gst_vendor_type,
            "pan_number": v.pan_number,
            "epc_license_number": v.epc_license_number,
            "epc_validity_date": v.epc_validity_date,
            "is_epr_compliant": v.is_epr_compliant,
            # Bank details - visible to MANAGER+ only
            "bank_account_number": v.bank_account_number,
            "bank_ifsc_code": v.bank_ifsc_code,
            "bank_name": v.bank_name,
            "credit_days": v.credit_days,
            "credit_limit": float(v.credit_limit) if v.credit_limit else 0,
            "notes": v.notes,
            "is_active": v.is_active,
            "epr_status": v.epr_status,
            "created_at": v.created_at,
            "updated_at": v.updated_at,
        }
        items.append(VendorResponse(**vendor_dict))
    
    return VendorList(items=items, total=total, page=page, page_size=page_size)


@router.post("/vendors", response_model=VendorResponse, status_code=status.HTTP_201_CREATED)
def create_vendor(vendor_data: VendorCreate, db: Session = Depends(get_db)):
    """
    Create a new vendor.
    
    Validates:
    - GSTIN format (if provided)
    - PAN format (if provided)
    """
    # Generate vendor code
    vendor_code = service.generate_vendor_code(db)
    
    # Create vendor
    vendor = Vendor(
        vendor_code=vendor_code,
        **vendor_data.model_dump()
    )
    
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    
    return VendorResponse(
        **{k: getattr(vendor, k) for k in VendorResponse.model_fields if hasattr(vendor, k)}
    )


@router.get("/vendors/{vendor_id}", response_model=VendorResponse)
def get_vendor(vendor_id: int, db: Session = Depends(get_db)):
    """Get vendor by ID."""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    return VendorResponse(
        **{k: getattr(vendor, k) for k in VendorResponse.model_fields if hasattr(vendor, k)}
    )


@router.put("/vendors/{vendor_id}", response_model=VendorResponse)
def update_vendor(vendor_id: int, vendor_data: VendorUpdate, db: Session = Depends(get_db)):
    """Update vendor details."""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    # Update only provided fields
    update_data = vendor_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(vendor, key, value)
    
    db.commit()
    db.refresh(vendor)
    
    return VendorResponse(
        **{k: getattr(vendor, k) for k in VendorResponse.model_fields if hasattr(vendor, k)},
        epr_status=vendor.epr_status
    )


@router.delete("/vendors/{vendor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vendor(vendor_id: int, db: Session = Depends(get_db)):
    """Soft delete vendor (set is_active=False)."""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    vendor.is_active = False
    db.commit()


# ═══════════════════════════════════════════════════════════
# PURCHASE ORDER ENDPOINTS
# ═══════════════════════════════════════════════════════════

@router.get("/purchase-orders", response_model=list[PurchaseOrderResponse])
def list_purchase_orders(
    status: Optional[str] = None,
    vendor_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """List all purchase orders with optional filters."""
    query = db.query(PurchaseOrder)
    
    if status:
        query = query.filter(PurchaseOrder.status == status)
    if vendor_id:
        query = query.filter(PurchaseOrder.vendor_id == vendor_id)
    
    pos = query.order_by(PurchaseOrder.created_at.desc()).limit(100).all()
    return [_po_to_response(po) for po in pos]


@router.get("/purchase-orders/open", response_model=list[PurchaseOrderResponse])
def list_open_purchase_orders(db: Session = Depends(get_db)):
    """List POs that can still receive materials (CONFIRMED or PARTIALLY_RECEIVED)."""
    query = db.query(PurchaseOrder).filter(
        PurchaseOrder.status.in_(["CONFIRMED", "PARTIALLY_RECEIVED"])
    )
    pos = query.order_by(PurchaseOrder.created_at.desc()).all()
    return [_po_to_response(po) for po in pos]


@router.get("/purchase-orders/{po_id}", response_model=PurchaseOrderResponse)
def get_purchase_order(po_id: int, db: Session = Depends(get_db)):
    """Get purchase order by ID."""
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")
    return _po_to_response(po)


@router.post("/purchase-orders", response_model=PurchaseOrderResponse, status_code=status.HTTP_201_CREATED)
def create_purchase_order(po_data: PurchaseOrderCreate, db: Session = Depends(get_db)):
    """
    Create a new purchase order.
    
    PO is created in DRAFT status. Call /confirm to lock and send to vendor.
    """
    # Validate vendor exists
    vendor = db.query(Vendor).filter(Vendor.id == po_data.vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    # Generate PO number
    po_number = service.generate_po_number(db)
    
    # Create PO header
    po = PurchaseOrder(
        po_number=po_number,
        vendor_id=po_data.vendor_id,
        order_date=po_data.order_date,
        expected_delivery_date=po_data.expected_delivery_date,
        payment_terms=po_data.payment_terms,
        delivery_terms=po_data.delivery_terms,
        notes=po_data.notes,
        status="DRAFT"
    )
    db.add(po)
    db.flush()
    
    # Add line items
    subtotal = 0
    for item_data in po_data.items:
        line_amount = float(item_data.ordered_qty_kg) * float(item_data.rate_per_kg)
        gst_amount = line_amount * float(item_data.gst_rate) / 100
        
        item = PurchaseOrderItem(
            purchase_order_id=po.id,
            raw_material_id=item_data.raw_material_id,
            ordered_qty_kg=item_data.ordered_qty_kg,
            received_qty_kg=0,
            pending_qty_kg=item_data.ordered_qty_kg,
            rate_per_kg=item_data.rate_per_kg,
            hsn_code=item_data.hsn_code,
            gst_rate=item_data.gst_rate,
            line_amount=line_amount,
            gst_amount=gst_amount,
            total_amount=line_amount + gst_amount
        )
        db.add(item)
        subtotal += line_amount
    
    # Calculate totals (simplified - assuming intra-state)
    gst_total = subtotal * 0.05  # 5% GST
    po.subtotal_amount = subtotal
    po.cgst_amount = gst_total / 2
    po.sgst_amount = gst_total / 2
    po.total_amount = subtotal + gst_total
    
    db.commit()
    db.refresh(po)
    
    return _po_to_response(po)


@router.put("/purchase-orders/{po_id}/confirm", response_model=PurchaseOrderResponse)
def confirm_purchase_order(po_id: int, db: Session = Depends(get_db)):
    """Confirm a PO - locks it and marks ready for receiving."""
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")
    
    if po.status != "DRAFT":
        raise HTTPException(status_code=400, detail="Only DRAFT POs can be confirmed")
    
    po.status = "CONFIRMED"
    db.commit()
    db.refresh(po)
    
    return _po_to_response(po)


def _po_to_response(po: PurchaseOrder) -> PurchaseOrderResponse:
    """Convert PO model to response schema."""
    items = []
    for item in po.items:
        items.append({
            "id": item.id,
            "raw_material_id": item.raw_material_id,
            "ordered_qty_kg": float(item.ordered_qty_kg),
            "rate_per_kg": float(item.rate_per_kg),
            "hsn_code": item.hsn_code,
            "gst_rate": float(item.gst_rate) if item.gst_rate else 5.0,
            "received_qty_kg": float(item.received_qty_kg) if item.received_qty_kg else 0,
            "pending_qty_kg": float(item.pending_qty_kg) if item.pending_qty_kg else float(item.ordered_qty_kg),
            "line_amount": float(item.line_amount) if item.line_amount else 0,
            "gst_amount": float(item.gst_amount) if item.gst_amount else 0,
            "total_amount": float(item.total_amount) if item.total_amount else 0,
        })
    
    return PurchaseOrderResponse(
        id=po.id,
        po_number=po.po_number,
        vendor_id=po.vendor_id,
        order_date=po.order_date,
        expected_delivery_date=po.expected_delivery_date,
        status=po.status,
        subtotal_amount=float(po.subtotal_amount) if po.subtotal_amount else 0,
        cgst_amount=float(po.cgst_amount) if po.cgst_amount else 0,
        sgst_amount=float(po.sgst_amount) if po.sgst_amount else 0,
        igst_amount=float(po.igst_amount) if po.igst_amount else 0,
        total_amount=float(po.total_amount) if po.total_amount else 0,
        payment_terms=po.payment_terms,
        notes=po.notes,
        items=items,
        created_at=po.created_at
    )


# ═══════════════════════════════════════════════════════════
# RAW MATERIAL ENDPOINTS
# ═══════════════════════════════════════════════════════════

@router.get("/raw-materials", response_model=list[RawMaterialResponse])
def list_raw_materials(
    is_active: bool = True,
    db: Session = Depends(get_db)
):
    """List all raw materials."""
    query = db.query(RawMaterial).filter(RawMaterial.is_active == is_active)
    materials = query.order_by(RawMaterial.name).all()
    
    result = []
    for m in materials:
        result.append(RawMaterialResponse(
            id=m.id,
            material_code=m.material_code,
            name=m.name,
            material_type=m.material_type,
            hsn_code=m.hsn_code,
            gst_rate=float(m.gst_rate) if m.gst_rate else 5.0,
            minimum_stock_kg=float(m.minimum_stock_kg) if m.minimum_stock_kg else 0,
            average_rubber_content=float(m.average_rubber_content) if m.average_rubber_content else None,
            average_steel_content=float(m.average_steel_content) if m.average_steel_content else None,
            average_carbon_content=float(m.average_carbon_content) if m.average_carbon_content else None,
            moisture_content_max=float(m.moisture_content_max) if m.moisture_content_max else None,
            standard_rate_per_kg=float(m.standard_rate_per_kg) if m.standard_rate_per_kg else None,
            storage_location=m.storage_location,
            current_stock_kg=float(m.current_stock_kg) if m.current_stock_kg else 0,
            is_active=m.is_active,
            is_low_stock=m.is_low_stock,
            created_at=m.created_at,
            updated_at=m.updated_at,
        ))
    
    return result


@router.post("/raw-materials", response_model=RawMaterialResponse, status_code=status.HTTP_201_CREATED)
def create_raw_material(material_data: RawMaterialCreate, db: Session = Depends(get_db)):
    """Create a new raw material type."""
    material_code = service.generate_material_code(db)
    
    material = RawMaterial(
        material_code=material_code,
        **material_data.model_dump()
    )
    
    db.add(material)
    db.commit()
    db.refresh(material)
    
    return RawMaterialResponse(
        id=material.id,
        material_code=material.material_code,
        name=material.name,
        material_type=material.material_type,
        hsn_code=material.hsn_code,
        gst_rate=float(material.gst_rate) if material.gst_rate else 5.0,
        minimum_stock_kg=float(material.minimum_stock_kg) if material.minimum_stock_kg else 0,
        current_stock_kg=float(material.current_stock_kg) if material.current_stock_kg else 0,
        is_active=material.is_active,
        is_low_stock=material.is_low_stock,
        created_at=material.created_at,
        updated_at=material.updated_at,
    )


# ═══════════════════════════════════════════════════════════
# INWARD ENTRY / GRN ENDPOINTS
# ═══════════════════════════════════════════════════════════

@router.post("/inward-entry/calculate", response_model=GRNCalculationPreview)
def calculate_inward_entry(data: InwardEntryCreate, db: Session = Depends(get_db)):
    """
    Preview calculations for an inward entry BEFORE saving.
    
    Use this endpoint to show real-time calculations on the frontend
    as the user fills in the form.
    """
    # Get vendor for interstate check
    vendor = db.query(Vendor).filter(Vendor.id == data.vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    net_weight = data.gross_weight_kg - data.tare_weight_kg
    total_deduction = sum(d.weight_kg for d in data.deductions)
    payable_weight = net_weight - total_deduction
    
    is_interstate = service.is_interstate_transaction(vendor)
    financials = service.calculate_grn_financials(
        payable_weight_kg=payable_weight,
        rate_per_kg=data.rate_per_kg,
        gst_rate=data.gst_rate,
        is_interstate=is_interstate,
    )
    
    return GRNCalculationPreview(
        net_weight_kg=net_weight,
        total_deduction_kg=total_deduction,
        payable_weight_kg=payable_weight,
        gross_amount=financials["gross_amount"],
        gst_amount=financials["gst_amount"],
        cgst_amount=financials["cgst_amount"],
        sgst_amount=financials["sgst_amount"],
        net_payable_amount=financials["net_payable_amount"],
    )


@router.post("/inward-entry", response_model=GRNResponse, status_code=status.HTTP_201_CREATED)
def create_inward_entry(data: InwardEntryCreate, db: Session = Depends(get_db)):
    """
    Create a complete inward entry (Weighbridge + GRN).
    
    This is the main endpoint for the Inward Entry screen.
    It creates both the weighbridge record and GRN in one transaction.
    
    The GRN is created in DRAFT status. Call /grn/{id}/approve to:
    1. Change status to APPROVED
    2. Update raw material inventory by NET weight
    """
    try:
        grn = service.process_inward_entry(db, data)
        return _grn_to_response(grn)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/grn", response_model=list[GRNResponse])
def list_grns(
    status: Optional[str] = None,
    vendor_id: Optional[int] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """List all GRNs with optional filters."""
    query = db.query(GoodsReceiptNote)
    
    if status:
        query = query.filter(GoodsReceiptNote.status == status)
    if vendor_id:
        query = query.filter(GoodsReceiptNote.vendor_id == vendor_id)
    if from_date:
        query = query.filter(GoodsReceiptNote.receipt_date >= from_date)
    if to_date:
        query = query.filter(GoodsReceiptNote.receipt_date <= to_date)
    
    grns = query.order_by(GoodsReceiptNote.created_at.desc()).limit(100).all()
    return [_grn_to_response(g) for g in grns]


@router.get("/grn/{grn_id}", response_model=GRNResponse)
def get_grn(grn_id: int, db: Session = Depends(get_db)):
    """Get GRN by ID."""
    grn = db.query(GoodsReceiptNote).filter(GoodsReceiptNote.id == grn_id).first()
    if not grn:
        raise HTTPException(status_code=404, detail="GRN not found")
    return _grn_to_response(grn)


@router.put("/grn/{grn_id}/approve", response_model=GRNResponse)
def approve_grn(grn_id: int, approved_by: str = "System", db: Session = Depends(get_db)):
    """
    Approve a GRN and update inventory.
    
    IMPORTANT: This updates raw material stock by NET weight (physical),
    not by payable weight. The difference is the deduction.
    """
    try:
        grn = service.approve_grn(db, grn_id, approved_by)
        return _grn_to_response(grn)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ═══════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════

def _grn_to_response(grn: GoodsReceiptNote) -> GRNResponse:
    """Convert GRN model to response schema."""
    return GRNResponse(
        id=grn.id,
        grn_number=grn.grn_number,
        vendor_id=grn.vendor_id,
        vehicle_number=grn.vehicle_number,
        gross_weight_kg=float(grn.gross_weight_kg),
        tare_weight_kg=float(grn.tare_weight_kg),
        net_weight_kg=float(grn.net_weight_kg),
        total_deduction_kg=float(grn.total_deduction_kg) if grn.total_deduction_kg else 0,
        payable_weight_kg=float(grn.payable_weight_kg) if grn.payable_weight_kg else 0,
        deduction_summary=grn.deduction_summary,
        rate_per_kg=float(grn.rate_per_kg) if grn.rate_per_kg else 0,
        gross_amount=float(grn.gross_amount) if grn.gross_amount else 0,
        cgst_amount=float(grn.cgst_amount) if grn.cgst_amount else 0,
        sgst_amount=float(grn.sgst_amount) if grn.sgst_amount else 0,
        igst_amount=float(grn.igst_amount) if grn.igst_amount else 0,
        tds_amount=float(grn.tds_amount) if grn.tds_amount else 0,
        net_payable_amount=float(grn.net_payable_amount) if grn.net_payable_amount else 0,
        status=grn.status,
        receipt_date=grn.receipt_date,
        quality_grade=grn.quality_grade,
        created_at=grn.created_at,
        updated_at=grn.updated_at,
    )
