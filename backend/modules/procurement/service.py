"""
Procurement Service Layer - Business Logic for GRN and Vendor Operations.

Contains the critical deduction and GST calculation logic.
"""
from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import Optional
from decimal import Decimal

from models.vendor import Vendor
from models.raw_material import RawMaterial
from models.weighbridge import WeighbridgeRecord
from models.grn import GoodsReceiptNote, GRNStatus
from models.purchase_order import PurchaseOrder, PurchaseOrderItem
from models.inventory_lot import InventoryLot
from schemas.grn import InwardEntryCreate, DeductionEntry


def generate_vendor_code(db: Session) -> str:
    """Generate next vendor code like VND-0001."""
    last = db.query(Vendor).order_by(Vendor.id.desc()).first()
    next_num = (last.id + 1) if last else 1
    return f"VND-{next_num:04d}"


def generate_material_code(db: Session) -> str:
    """Generate next material code like RM-0001."""
    last = db.query(RawMaterial).order_by(RawMaterial.id.desc()).first()
    next_num = (last.id + 1) if last else 1
    return f"RM-{next_num:04d}"


def generate_ticket_number(db: Session) -> str:
    """Generate weighbridge ticket number like WB-20251231-0001."""
    today = date.today().strftime("%Y%m%d")
    prefix = f"WB-{today}-"
    
    # Count today's tickets
    count = db.query(WeighbridgeRecord).filter(
        WeighbridgeRecord.ticket_number.like(f"{prefix}%")
    ).count()
    
    return f"{prefix}{count + 1:04d}"


def generate_grn_number(db: Session) -> str:
    """Generate GRN number like GRN-2025-0001."""
    year = date.today().year
    prefix = f"GRN-{year}-"
    
    count = db.query(GoodsReceiptNote).filter(
        GoodsReceiptNote.grn_number.like(f"{prefix}%")
    ).count()
    
    return f"{prefix}{count + 1:04d}"


def generate_po_number(db: Session) -> str:
    """Generate PO number like PO-2025-0001."""
    year = date.today().year
    prefix = f"PO-{year}-"
    
    count = db.query(PurchaseOrder).filter(
        PurchaseOrder.po_number.like(f"{prefix}%")
    ).count()
    
    return f"{prefix}{count + 1:04d}"


def is_interstate_transaction(vendor: Vendor, plant_state: str = "Maharashtra") -> bool:
    """
    Determine if transaction is inter-state for GST purposes.
    
    Inter-state: IGST applies (full rate)
    Intra-state: CGST + SGST applies (split 50-50)
    """
    if not vendor.state:
        return False  # Default to intra-state if unknown
    return vendor.state.lower().strip() != plant_state.lower().strip()


def calculate_grn_financials(
    payable_weight_kg: float,
    rate_per_kg: float,
    gst_rate: float,
    is_interstate: bool = False,
    tds_rate: float = 0
) -> dict:
    """
    Calculate all financial components for a GRN.
    
    Args:
        payable_weight_kg: Weight after deductions (financial basis)
        rate_per_kg: Rate per kg
        gst_rate: GST rate percentage
        is_interstate: True for IGST, False for CGST+SGST split
        tds_rate: TDS rate if applicable
    
    Returns:
        dict with all calculated amounts
    """
    payable = Decimal(str(payable_weight_kg))
    rate = Decimal(str(rate_per_kg))
    gst_pct = Decimal(str(gst_rate))
    tds_pct = Decimal(str(tds_rate))
    
    # Taxable amount
    gross_amount = payable * rate
    
    # GST calculation
    gst_amount = (gross_amount * gst_pct) / Decimal("100")
    
    if is_interstate:
        igst = gst_amount
        cgst = Decimal("0")
        sgst = Decimal("0")
    else:
        igst = Decimal("0")
        cgst = gst_amount / Decimal("2")
        sgst = gst_amount / Decimal("2")
    
    # TDS (Tax Deducted at Source) - deducted from vendor payment
    tds = (gross_amount * tds_pct) / Decimal("100")
    
    # Net payable to vendor
    net_payable = gross_amount + cgst + sgst + igst - tds
    
    return {
        "gross_amount": float(gross_amount),
        "gst_amount": float(gst_amount),
        "cgst_amount": float(cgst),
        "sgst_amount": float(sgst),
        "igst_amount": float(igst),
        "tds_amount": float(tds),
        "net_payable_amount": float(net_payable),
    }


def process_inward_entry(db: Session, data: InwardEntryCreate) -> GoodsReceiptNote:
    """
    Process complete inward entry - creates weighbridge record and GRN.
    
    This is the main business logic that:
    1. Creates weighbridge record with weights
    2. Creates GRN with deductions
    3. Calculates payable weight and financials
    4. Does NOT update inventory (that happens on approval)
    
    Returns:
        Created GRN object
    """
    # Get vendor for interstate check
    vendor = db.query(Vendor).filter(Vendor.id == data.vendor_id).first()
    if not vendor:
        raise ValueError(f"Vendor {data.vendor_id} not found")
    
    # Create Weighbridge Record
    wb = WeighbridgeRecord(
        ticket_number=generate_ticket_number(db),
        vehicle_number=data.vehicle_number,
        driver_name=data.driver_name,
        driver_phone=data.driver_phone,
        gross_weight_kg=data.gross_weight_kg,
        tare_weight_kg=data.tare_weight_kg,
        net_weight_kg=data.gross_weight_kg - data.tare_weight_kg,
        weighment_type="INWARD",
        material_type=data.material_description,
        first_weight_datetime=datetime.now(),
        second_weight_datetime=datetime.now(),
        status="COMPLETED",
    )
    db.add(wb)
    db.flush()  # Get ID
    
    # Calculate deduction totals
    total_deduction = sum(d.weight_kg for d in data.deductions)
    net_weight = data.gross_weight_kg - data.tare_weight_kg
    payable_weight = net_weight - total_deduction
    
    # Create GRN
    grn = GoodsReceiptNote(
        grn_number=generate_grn_number(db),
        vendor_id=data.vendor_id,
        raw_material_id=data.raw_material_id,
        purchase_order_id=data.purchase_order_id,
        weighbridge_record_id=wb.id,
        receipt_date=date.today(),
        receipt_datetime=datetime.now(),
        vehicle_number=data.vehicle_number,
        driver_name=data.driver_name,
        material_description=data.material_description,
        
        # Weights
        gross_weight_kg=data.gross_weight_kg,
        tare_weight_kg=data.tare_weight_kg,
        net_weight_kg=net_weight,
        
        # Deductions - map from list to individual fields
        deduction_1_type=data.deductions[0].type if len(data.deductions) > 0 else None,
        deduction_1_weight_kg=data.deductions[0].weight_kg if len(data.deductions) > 0 else 0,
        deduction_1_reason=data.deductions[0].reason if len(data.deductions) > 0 else None,
        
        deduction_2_type=data.deductions[1].type if len(data.deductions) > 1 else None,
        deduction_2_weight_kg=data.deductions[1].weight_kg if len(data.deductions) > 1 else 0,
        deduction_2_reason=data.deductions[1].reason if len(data.deductions) > 1 else None,
        
        deduction_3_type=data.deductions[2].type if len(data.deductions) > 2 else None,
        deduction_3_weight_kg=data.deductions[2].weight_kg if len(data.deductions) > 2 else 0,
        deduction_3_reason=data.deductions[2].reason if len(data.deductions) > 2 else None,
        
        total_deduction_kg=total_deduction,
        payable_weight_kg=payable_weight,
        
        # Rate & GST
        rate_per_kg=data.rate_per_kg,
        gst_rate=data.gst_rate,
        
        # Quality
        moisture_content_pct=data.moisture_content_pct,
        quality_grade=data.quality_grade,
        quality_remarks=data.quality_remarks,
        
        # Reference
        vendor_slip_number=data.vendor_slip_number,
        remarks=data.remarks,
        
        status=GRNStatus.DRAFT.value,
    )
    
    # Calculate financials
    is_interstate = is_interstate_transaction(vendor)
    financials = calculate_grn_financials(
        payable_weight_kg=payable_weight,
        rate_per_kg=data.rate_per_kg,
        gst_rate=data.gst_rate,
        is_interstate=is_interstate,
    )
    
    grn.gross_amount = financials["gross_amount"]
    grn.cgst_amount = financials["cgst_amount"]
    grn.sgst_amount = financials["sgst_amount"]
    grn.igst_amount = financials["igst_amount"]
    grn.tds_amount = financials["tds_amount"]
    grn.net_payable_amount = financials["net_payable_amount"]
    
    # Link weighbridge to GRN
    wb.reference_type = "GRN"
    wb.reference_id = grn.id
    
    db.add(grn)
    db.commit()
    db.refresh(grn)
    
    return grn


def generate_lot_id(receipt_date: date, vendor_code: str) -> str:
    """
    Generate lot ID in format: YYYYMMDD-VND-XXXX
    Example: 20251231-VND-0001
    """
    date_str = receipt_date.strftime("%Y%m%d")
    return f"{date_str}-{vendor_code}"


def approve_grn(db: Session, grn_id: int, approved_by: str) -> GoodsReceiptNote:
    """
    Approve a GRN and update inventory.
    
    This function:
    1. Updates raw material aggregate stock
    2. Creates an InventoryLot for FIFO tracking
    3. Updates PO received qty (if linked to PO)
    4. Marks GRN as approved
    
    IMPORTANT: Inventory increases by NET weight (physical material),
    NOT by payable weight (financial).
    """
    grn = db.query(GoodsReceiptNote).filter(GoodsReceiptNote.id == grn_id).first()
    if not grn:
        raise ValueError(f"GRN {grn_id} not found")
    
    if grn.status != GRNStatus.DRAFT.value:
        raise ValueError(f"GRN is not in DRAFT status")
    
    # Get vendor for lot ID generation
    vendor = db.query(Vendor).filter(Vendor.id == grn.vendor_id).first()
    if not vendor:
        raise ValueError(f"Vendor {grn.vendor_id} not found")
    
    # 1. Update raw material aggregate stock by NET weight (physical)
    if grn.raw_material_id:
        material = db.query(RawMaterial).filter(
            RawMaterial.id == grn.raw_material_id
        ).first()
        if material:
            material.current_stock_kg = float(material.current_stock_kg or 0) + float(grn.net_weight_kg)
    
    # 2. Create Inventory Lot for FIFO tracking
    lot_id = generate_lot_id(grn.receipt_date, vendor.vendor_code)
    
    # Check if lot with same ID exists (same vendor, same day) - append sequence
    existing_count = db.query(InventoryLot).filter(
        InventoryLot.lot_id.like(f"{lot_id}%")
    ).count()
    if existing_count > 0:
        lot_id = f"{lot_id}-{existing_count + 1}"
    
    inventory_lot = InventoryLot(
        lot_id=lot_id,
        grn_id=grn.id,
        vendor_id=grn.vendor_id,
        raw_material_id=grn.raw_material_id or 1,  # Default if not specified
        receipt_date=grn.receipt_date,
        vehicle_number=grn.vehicle_number,
        received_qty_kg=grn.net_weight_kg,
        current_qty_kg=grn.net_weight_kg,  # Initially full
        consumed_qty_kg=0,
        rate_per_kg=grn.rate_per_kg or 0,
        total_cost=float(grn.net_weight_kg) * float(grn.rate_per_kg or 0),
        is_exhausted=False,
        is_active=True,
    )
    db.add(inventory_lot)
    
    # 3. Update PO received qty (if linked to PO)
    if grn.purchase_order_id:
        po = db.query(PurchaseOrder).filter(
            PurchaseOrder.id == grn.purchase_order_id
        ).first()
        if po and po.items:
            # Update first item (simplified - assumes single line PO)
            for item in po.items:
                item.received_qty_kg = float(item.received_qty_kg or 0) + float(grn.net_weight_kg)
                item.pending_qty_kg = float(item.ordered_qty_kg) - float(item.received_qty_kg)
            
            # Update PO status based on received qty
            total_ordered = sum(float(i.ordered_qty_kg) for i in po.items)
            total_received = sum(float(i.received_qty_kg or 0) for i in po.items)
            
            if total_received >= total_ordered:
                po.status = "RECEIVED"
            elif total_received > 0:
                po.status = "PARTIALLY_RECEIVED"
    
    # 4. Update GRN status
    grn.status = GRNStatus.APPROVED.value
    grn.approved_by = approved_by
    grn.approved_datetime = datetime.now()
    grn.inventory_updated = True
    
    db.commit()
    db.refresh(grn)
    
    return grn
