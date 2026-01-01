"""
Quotation Router - Quote to Order workflow APIs.

Workflow: Create Quote → Send → Accept/Reject → Convert to Sale Order
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, timedelta
from decimal import Decimal

from database import get_db
from models.customer import Customer
from models.product import Product
from models.quotation import Quotation, QuotationItem, SaleOrder, SaleOrderItem, QuotationStatus, SaleOrderStatus

router = APIRouter(prefix="/quotations", tags=["Quotations"])


# ═══════════════════════════════════════════════════════════
# SCHEMAS
# ═══════════════════════════════════════════════════════════

class QuotationItemCreate(BaseModel):
    product_id: int
    quantity: float
    rate: float
    description: Optional[str] = None

class QuotationCreate(BaseModel):
    customer_id: int
    valid_days: int = 30  # Validity in days
    payment_terms: Optional[str] = None
    delivery_terms: Optional[str] = None
    notes: Optional[str] = None
    items: List[QuotationItemCreate]

class QuotationItemResponse(BaseModel):
    id: int
    product_id: int
    description: Optional[str] = None
    quantity: float
    unit: str
    rate: float
    amount: float
    tax_rate: float
    tax_amount: float
    total_amount: float
    
    class Config:
        from_attributes = True

class QuotationResponse(BaseModel):
    id: int
    quotation_number: str
    quotation_date: date
    valid_until: Optional[date] = None
    customer_id: int
    status: str
    subtotal: float
    tax_amount: float
    discount_amount: float
    total_amount: float
    payment_terms: Optional[str] = None
    delivery_terms: Optional[str] = None
    notes: Optional[str] = None
    
    class Config:
        from_attributes = True

class SaleOrderResponse(BaseModel):
    id: int
    order_number: str
    order_date: date
    customer_id: int
    quotation_id: Optional[int] = None
    status: str
    subtotal: float
    tax_amount: float
    total_amount: float
    
    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════
# QUOTATION ENDPOINTS
# ═══════════════════════════════════════════════════════════

def generate_quotation_number(db: Session) -> str:
    """Generate quotation number: QT-YYYYMMDD-XXX"""
    today = date.today().strftime("%Y%m%d")
    prefix = f"QT-{today}-"
    last = db.query(Quotation).filter(
        Quotation.quotation_number.like(f"{prefix}%")
    ).order_by(Quotation.id.desc()).first()
    seq = 1
    if last:
        try:
            seq = int(last.quotation_number.split("-")[-1]) + 1
        except:
            pass
    return f"{prefix}{seq:03d}"


def generate_sale_order_number(db: Session) -> str:
    """Generate sale order number: SO-YYYYMMDD-XXX"""
    today = date.today().strftime("%Y%m%d")
    prefix = f"SO-{today}-"
    last = db.query(SaleOrder).filter(
        SaleOrder.order_number.like(f"{prefix}%")
    ).order_by(SaleOrder.id.desc()).first()
    seq = 1
    if last:
        try:
            seq = int(last.order_number.split("-")[-1]) + 1
        except:
            pass
    return f"{prefix}{seq:03d}"


@router.get("/", response_model=List[QuotationResponse])
def list_quotations(
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List all quotations, optionally filtered by status."""
    query = db.query(Quotation)
    if status:
        query = query.filter(Quotation.status == status)
    return query.order_by(Quotation.quotation_date.desc()).limit(limit).all()


@router.get("/{quotation_id}", response_model=QuotationResponse)
def get_quotation(quotation_id: int, db: Session = Depends(get_db)):
    """Get quotation details."""
    quotation = db.query(Quotation).filter(Quotation.id == quotation_id).first()
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")
    return quotation


@router.get("/{quotation_id}/items", response_model=List[QuotationItemResponse])
def get_quotation_items(quotation_id: int, db: Session = Depends(get_db)):
    """Get line items for a quotation."""
    items = db.query(QuotationItem).filter(QuotationItem.quotation_id == quotation_id).all()
    return items


@router.post("/", response_model=QuotationResponse, status_code=status.HTTP_201_CREATED)
def create_quotation(data: QuotationCreate, db: Session = Depends(get_db)):
    """Create a new quotation with line items."""
    # Validate customer
    customer = db.query(Customer).filter(Customer.id == data.customer_id).first()
    if not customer:
        raise HTTPException(status_code=400, detail="Customer not found")
    
    # Create quotation
    quotation = Quotation(
        quotation_number=generate_quotation_number(db),
        quotation_date=date.today(),
        valid_until=date.today() + timedelta(days=data.valid_days),
        customer_id=data.customer_id,
        status=QuotationStatus.DRAFT.value,
        payment_terms=data.payment_terms,
        delivery_terms=data.delivery_terms,
        notes=data.notes
    )
    db.add(quotation)
    db.flush()  # Get ID
    
    # Add items
    subtotal = Decimal(0)
    total_tax = Decimal(0)
    
    for item_data in data.items:
        # Validate product
        product = db.query(Product).filter(Product.id == item_data.product_id).first()
        if not product:
            raise HTTPException(status_code=400, detail=f"Product {item_data.product_id} not found")
        
        qty = Decimal(str(item_data.quantity))
        rate = Decimal(str(item_data.rate))
        amount = qty * rate
        tax_rate = product.gst_rate or Decimal("18.0")
        tax_amount = amount * (tax_rate / 100)
        total_amount = amount + tax_amount
        
        item = QuotationItem(
            quotation_id=quotation.id,
            product_id=item_data.product_id,
            description=item_data.description or product.name,
            quantity=qty,
            unit=product.unit,
            rate=rate,
            amount=amount,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            total_amount=total_amount
        )
        db.add(item)
        
        subtotal += amount
        total_tax += tax_amount
    
    # Update quotation totals
    quotation.subtotal = subtotal
    quotation.tax_amount = total_tax
    quotation.total_amount = subtotal + total_tax
    
    db.commit()
    db.refresh(quotation)
    return quotation


@router.put("/{quotation_id}/send")
def send_quotation(quotation_id: int, db: Session = Depends(get_db)):
    """Mark quotation as sent to customer."""
    quotation = db.query(Quotation).filter(Quotation.id == quotation_id).first()
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")
    
    if quotation.status != QuotationStatus.DRAFT.value:
        raise HTTPException(status_code=400, detail="Only DRAFT quotations can be sent")
    
    quotation.status = QuotationStatus.SENT.value
    db.commit()
    return {"message": "Quotation sent", "quotation_number": quotation.quotation_number, "status": quotation.status}


@router.put("/{quotation_id}/accept")
def accept_quotation(quotation_id: int, db: Session = Depends(get_db)):
    """Mark quotation as accepted by customer."""
    quotation = db.query(Quotation).filter(Quotation.id == quotation_id).first()
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")
    
    if quotation.status != QuotationStatus.SENT.value:
        raise HTTPException(status_code=400, detail="Only SENT quotations can be accepted")
    
    quotation.status = QuotationStatus.ACCEPTED.value
    db.commit()
    return {"message": "Quotation accepted", "quotation_number": quotation.quotation_number, "status": quotation.status}


@router.put("/{quotation_id}/reject")
def reject_quotation(quotation_id: int, db: Session = Depends(get_db)):
    """Mark quotation as rejected by customer."""
    quotation = db.query(Quotation).filter(Quotation.id == quotation_id).first()
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")
    
    if quotation.status != QuotationStatus.SENT.value:
        raise HTTPException(status_code=400, detail="Only SENT quotations can be rejected")
    
    quotation.status = QuotationStatus.REJECTED.value
    db.commit()
    return {"message": "Quotation rejected", "quotation_number": quotation.quotation_number, "status": quotation.status}


@router.post("/{quotation_id}/convert", response_model=SaleOrderResponse)
def convert_to_sale_order(quotation_id: int, db: Session = Depends(get_db)):
    """Convert an accepted quotation to a Sale Order."""
    quotation = db.query(Quotation).filter(Quotation.id == quotation_id).first()
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")
    
    if quotation.status != QuotationStatus.ACCEPTED.value:
        raise HTTPException(status_code=400, detail="Only ACCEPTED quotations can be converted to Sale Orders")
    
    # Create Sale Order
    sale_order = SaleOrder(
        order_number=generate_sale_order_number(db),
        order_date=date.today(),
        customer_id=quotation.customer_id,
        quotation_id=quotation.id,
        status=SaleOrderStatus.CONFIRMED.value,
        subtotal=quotation.subtotal,
        tax_amount=quotation.tax_amount,
        discount_amount=quotation.discount_amount,
        total_amount=quotation.total_amount,
        notes=quotation.notes
    )
    db.add(sale_order)
    db.flush()
    
    # Copy items from quotation
    quotation_items = db.query(QuotationItem).filter(QuotationItem.quotation_id == quotation_id).all()
    for qi in quotation_items:
        soi = SaleOrderItem(
            sale_order_id=sale_order.id,
            product_id=qi.product_id,
            description=qi.description,
            quantity=qi.quantity,
            unit=qi.unit,
            rate=qi.rate,
            dispatched_quantity=Decimal("0"),
            pending_quantity=qi.quantity,
            amount=qi.amount,
            tax_rate=qi.tax_rate,
            tax_amount=qi.tax_amount,
            total_amount=qi.total_amount
        )
        db.add(soi)
    
    # Update quotation status
    quotation.status = QuotationStatus.CONVERTED.value
    quotation.sale_order_id = sale_order.id
    
    db.commit()
    db.refresh(sale_order)
    return sale_order


# ═══════════════════════════════════════════════════════════
# SALE ORDER ENDPOINTS
# ═══════════════════════════════════════════════════════════

@router.get("/orders/list", response_model=List[SaleOrderResponse])
def list_sale_orders(
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List all sale orders."""
    query = db.query(SaleOrder)
    if status:
        query = query.filter(SaleOrder.status == status)
    return query.order_by(SaleOrder.order_date.desc()).limit(limit).all()


@router.get("/orders/{order_id}", response_model=SaleOrderResponse)
def get_sale_order(order_id: int, db: Session = Depends(get_db)):
    """Get sale order details."""
    order = db.query(SaleOrder).filter(SaleOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Sale Order not found")
    return order


@router.get("/summary")
def get_quotation_summary(db: Session = Depends(get_db)):
    """Get quotation and sale order summary."""
    # Quotation counts by status
    quotation_counts = db.query(
        Quotation.status,
        func.count(Quotation.id)
    ).group_by(Quotation.status).all()
    
    quot_by_status = {status: count for status, count in quotation_counts}
    
    # Sale order counts by status
    order_counts = db.query(
        SaleOrder.status,
        func.count(SaleOrder.id)
    ).group_by(SaleOrder.status).all()
    
    orders_by_status = {status: count for status, count in order_counts}
    
    # Totals
    total_quotations = db.query(func.count(Quotation.id)).scalar() or 0
    total_orders = db.query(func.count(SaleOrder.id)).scalar() or 0
    pending_value = db.query(func.sum(Quotation.total_amount)).filter(
        Quotation.status.in_([QuotationStatus.DRAFT.value, QuotationStatus.SENT.value])
    ).scalar() or 0
    
    return {
        "total_quotations": total_quotations,
        "total_orders": total_orders,
        "quotations_by_status": quot_by_status,
        "orders_by_status": orders_by_status,
        "pending_quotation_value": float(pending_value)
    }
