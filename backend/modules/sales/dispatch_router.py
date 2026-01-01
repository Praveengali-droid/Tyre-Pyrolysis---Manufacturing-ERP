"""
Dispatch Router - Sales Dispatch and Invoice APIs.

Features:
- Stock validation on dispatch creation
- Separate "Generate Invoice" action
- Partial fulfillment tracking
- Document generation (DC, Invoice, Gate Pass)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime, timedelta
from decimal import Decimal

from database import get_db
from models.customer import Customer
from models.product import Product
from models.quotation import SaleOrder, SaleOrderItem, SaleOrderStatus
from models.dispatch import SalesDispatch, SalesDispatchItem, SalesInvoice, DispatchStatus

router = APIRouter(prefix="/dispatches", tags=["Dispatches"])


# ═══════════════════════════════════════════════════════════
# SCHEMAS
# ═══════════════════════════════════════════════════════════

class DispatchItemCreate(BaseModel):
    sale_order_item_id: int
    product_id: int
    quantity: float
    rate: float

class DispatchCreate(BaseModel):
    sale_order_id: int
    truck_number: Optional[str] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    is_returnable: bool = False
    eway_bill_number: Optional[str] = None
    notes: Optional[str] = None
    items: List[DispatchItemCreate]

class DispatchItemResponse(BaseModel):
    id: int
    product_id: int
    description: Optional[str] = None
    quantity: float
    unit: str
    rate: float
    amount: float
    hsn_code: Optional[str] = None
    tax_rate: float
    tax_amount: float
    total_amount: float
    
    class Config:
        from_attributes = True

class DispatchResponse(BaseModel):
    id: int
    dispatch_number: str
    dispatch_date: date
    sale_order_id: int
    customer_id: int
    status: str
    truck_number: Optional[str] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    gate_pass_number: Optional[str] = None
    eway_bill_number: Optional[str] = None
    is_returnable: bool
    total_quantity: float
    total_amount: float
    notes: Optional[str] = None
    
    class Config:
        from_attributes = True

class InvoiceResponse(BaseModel):
    id: int
    invoice_number: str
    invoice_date: date
    dispatch_id: int
    sale_order_id: int
    customer_id: int
    buyer_name: Optional[str] = None
    buyer_gstin: Optional[str] = None
    place_of_supply: Optional[str] = None
    is_inter_state: bool
    subtotal: float
    cgst_amount: float
    sgst_amount: float
    igst_amount: float
    total_tax: float
    grand_total: float
    
    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════

def generate_dispatch_number(db: Session) -> str:
    """Generate dispatch number: DC-YYYYMMDD-XXX"""
    today = date.today().strftime("%Y%m%d")
    prefix = f"DC-{today}-"
    last = db.query(SalesDispatch).filter(
        SalesDispatch.dispatch_number.like(f"{prefix}%")
    ).order_by(SalesDispatch.id.desc()).first()
    seq = 1
    if last:
        try:
            seq = int(last.dispatch_number.split("-")[-1]) + 1
        except:
            pass
    return f"{prefix}{seq:03d}"


def generate_gate_pass_number(db: Session) -> str:
    """Generate gate pass: GP-YYYYMMDD-XXX"""
    today = date.today().strftime("%Y%m%d")
    prefix = f"GP-{today}-"
    last = db.query(SalesDispatch).filter(
        SalesDispatch.gate_pass_number.like(f"{prefix}%")
    ).order_by(SalesDispatch.id.desc()).first()
    seq = 1
    if last and last.gate_pass_number:
        try:
            seq = int(last.gate_pass_number.split("-")[-1]) + 1
        except:
            pass
    return f"{prefix}{seq:03d}"


def generate_invoice_number(db: Session) -> str:
    """Generate invoice number: INV/YY-YY/XXX (financial year format)"""
    today = date.today()
    # Financial year: April to March
    if today.month >= 4:
        fy_start = today.year % 100
        fy_end = (today.year + 1) % 100
    else:
        fy_start = (today.year - 1) % 100
        fy_end = today.year % 100
    
    prefix = f"INV/{fy_start:02d}-{fy_end:02d}/"
    last = db.query(SalesInvoice).filter(
        SalesInvoice.invoice_number.like(f"{prefix}%")
    ).order_by(SalesInvoice.id.desc()).first()
    seq = 1
    if last:
        try:
            seq = int(last.invoice_number.split("/")[-1]) + 1
        except:
            pass
    return f"{prefix}{seq:03d}"


def update_sale_order_status(db: Session, sale_order_id: int):
    """Update SO status based on dispatched quantities."""
    so = db.query(SaleOrder).filter(SaleOrder.id == sale_order_id).first()
    if not so:
        return
    
    so_items = db.query(SaleOrderItem).filter(SaleOrderItem.sale_order_id == sale_order_id).all()
    
    all_dispatched = True
    any_dispatched = False
    
    for item in so_items:
        if item.dispatched_quantity and item.dispatched_quantity > 0:
            any_dispatched = True
        if item.pending_quantity and item.pending_quantity > 0:
            all_dispatched = False
    
    if all_dispatched:
        so.status = SaleOrderStatus.DISPATCHED.value
    elif any_dispatched:
        so.status = SaleOrderStatus.PARTIALLY_DISPATCHED.value
    
    db.commit()


# ═══════════════════════════════════════════════════════════
# DISPATCH ENDPOINTS
# ═══════════════════════════════════════════════════════════

@router.get("/", response_model=List[DispatchResponse])
def list_dispatches(
    sale_order_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List all dispatches."""
    query = db.query(SalesDispatch)
    if sale_order_id:
        query = query.filter(SalesDispatch.sale_order_id == sale_order_id)
    if status:
        query = query.filter(SalesDispatch.status == status)
    return query.order_by(SalesDispatch.dispatch_date.desc()).limit(limit).all()


@router.get("/{dispatch_id}", response_model=DispatchResponse)
def get_dispatch(dispatch_id: int, db: Session = Depends(get_db)):
    """Get dispatch details."""
    dispatch = db.query(SalesDispatch).filter(SalesDispatch.id == dispatch_id).first()
    if not dispatch:
        raise HTTPException(status_code=404, detail="Dispatch not found")
    return dispatch


@router.get("/{dispatch_id}/items", response_model=List[DispatchItemResponse])
def get_dispatch_items(dispatch_id: int, db: Session = Depends(get_db)):
    """Get items in a dispatch."""
    items = db.query(SalesDispatchItem).filter(SalesDispatchItem.dispatch_id == dispatch_id).all()
    return items


@router.post("/", response_model=DispatchResponse, status_code=status.HTTP_201_CREATED)
def create_dispatch(data: DispatchCreate, db: Session = Depends(get_db)):
    """
    Create a dispatch from a Sale Order.
    
    STOCK VALIDATION: Rejects if dispatch_quantity > current_stock for any item.
    """
    # Validate Sale Order
    sale_order = db.query(SaleOrder).filter(SaleOrder.id == data.sale_order_id).first()
    if not sale_order:
        raise HTTPException(status_code=400, detail="Sale Order not found")
    
    if sale_order.status in [SaleOrderStatus.CANCELLED.value, SaleOrderStatus.DISPATCHED.value]:
        raise HTTPException(status_code=400, detail=f"Cannot dispatch: SO status is {sale_order.status}")
    
    # Validate each item - check stock availability
    for item_data in data.items:
        product = db.query(Product).filter(Product.id == item_data.product_id).first()
        if not product:
            raise HTTPException(status_code=400, detail=f"Product {item_data.product_id} not found")
        
        current_stock = float(product.current_stock or 0)
        if item_data.quantity > current_stock:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient inventory for {product.name}: requested {item_data.quantity}, available {current_stock}"
            )
        
        # Validate SO item
        so_item = db.query(SaleOrderItem).filter(SaleOrderItem.id == item_data.sale_order_item_id).first()
        if not so_item or so_item.sale_order_id != data.sale_order_id:
            raise HTTPException(status_code=400, detail=f"Invalid SO item {item_data.sale_order_item_id}")
        
        pending = float(so_item.pending_quantity or so_item.quantity)
        if item_data.quantity > pending:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot dispatch {item_data.quantity} - only {pending} pending on SO"
            )
    
    # Create Dispatch
    dispatch = SalesDispatch(
        dispatch_number=generate_dispatch_number(db),
        dispatch_date=date.today(),
        sale_order_id=data.sale_order_id,
        customer_id=sale_order.customer_id,
        status=DispatchStatus.PENDING.value,
        truck_number=data.truck_number,
        driver_name=data.driver_name,
        driver_phone=data.driver_phone,
        gate_pass_number=generate_gate_pass_number(db),
        gate_pass_time=datetime.now(),
        is_returnable=data.is_returnable,
        eway_bill_number=data.eway_bill_number,
        notes=data.notes
    )
    db.add(dispatch)
    db.flush()
    
    # Add items
    total_qty = Decimal(0)
    total_amt = Decimal(0)
    
    for item_data in data.items:
        product = db.query(Product).filter(Product.id == item_data.product_id).first()
        
        qty = Decimal(str(item_data.quantity))
        rate = Decimal(str(item_data.rate))
        amount = qty * rate
        tax_rate = product.gst_rate or Decimal("18.0")
        tax_amount = amount * (tax_rate / 100)
        item_total = amount + tax_amount
        
        dispatch_item = SalesDispatchItem(
            dispatch_id=dispatch.id,
            sale_order_item_id=item_data.sale_order_item_id,
            product_id=item_data.product_id,
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
        db.add(dispatch_item)
        
        total_qty += qty
        total_amt += item_total
    
    dispatch.total_quantity = total_qty
    dispatch.total_amount = total_amt
    
    db.commit()
    db.refresh(dispatch)
    return dispatch


@router.put("/{dispatch_id}/ship")
def ship_dispatch(dispatch_id: int, db: Session = Depends(get_db)):
    """
    Mark dispatch as SHIPPED.
    
    This action:
    1. Deducts stock from Product.current_stock
    2. Updates SaleOrderItem.dispatched_quantity
    3. Updates Sale Order status
    """
    dispatch = db.query(SalesDispatch).filter(SalesDispatch.id == dispatch_id).first()
    if not dispatch:
        raise HTTPException(status_code=404, detail="Dispatch not found")
    
    if dispatch.status != DispatchStatus.PENDING.value:
        raise HTTPException(status_code=400, detail=f"Cannot ship: status is {dispatch.status}")
    
    # Get dispatch items
    items = db.query(SalesDispatchItem).filter(SalesDispatchItem.dispatch_id == dispatch_id).all()
    
    # Deduct stock and update SO items
    for item in items:
        # Deduct from product stock
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            product.current_stock = (product.current_stock or 0) - item.quantity
        
        # Update SO item
        so_item = db.query(SaleOrderItem).filter(SaleOrderItem.id == item.sale_order_item_id).first()
        if so_item:
            so_item.dispatched_quantity = (so_item.dispatched_quantity or 0) + item.quantity
            so_item.pending_quantity = so_item.quantity - so_item.dispatched_quantity
    
    # Update dispatch status
    dispatch.status = DispatchStatus.SHIPPED.value
    dispatch.shipped_at = datetime.now()
    
    db.commit()
    
    # Update SO status
    update_sale_order_status(db, dispatch.sale_order_id)
    
    return {"message": "Dispatch shipped", "dispatch_number": dispatch.dispatch_number, "status": dispatch.status}


@router.put("/{dispatch_id}/deliver")
def deliver_dispatch(dispatch_id: int, db: Session = Depends(get_db)):
    """Mark dispatch as DELIVERED by customer."""
    dispatch = db.query(SalesDispatch).filter(SalesDispatch.id == dispatch_id).first()
    if not dispatch:
        raise HTTPException(status_code=404, detail="Dispatch not found")
    
    if dispatch.status != DispatchStatus.SHIPPED.value:
        raise HTTPException(status_code=400, detail="Only SHIPPED dispatches can be marked delivered")
    
    dispatch.status = DispatchStatus.DELIVERED.value
    dispatch.delivered_at = datetime.now()
    
    db.commit()
    
    # Update SO status
    sale_order = db.query(SaleOrder).filter(SaleOrder.id == dispatch.sale_order_id).first()
    if sale_order:
        # Check if all dispatches delivered
        all_delivered = db.query(SalesDispatch).filter(
            SalesDispatch.sale_order_id == dispatch.sale_order_id,
            SalesDispatch.status != DispatchStatus.DELIVERED.value,
            SalesDispatch.status != DispatchStatus.CANCELLED.value
        ).count() == 0
        
        if all_delivered and sale_order.status == SaleOrderStatus.DISPATCHED.value:
            sale_order.status = SaleOrderStatus.DELIVERED.value
            db.commit()
    
    return {"message": "Dispatch delivered", "dispatch_number": dispatch.dispatch_number, "status": dispatch.status}


# ═══════════════════════════════════════════════════════════
# INVOICE ENDPOINTS
# ═══════════════════════════════════════════════════════════

@router.post("/{dispatch_id}/generate-invoice", response_model=InvoiceResponse)
def generate_invoice(dispatch_id: int, db: Session = Depends(get_db)):
    """
    Generate Tax Invoice for a dispatch.
    
    Separate action - not auto-generated on dispatch creation.
    Allows creating dispatch today, invoice tomorrow.
    """
    dispatch = db.query(SalesDispatch).filter(SalesDispatch.id == dispatch_id).first()
    if not dispatch:
        raise HTTPException(status_code=404, detail="Dispatch not found")
    
    # Check if invoice already exists
    existing = db.query(SalesInvoice).filter(SalesInvoice.dispatch_id == dispatch_id).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Invoice already exists: {existing.invoice_number}")
    
    # Get customer for GSTIN and address
    customer = db.query(Customer).filter(Customer.id == dispatch.customer_id).first()
    
    # Get dispatch items for amounts
    items = db.query(SalesDispatchItem).filter(SalesDispatchItem.dispatch_id == dispatch_id).all()
    
    subtotal = sum(float(i.amount) for i in items)
    total_tax = sum(float(i.tax_amount) for i in items)
    
    # Determine CGST+SGST vs IGST (based on state)
    seller_state = "Telangana"  # TODO: Get from company config
    buyer_state = customer.state if customer else None
    is_inter_state = buyer_state and buyer_state.lower() != seller_state.lower()
    
    if is_inter_state:
        igst = total_tax
        cgst = sgst = 0
    else:
        cgst = sgst = total_tax / 2
        igst = 0
    
    # Create invoice
    invoice = SalesInvoice(
        invoice_number=generate_invoice_number(db),
        invoice_date=date.today(),
        dispatch_id=dispatch.id,
        sale_order_id=dispatch.sale_order_id,
        customer_id=dispatch.customer_id,
        
        # Seller details
        seller_name="Tyre Pyrolysis Industries Pvt Ltd",
        seller_gstin="36AABCT1234Z1ZT",  # TODO: From config
        seller_address="Plot No. 123, Industrial Area, Hyderabad",
        seller_state="Telangana",
        seller_state_code="36",
        
        # Buyer details
        buyer_name=customer.name if customer else None,
        buyer_gstin=customer.gst_number if customer else None,
        buyer_address=customer.address if customer else None,
        buyer_state=customer.state if customer else None,
        buyer_state_code=None,  # TODO: Lookup state code
        
        # Place of supply
        place_of_supply=buyer_state or seller_state,
        is_inter_state=is_inter_state,
        
        # Amounts
        subtotal=Decimal(str(subtotal)),
        cgst_amount=Decimal(str(cgst)),
        sgst_amount=Decimal(str(sgst)),
        igst_amount=Decimal(str(igst)),
        total_tax=Decimal(str(total_tax)),
        grand_total=Decimal(str(subtotal + total_tax))
    )
    
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


@router.get("/{dispatch_id}/invoice", response_model=InvoiceResponse)
def get_invoice(dispatch_id: int, db: Session = Depends(get_db)):
    """Get invoice for a dispatch."""
    invoice = db.query(SalesInvoice).filter(SalesInvoice.dispatch_id == dispatch_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found. Generate invoice first.")
    return invoice


# ═══════════════════════════════════════════════════════════
# DOCUMENT ENDPOINTS
# ═══════════════════════════════════════════════════════════

@router.get("/{dispatch_id}/documents/dc")
def get_delivery_challan(dispatch_id: int, db: Session = Depends(get_db)):
    """Get Delivery Challan data for printing (non-financial, just quantities)."""
    dispatch = db.query(SalesDispatch).filter(SalesDispatch.id == dispatch_id).first()
    if not dispatch:
        raise HTTPException(status_code=404, detail="Dispatch not found")
    
    customer = db.query(Customer).filter(Customer.id == dispatch.customer_id).first()
    sale_order = db.query(SaleOrder).filter(SaleOrder.id == dispatch.sale_order_id).first()
    items = db.query(SalesDispatchItem).filter(SalesDispatchItem.dispatch_id == dispatch_id).all()
    
    return {
        "document_type": "DELIVERY_CHALLAN",
        "dc_number": dispatch.dispatch_number,
        "dc_date": str(dispatch.dispatch_date),
        "sale_order_number": sale_order.order_number if sale_order else None,
        
        "customer": {
            "name": customer.name if customer else None,
            "address": customer.address if customer else None,
            "city": customer.city if customer else None,
            "phone": customer.phone if customer else None
        },
        
        "truck_number": dispatch.truck_number,
        "driver_name": dispatch.driver_name,
        "driver_phone": dispatch.driver_phone,
        
        "items": [
            {
                "description": i.description,
                "hsn_code": i.hsn_code,
                "quantity": float(i.quantity),
                "unit": i.unit
            }
            for i in items
        ],
        
        "total_quantity": float(dispatch.total_quantity),
        "notes": dispatch.notes
    }


@router.get("/{dispatch_id}/documents/gatepass")
def get_gate_pass(dispatch_id: int, db: Session = Depends(get_db)):
    """Get Gate Pass data for security guard (A5 size slip)."""
    dispatch = db.query(SalesDispatch).filter(SalesDispatch.id == dispatch_id).first()
    if not dispatch:
        raise HTTPException(status_code=404, detail="Dispatch not found")
    
    customer = db.query(Customer).filter(Customer.id == dispatch.customer_id).first()
    
    return {
        "document_type": "GATE_PASS",
        "size": "A5",
        "gate_pass_number": dispatch.gate_pass_number,
        "date": str(dispatch.dispatch_date),
        "time": dispatch.gate_pass_time.strftime("%H:%M") if dispatch.gate_pass_time else None,
        
        "truck_number": dispatch.truck_number,
        "driver_name": dispatch.driver_name,
        "driver_phone": dispatch.driver_phone,
        
        "destination": customer.name if customer else "N/A",
        "total_quantity": float(dispatch.total_quantity),
        
        "is_returnable": dispatch.is_returnable,
        "returnable_items": "Pallets / Drums" if dispatch.is_returnable else None,
        
        "dc_number": dispatch.dispatch_number
    }


@router.get("/{dispatch_id}/documents/invoice")
def get_invoice_document(dispatch_id: int, db: Session = Depends(get_db)):
    """Get full Tax Invoice data with GST breakdown for printing."""
    dispatch = db.query(SalesDispatch).filter(SalesDispatch.id == dispatch_id).first()
    if not dispatch:
        raise HTTPException(status_code=404, detail="Dispatch not found")
    
    invoice = db.query(SalesInvoice).filter(SalesInvoice.dispatch_id == dispatch_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found. Generate invoice first.")
    
    items = db.query(SalesDispatchItem).filter(SalesDispatchItem.dispatch_id == dispatch_id).all()
    
    return {
        "document_type": "TAX_INVOICE",
        "invoice_number": invoice.invoice_number,
        "invoice_date": str(invoice.invoice_date),
        "dc_number": dispatch.dispatch_number,
        
        "seller": {
            "name": invoice.seller_name,
            "gstin": invoice.seller_gstin,
            "address": invoice.seller_address,
            "state": invoice.seller_state,
            "state_code": invoice.seller_state_code
        },
        
        "buyer": {
            "name": invoice.buyer_name,
            "gstin": invoice.buyer_gstin,
            "address": invoice.buyer_address,
            "state": invoice.buyer_state,
            "state_code": invoice.buyer_state_code
        },
        
        "place_of_supply": invoice.place_of_supply,
        "is_inter_state": invoice.is_inter_state,
        
        "items": [
            {
                "description": i.description,
                "hsn_code": i.hsn_code,
                "quantity": float(i.quantity),
                "unit": i.unit,
                "rate": float(i.rate),
                "amount": float(i.amount),
                "tax_rate": float(i.tax_rate),
                "cgst": float(i.tax_amount / 2) if not invoice.is_inter_state else 0,
                "sgst": float(i.tax_amount / 2) if not invoice.is_inter_state else 0,
                "igst": float(i.tax_amount) if invoice.is_inter_state else 0,
                "total": float(i.total_amount)
            }
            for i in items
        ],
        
        "totals": {
            "subtotal": float(invoice.subtotal),
            "cgst": float(invoice.cgst_amount),
            "sgst": float(invoice.sgst_amount),
            "igst": float(invoice.igst_amount),
            "total_tax": float(invoice.total_tax),
            "grand_total": float(invoice.grand_total)
        },
        
        "amount_in_words": invoice.amount_in_words,
        "payment_terms": invoice.payment_terms
    }


# ═══════════════════════════════════════════════════════════
# SALE ORDER HELPER ENDPOINTS
# ═══════════════════════════════════════════════════════════

@router.get("/orders/{order_id}/pending-items")
def get_pending_items(order_id: int, db: Session = Depends(get_db)):
    """Get items that have pending quantity for dispatch."""
    items = db.query(SaleOrderItem).filter(
        SaleOrderItem.sale_order_id == order_id,
        SaleOrderItem.pending_quantity > 0
    ).all()
    
    result = []
    for item in items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        result.append({
            "sale_order_item_id": item.id,
            "product_id": item.product_id,
            "product_name": product.name if product else None,
            "hsn_code": product.hsn_code if product else None,
            "ordered_quantity": float(item.quantity),
            "dispatched_quantity": float(item.dispatched_quantity or 0),
            "pending_quantity": float(item.pending_quantity or item.quantity),
            "unit": item.unit,
            "rate": float(item.rate),
            "current_stock": float(product.current_stock or 0) if product else 0
        })
    
    return result
