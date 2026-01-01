"""
Sales Returns Router - RMA and Credit Note APIs.

Workflow: Create Return → Receive (Quarantine) → QC Check → Accept/Scrap → Credit Note
Safety: Returned goods never go directly to main inventory.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal

from database import get_db
from models.customer import Customer
from models.product import Product
from models.dispatch import SalesDispatch, SalesDispatchItem, SalesInvoice
from models.sales_return import SalesReturn, SalesReturnItem, CreditNote, ReturnStatus

router = APIRouter(prefix="/returns", tags=["Returns"])


# ═══════════════════════════════════════════════════════════
# SCHEMAS
# ═══════════════════════════════════════════════════════════

class ReturnItemCreate(BaseModel):
    product_id: int
    dispatch_item_id: Optional[int] = None
    quantity: float
    rate: float
    reason: Optional[str] = None

class ReturnCreate(BaseModel):
    invoice_id: int
    reason: Optional[str] = None
    reason_category: Optional[str] = "OTHER"  # QUALITY, DAMAGE, WRONG_PRODUCT, OTHER
    items: List[ReturnItemCreate]

class ReturnItemResponse(BaseModel):
    id: int
    product_id: int
    description: Optional[str] = None
    quantity: float
    unit: str
    rate: float
    amount: float
    tax_amount: float
    total_amount: float
    qc_status: Optional[str] = None
    destination: Optional[str] = None
    
    class Config:
        from_attributes = True

class ReturnResponse(BaseModel):
    id: int
    return_number: str
    return_date: date
    invoice_id: int
    customer_id: int
    status: str
    reason: Optional[str] = None
    reason_category: Optional[str] = None
    total_quantity: float
    total_amount: float
    quarantine_location: Optional[str] = None
    
    class Config:
        from_attributes = True

class CreditNoteResponse(BaseModel):
    id: int
    credit_note_number: str
    credit_note_date: date
    sales_return_id: int
    original_invoice_id: int
    customer_id: int
    subtotal: float
    cgst_amount: float
    sgst_amount: float
    igst_amount: float
    grand_total: float
    
    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════

def generate_return_number(db: Session) -> str:
    """Generate return number: RMA-YYYYMMDD-XXX"""
    today = date.today().strftime("%Y%m%d")
    prefix = f"RMA-{today}-"
    last = db.query(SalesReturn).filter(
        SalesReturn.return_number.like(f"{prefix}%")
    ).order_by(SalesReturn.id.desc()).first()
    seq = 1
    if last:
        try:
            seq = int(last.return_number.split("-")[-1]) + 1
        except:
            pass
    return f"{prefix}{seq:03d}"


def generate_credit_note_number(db: Session) -> str:
    """Generate credit note number: CN-YYYY-XXXX"""
    year = date.today().year
    prefix = f"CN-{year}-"
    last = db.query(CreditNote).filter(
        CreditNote.credit_note_number.like(f"{prefix}%")
    ).order_by(CreditNote.id.desc()).first()
    seq = 1
    if last:
        try:
            seq = int(last.credit_note_number.split("-")[-1]) + 1
        except:
            pass
    return f"{prefix}{seq:04d}"


# ═══════════════════════════════════════════════════════════
# RETURN ENDPOINTS
# ═══════════════════════════════════════════════════════════

@router.get("/", response_model=List[ReturnResponse])
def list_returns(
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List all sales returns."""
    query = db.query(SalesReturn)
    if status:
        query = query.filter(SalesReturn.status == status)
    return query.order_by(SalesReturn.return_date.desc()).limit(limit).all()


@router.get("/pending-qc")
def list_pending_qc(db: Session = Depends(get_db)):
    """Get returns pending QC check for plant manager dashboard."""
    returns = db.query(SalesReturn).filter(
        SalesReturn.status == ReturnStatus.RECEIVED.value
    ).all()
    
    result = []
    for r in returns:
        customer = db.query(Customer).filter(Customer.id == r.customer_id).first()
        items = db.query(SalesReturnItem).filter(SalesReturnItem.sales_return_id == r.id).all()
        
        result.append({
            "id": r.id,
            "return_number": r.return_number,
            "return_date": str(r.return_date),
            "customer_name": customer.name if customer else None,
            "reason": r.reason,
            "reason_category": r.reason_category,
            "total_quantity": float(r.total_quantity or 0),
            "quarantine_location": r.quarantine_location,
            "received_at": str(r.received_at) if r.received_at else None,
            "items": [
                {
                    "id": i.id,
                    "product_id": i.product_id,
                    "description": i.description,
                    "quantity": float(i.quantity),
                    "unit": i.unit,
                    "qc_status": i.qc_status
                }
                for i in items
            ]
        })
    
    return result


@router.get("/{return_id}", response_model=ReturnResponse)
def get_return(return_id: int, db: Session = Depends(get_db)):
    """Get return details."""
    ret = db.query(SalesReturn).filter(SalesReturn.id == return_id).first()
    if not ret:
        raise HTTPException(status_code=404, detail="Return not found")
    return ret


@router.get("/{return_id}/items", response_model=List[ReturnItemResponse])
def get_return_items(return_id: int, db: Session = Depends(get_db)):
    """Get items in a return."""
    items = db.query(SalesReturnItem).filter(SalesReturnItem.sales_return_id == return_id).all()
    return items


@router.post("/", response_model=ReturnResponse, status_code=status.HTTP_201_CREATED)
def create_return(data: ReturnCreate, db: Session = Depends(get_db)):
    """
    Create a sales return request.
    Status starts as PENDING until goods are physically received.
    """
    # Validate invoice
    invoice = db.query(SalesInvoice).filter(SalesInvoice.id == data.invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=400, detail="Invoice not found")
    
    dispatch = db.query(SalesDispatch).filter(SalesDispatch.id == invoice.dispatch_id).first()
    
    # Create return
    sales_return = SalesReturn(
        return_number=generate_return_number(db),
        return_date=date.today(),
        invoice_id=data.invoice_id,
        dispatch_id=dispatch.id if dispatch else None,
        sale_order_id=dispatch.sale_order_id if dispatch else None,
        customer_id=invoice.customer_id,
        status=ReturnStatus.PENDING.value,
        reason=data.reason,
        reason_category=data.reason_category,
        quarantine_location="QUARANTINE"
    )
    db.add(sales_return)
    db.flush()
    
    # Add items
    total_qty = Decimal(0)
    total_amt = Decimal(0)
    
    for item_data in data.items:
        product = db.query(Product).filter(Product.id == item_data.product_id).first()
        if not product:
            raise HTTPException(status_code=400, detail=f"Product {item_data.product_id} not found")
        
        qty = Decimal(str(item_data.quantity))
        rate = Decimal(str(item_data.rate))
        amount = qty * rate
        tax_rate = product.gst_rate or Decimal("18.0")
        tax_amount = amount * (tax_rate / 100)
        item_total = amount + tax_amount
        
        return_item = SalesReturnItem(
            sales_return_id=sales_return.id,
            product_id=item_data.product_id,
            dispatch_item_id=item_data.dispatch_item_id,
            description=product.name,
            quantity=qty,
            unit=product.unit,
            rate=rate,
            amount=amount,
            hsn_code=product.hsn_code,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            total_amount=item_total
        )
        db.add(return_item)
        
        total_qty += qty
        total_amt += item_total
    
    sales_return.total_quantity = total_qty
    sales_return.total_amount = total_amt
    
    db.commit()
    db.refresh(sales_return)
    return sales_return


@router.put("/{return_id}/receive")
def receive_return(return_id: int, db: Session = Depends(get_db)):
    """
    Mark return as RECEIVED - goods are now in QUARANTINE.
    
    SAFETY: Does NOT add to main inventory. Goes to quarantine for QC.
    """
    ret = db.query(SalesReturn).filter(SalesReturn.id == return_id).first()
    if not ret:
        raise HTTPException(status_code=404, detail="Return not found")
    
    if ret.status != ReturnStatus.PENDING.value:
        raise HTTPException(status_code=400, detail=f"Cannot receive: status is {ret.status}")
    
    ret.status = ReturnStatus.RECEIVED.value
    ret.received_at = datetime.now()
    ret.quarantine_location = "QUARANTINE"
    
    db.commit()
    
    return {
        "message": "Return received and in quarantine",
        "return_number": ret.return_number,
        "status": ret.status,
        "quarantine_location": ret.quarantine_location
    }


@router.put("/{return_id}/qc-pass")
def qc_pass_return(return_id: int, qc_notes: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Mark return as QC PASSED.
    
    This action:
    1. Moves goods from QUARANTINE to MAIN STOCK
    2. Increases product.current_stock
    3. Generates Credit Note
    """
    ret = db.query(SalesReturn).filter(SalesReturn.id == return_id).first()
    if not ret:
        raise HTTPException(status_code=404, detail="Return not found")
    
    if ret.status != ReturnStatus.RECEIVED.value:
        raise HTTPException(status_code=400, detail="Only RECEIVED returns can be QC checked")
    
    # Get return items
    items = db.query(SalesReturnItem).filter(SalesReturnItem.sales_return_id == return_id).all()
    
    # Update items and add to main stock
    for item in items:
        item.qc_status = "PASS"
        item.destination = "MAIN_STOCK"
        
        # Add back to main inventory
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            product.current_stock = (product.current_stock or 0) + item.quantity
    
    # Update return status
    ret.status = ReturnStatus.QC_PASS.value
    ret.qc_date = datetime.now()
    ret.qc_notes = qc_notes
    
    db.commit()
    
    # Generate Credit Note
    credit_note = _generate_credit_note(db, ret)
    
    return {
        "message": "QC passed - stock updated and credit note generated",
        "return_number": ret.return_number,
        "status": ret.status,
        "credit_note_number": credit_note.credit_note_number if credit_note else None
    }


@router.put("/{return_id}/qc-fail")
def qc_fail_return(return_id: int, qc_notes: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Mark return as QC FAILED.
    
    This action:
    1. Moves goods from QUARANTINE to SCRAP
    2. Does NOT increase main stock
    3. Still generates Credit Note (customer gets refund regardless)
    """
    ret = db.query(SalesReturn).filter(SalesReturn.id == return_id).first()
    if not ret:
        raise HTTPException(status_code=404, detail="Return not found")
    
    if ret.status != ReturnStatus.RECEIVED.value:
        raise HTTPException(status_code=400, detail="Only RECEIVED returns can be QC checked")
    
    # Get return items
    items = db.query(SalesReturnItem).filter(SalesReturnItem.sales_return_id == return_id).all()
    
    # Update items - move to scrap, NOT main stock
    for item in items:
        item.qc_status = "FAIL"
        item.destination = "SCRAP"
        # NOTE: We do NOT add to current_stock
    
    # Update return status
    ret.status = ReturnStatus.QC_FAIL.value
    ret.qc_date = datetime.now()
    ret.qc_notes = qc_notes
    
    db.commit()
    
    # Generate Credit Note (customer still gets credit)
    credit_note = _generate_credit_note(db, ret)
    
    return {
        "message": "QC failed - goods moved to scrap, credit note generated",
        "return_number": ret.return_number,
        "status": ret.status,
        "credit_note_number": credit_note.credit_note_number if credit_note else None
    }


def _generate_credit_note(db: Session, sales_return: SalesReturn) -> CreditNote:
    """Generate a Credit Note for a completed return."""
    # Check if already exists
    existing = db.query(CreditNote).filter(CreditNote.sales_return_id == sales_return.id).first()
    if existing:
        return existing
    
    # Get original invoice for details
    invoice = db.query(SalesInvoice).filter(SalesInvoice.id == sales_return.invoice_id).first()
    customer = db.query(Customer).filter(Customer.id == sales_return.customer_id).first()
    
    # Calculate totals from return items
    items = db.query(SalesReturnItem).filter(SalesReturnItem.sales_return_id == sales_return.id).all()
    
    subtotal = sum(float(i.amount) for i in items)
    total_tax = sum(float(i.tax_amount) for i in items)
    
    # Determine CGST+SGST vs IGST
    is_inter_state = invoice.is_inter_state if invoice else False
    
    if is_inter_state:
        igst = total_tax
        cgst = sgst = 0
    else:
        cgst = sgst = total_tax / 2
        igst = 0
    
    # Create credit note
    credit_note = CreditNote(
        credit_note_number=generate_credit_note_number(db),
        credit_note_date=date.today(),
        sales_return_id=sales_return.id,
        original_invoice_id=sales_return.invoice_id,
        customer_id=sales_return.customer_id,
        reason=sales_return.reason,
        
        # Seller details
        seller_name=invoice.seller_name if invoice else "Tyre Pyrolysis Industries Pvt Ltd",
        seller_gstin=invoice.seller_gstin if invoice else None,
        seller_address=invoice.seller_address if invoice else None,
        seller_state=invoice.seller_state if invoice else None,
        seller_state_code=invoice.seller_state_code if invoice else None,
        
        # Buyer details
        buyer_name=customer.name if customer else None,
        buyer_gstin=customer.gst_number if customer else None,
        buyer_address=customer.address if customer else None,
        buyer_state=customer.state if customer else None,
        
        # Place of supply
        place_of_supply=invoice.place_of_supply if invoice else None,
        is_inter_state=is_inter_state,
        
        # Reversed amounts
        subtotal=Decimal(str(subtotal)),
        cgst_amount=Decimal(str(cgst)),
        sgst_amount=Decimal(str(sgst)),
        igst_amount=Decimal(str(igst)),
        total_tax=Decimal(str(total_tax)),
        grand_total=Decimal(str(subtotal + total_tax))
    )
    
    db.add(credit_note)
    db.commit()
    db.refresh(credit_note)
    
    return credit_note


# ═══════════════════════════════════════════════════════════
# CREDIT NOTE ENDPOINTS
# ═══════════════════════════════════════════════════════════

@router.get("/{return_id}/credit-note", response_model=CreditNoteResponse)
def get_credit_note(return_id: int, db: Session = Depends(get_db)):
    """Get credit note for a return."""
    cn = db.query(CreditNote).filter(CreditNote.sales_return_id == return_id).first()
    if not cn:
        raise HTTPException(status_code=404, detail="Credit note not found")
    return cn


@router.get("/{return_id}/credit-note/document")
def get_credit_note_document(return_id: int, db: Session = Depends(get_db)):
    """Get full Credit Note for printing."""
    ret = db.query(SalesReturn).filter(SalesReturn.id == return_id).first()
    if not ret:
        raise HTTPException(status_code=404, detail="Return not found")
    
    cn = db.query(CreditNote).filter(CreditNote.sales_return_id == return_id).first()
    if not cn:
        raise HTTPException(status_code=404, detail="Credit note not generated yet")
    
    invoice = db.query(SalesInvoice).filter(SalesInvoice.id == cn.original_invoice_id).first()
    items = db.query(SalesReturnItem).filter(SalesReturnItem.sales_return_id == return_id).all()
    
    return {
        "document_type": "CREDIT_NOTE",
        "credit_note_number": cn.credit_note_number,
        "credit_note_date": str(cn.credit_note_date),
        "original_invoice_number": invoice.invoice_number if invoice else None,
        "original_invoice_date": str(invoice.invoice_date) if invoice else None,
        "return_number": ret.return_number,
        
        "seller": {
            "name": cn.seller_name,
            "gstin": cn.seller_gstin,
            "address": cn.seller_address,
            "state": cn.seller_state,
            "state_code": cn.seller_state_code
        },
        
        "buyer": {
            "name": cn.buyer_name,
            "gstin": cn.buyer_gstin,
            "address": cn.buyer_address,
            "state": cn.buyer_state
        },
        
        "place_of_supply": cn.place_of_supply,
        "is_inter_state": cn.is_inter_state,
        "reason": cn.reason,
        
        "items": [
            {
                "description": i.description,
                "hsn_code": i.hsn_code,
                "quantity": float(i.quantity),
                "unit": i.unit,
                "rate": float(i.rate),
                "amount": float(i.amount),
                "tax_rate": float(i.tax_rate),
                "cgst": float(i.tax_amount / 2) if not cn.is_inter_state else 0,
                "sgst": float(i.tax_amount / 2) if not cn.is_inter_state else 0,
                "igst": float(i.tax_amount) if cn.is_inter_state else 0,
                "total": float(i.total_amount)
            }
            for i in items
        ],
        
        "totals": {
            "subtotal": float(cn.subtotal),
            "cgst": float(cn.cgst_amount),
            "sgst": float(cn.sgst_amount),
            "igst": float(cn.igst_amount),
            "total_tax": float(cn.total_tax),
            "grand_total": float(cn.grand_total)
        }
    }


# ═══════════════════════════════════════════════════════════
# INVOICE HELPER - Get items available for return
# ═══════════════════════════════════════════════════════════

@router.get("/invoices/{invoice_id}/returnable-items")
def get_returnable_items(invoice_id: int, db: Session = Depends(get_db)):
    """Get items from an invoice that can be returned."""
    invoice = db.query(SalesInvoice).filter(SalesInvoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Get dispatch items
    dispatch_items = db.query(SalesDispatchItem).filter(
        SalesDispatchItem.dispatch_id == invoice.dispatch_id
    ).all()
    
    # TODO: In future, subtract already returned quantities
    
    result = []
    for item in dispatch_items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        result.append({
            "dispatch_item_id": item.id,
            "product_id": item.product_id,
            "product_name": product.name if product else None,
            "hsn_code": item.hsn_code,
            "dispatched_quantity": float(item.quantity),
            "returnable_quantity": float(item.quantity),  # TODO: Subtract returned
            "unit": item.unit,
            "rate": float(item.rate)
        })
    
    return {
        "invoice_id": invoice_id,
        "invoice_number": invoice.invoice_number,
        "items": result
    }
