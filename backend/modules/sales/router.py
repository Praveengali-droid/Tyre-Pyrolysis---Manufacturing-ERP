"""
Sales Router - Products, Customers, and Dispatch (Carbon, Steel)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal

from database import get_db
from models.customer import Customer
from models.product import Product
from models.output_dispatch import CarbonDispatch, SteelDispatch

router = APIRouter(prefix="/sales", tags=["Sales"])


# ═══════════════════════════════════════════════════════════
# SCHEMAS
# ═══════════════════════════════════════════════════════════

# Product Schemas
class ProductCreate(BaseModel):
    name: str
    product_type: str  # OIL, CARBON, STEEL, OTHER
    hsn_code: Optional[str] = None
    gst_rate: float = 18.0
    unit: str = "KG"
    default_rate: Optional[float] = None
    description: Optional[str] = None

class ProductResponse(BaseModel):
    id: int
    product_code: str
    name: str
    product_type: str
    hsn_code: Optional[str] = None
    gst_rate: Optional[float] = 18.0
    unit: str
    default_rate: Optional[float] = None
    current_stock: Optional[float] = 0.0
    is_active: bool
    
    class Config:
        from_attributes = True

# Customer Schemas
class CustomerCreate(BaseModel):
    name: str
    customer_type: str = "ALL"
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    payment_terms_days: int = 30
    credit_limit: int = 0

class CustomerResponse(BaseModel):
    id: int
    customer_code: str
    name: str
    customer_type: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    payment_terms_days: Optional[int] = 30
    credit_limit: Optional[int] = 0
    is_active: bool
    
    class Config:
        from_attributes = True

# Dispatch Schemas
class DispatchCreate(BaseModel):
    customer_id: int
    quantity_kg: float
    rate_per_kg: float
    vehicle_number: Optional[str] = None
    driver_name: Optional[str] = None
    invoice_number: Optional[str] = None
    notes: Optional[str] = None

class DispatchResponse(BaseModel):
    id: int
    dispatch_code: str
    customer_id: Optional[int]
    quantity_kg: float
    rate_per_kg: Optional[float]
    total_amount: Optional[float]
    dispatch_date: date
    vehicle_number: Optional[str]
    invoice_number: Optional[str]
    customer_confirmed: bool
    
    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════
# PRODUCT ENDPOINTS
# ═══════════════════════════════════════════════════════════

def generate_product_code(db: Session) -> str:
    """Generate product code: PROD-XXX"""
    last = db.query(Product).order_by(Product.id.desc()).first()
    seq = (last.id + 1) if last else 1
    return f"PROD-{seq:03d}"


@router.get("/products", response_model=List[ProductResponse])
def list_products(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """List all products."""
    query = db.query(Product)
    if active_only:
        query = query.filter(Product.is_active == True)
    return query.order_by(Product.name).all()


@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(data: ProductCreate, db: Session = Depends(get_db)):
    """Create a new product."""
    product = Product(
        product_code=generate_product_code(db),
        name=data.name,
        product_type=data.product_type,
        hsn_code=data.hsn_code,
        gst_rate=Decimal(str(data.gst_rate)) if data.gst_rate else None,
        unit=data.unit,
        default_rate=Decimal(str(data.default_rate)) if data.default_rate else None,
        description=data.description
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get product details."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


# ═══════════════════════════════════════════════════════════
# CUSTOMER ENDPOINTS
# ═══════════════════════════════════════════════════════════

def generate_customer_code(db: Session) -> str:
    """Generate customer code: CUST-XXX"""
    last = db.query(Customer).order_by(Customer.id.desc()).first()
    seq = (last.id + 1) if last else 1
    return f"CUST-{seq:03d}"


@router.get("/customers", response_model=List[CustomerResponse])
def list_customers(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """List all customers."""
    query = db.query(Customer)
    if active_only:
        query = query.filter(Customer.is_active == True)
    return query.order_by(Customer.name).all()


@router.post("/customers", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(data: CustomerCreate, db: Session = Depends(get_db)):
    """Create a new customer."""
    customer = Customer(
        customer_code=generate_customer_code(db),
        name=data.name,
        customer_type=data.customer_type,
        contact_person=data.contact_person,
        phone=data.phone,
        email=data.email,
        address=data.address,
        city=data.city,
        state=data.state,
        pincode=data.pincode,
        gst_number=data.gst_number,
        pan_number=data.pan_number,
        payment_terms_days=data.payment_terms_days,
        credit_limit=data.credit_limit
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    """Get customer details."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.get("/customers/{customer_id}/ledger")
def get_customer_ledger(customer_id: int, db: Session = Depends(get_db)):
    """Get customer ledger with transaction history."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Get all dispatches for this customer
    carbon_dispatches = db.query(CarbonDispatch).filter(
        CarbonDispatch.customer_id == customer_id
    ).order_by(CarbonDispatch.dispatch_date.desc()).all()
    
    steel_dispatches = db.query(SteelDispatch).filter(
        SteelDispatch.customer_id == customer_id
    ).order_by(SteelDispatch.dispatch_date.desc()).all()
    
    # Calculate totals
    carbon_total = sum(float(d.total_amount or 0) for d in carbon_dispatches)
    steel_total = sum(float(d.total_amount or 0) for d in steel_dispatches)
    
    return {
        "customer": {
            "id": customer.id,
            "code": customer.customer_code,
            "name": customer.name
        },
        "summary": {
            "total_carbon_orders": len(carbon_dispatches),
            "total_steel_orders": len(steel_dispatches),
            "carbon_amount": carbon_total,
            "steel_amount": steel_total,
            "total_amount": carbon_total + steel_total
        },
        "carbon_dispatches": [
            {
                "dispatch_code": d.dispatch_code,
                "date": str(d.dispatch_date),
                "quantity_kg": float(d.quantity_kg),
                "amount": float(d.total_amount or 0)
            } for d in carbon_dispatches
        ],
        "steel_dispatches": [
            {
                "dispatch_code": d.dispatch_code,
                "date": str(d.dispatch_date),
                "quantity_kg": float(d.quantity_kg),
                "amount": float(d.total_amount or 0)
            } for d in steel_dispatches
        ]
    }


# ═══════════════════════════════════════════════════════════
# CARBON DISPATCH ENDPOINTS
# ═══════════════════════════════════════════════════════════

def generate_carbon_dispatch_code(db: Session) -> str:
    """Generate dispatch code: CD-YYYYMMDD-XXX"""
    today = date.today().strftime("%Y%m%d")
    prefix = f"CD-{today}-"
    last = db.query(CarbonDispatch).filter(
        CarbonDispatch.dispatch_code.like(f"{prefix}%")
    ).order_by(CarbonDispatch.id.desc()).first()
    seq = 1
    if last:
        try:
            seq = int(last.dispatch_code.split("-")[-1]) + 1
        except:
            pass
    return f"{prefix}{seq:03d}"


@router.get("/carbon/dispatches", response_model=List[DispatchResponse])
def list_carbon_dispatches(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List recent carbon dispatches."""
    dispatches = db.query(CarbonDispatch).order_by(
        CarbonDispatch.dispatch_date.desc()
    ).limit(limit).all()
    return dispatches


@router.post("/carbon/dispatch", response_model=DispatchResponse, status_code=status.HTTP_201_CREATED)
def create_carbon_dispatch(data: DispatchCreate, db: Session = Depends(get_db)):
    """Create a carbon dispatch (sale)."""
    # Validate customer
    customer = db.query(Customer).filter(Customer.id == data.customer_id).first()
    if not customer:
        raise HTTPException(status_code=400, detail="Customer not found")
    
    total_amount = data.quantity_kg * data.rate_per_kg
    
    dispatch = CarbonDispatch(
        dispatch_code=generate_carbon_dispatch_code(db),
        customer_id=data.customer_id,
        quantity_kg=Decimal(str(data.quantity_kg)),
        rate_per_kg=Decimal(str(data.rate_per_kg)),
        total_amount=Decimal(str(total_amount)),
        dispatch_date=date.today(),
        vehicle_number=data.vehicle_number,
        driver_name=data.driver_name,
        invoice_number=data.invoice_number,
        notes=data.notes
    )
    db.add(dispatch)
    db.commit()
    db.refresh(dispatch)
    return dispatch


@router.put("/carbon/dispatches/{dispatch_id}/confirm")
def confirm_carbon_receipt(dispatch_id: int, db: Session = Depends(get_db)):
    """Mark carbon dispatch as received by customer."""
    dispatch = db.query(CarbonDispatch).filter(CarbonDispatch.id == dispatch_id).first()
    if not dispatch:
        raise HTTPException(status_code=404, detail="Dispatch not found")
    
    dispatch.customer_confirmed = True
    db.commit()
    return {"message": "Receipt confirmed", "dispatch_code": dispatch.dispatch_code}


# ═══════════════════════════════════════════════════════════
# STEEL DISPATCH ENDPOINTS
# ═══════════════════════════════════════════════════════════

def generate_steel_dispatch_code(db: Session) -> str:
    """Generate dispatch code: SD-YYYYMMDD-XXX"""
    today = date.today().strftime("%Y%m%d")
    prefix = f"SD-{today}-"
    last = db.query(SteelDispatch).filter(
        SteelDispatch.dispatch_code.like(f"{prefix}%")
    ).order_by(SteelDispatch.id.desc()).first()
    seq = 1
    if last:
        try:
            seq = int(last.dispatch_code.split("-")[-1]) + 1
        except:
            pass
    return f"{prefix}{seq:03d}"


@router.get("/steel/dispatches", response_model=List[DispatchResponse])
def list_steel_dispatches(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List recent steel dispatches."""
    dispatches = db.query(SteelDispatch).order_by(
        SteelDispatch.dispatch_date.desc()
    ).limit(limit).all()
    return dispatches


@router.post("/steel/dispatch", response_model=DispatchResponse, status_code=status.HTTP_201_CREATED)
def create_steel_dispatch(data: DispatchCreate, db: Session = Depends(get_db)):
    """Create a steel dispatch (sale)."""
    # Validate customer
    customer = db.query(Customer).filter(Customer.id == data.customer_id).first()
    if not customer:
        raise HTTPException(status_code=400, detail="Customer not found")
    
    total_amount = data.quantity_kg * data.rate_per_kg
    
    dispatch = SteelDispatch(
        dispatch_code=generate_steel_dispatch_code(db),
        customer_id=data.customer_id,
        quantity_kg=Decimal(str(data.quantity_kg)),
        rate_per_kg=Decimal(str(data.rate_per_kg)),
        total_amount=Decimal(str(total_amount)),
        dispatch_date=date.today(),
        vehicle_number=data.vehicle_number,
        driver_name=data.driver_name,
        invoice_number=data.invoice_number,
        notes=data.notes
    )
    db.add(dispatch)
    db.commit()
    db.refresh(dispatch)
    return dispatch


@router.put("/steel/dispatches/{dispatch_id}/confirm")
def confirm_steel_receipt(dispatch_id: int, db: Session = Depends(get_db)):
    """Mark steel dispatch as received by customer."""
    dispatch = db.query(SteelDispatch).filter(SteelDispatch.id == dispatch_id).first()
    if not dispatch:
        raise HTTPException(status_code=404, detail="Dispatch not found")
    
    dispatch.customer_confirmed = True
    db.commit()
    return {"message": "Receipt confirmed", "dispatch_code": dispatch.dispatch_code}


# ═══════════════════════════════════════════════════════════
# SALES SUMMARY
# ═══════════════════════════════════════════════════════════

@router.get("/summary")
def get_sales_summary(db: Session = Depends(get_db)):
    """Get sales summary for dashboard with time-based stats."""
    from datetime import timedelta
    
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)
    start_of_year = today.replace(month=1, day=1)
    
    # Helper to get counts and revenue for date range
    def get_dispatch_stats(start_date=None):
        carbon_q = db.query(
            func.count(CarbonDispatch.id),
            func.sum(CarbonDispatch.total_amount)
        )
        steel_q = db.query(
            func.count(SteelDispatch.id),
            func.sum(SteelDispatch.total_amount)
        )
        if start_date:
            carbon_q = carbon_q.filter(CarbonDispatch.dispatch_date >= start_date)
            steel_q = steel_q.filter(SteelDispatch.dispatch_date >= start_date)
        
        carbon = carbon_q.first()
        steel = steel_q.first()
        
        return {
            "orders": (carbon[0] or 0) + (steel[0] or 0),
            "revenue": float((carbon[1] or 0) + (steel[1] or 0))
        }
    
    # Time-based stats
    stats_today = get_dispatch_stats(today)
    stats_week = get_dispatch_stats(start_of_week)
    stats_month = get_dispatch_stats(start_of_month)
    stats_year = get_dispatch_stats(start_of_year)
    stats_all = get_dispatch_stats(None)
    
    # Customer and Product counts
    customer_count = db.query(func.count(Customer.id)).filter(Customer.is_active == True).scalar() or 0
    product_count = db.query(func.count(Product.id)).filter(Product.is_active == True).scalar() or 0
    
    # Top products by default rate * some assumed stock (for demo, using default_rate as value indicator)
    # In future, calculate actual stock from batch outputs - dispatches
    top_products = db.query(Product).filter(
        Product.is_active == True,
        Product.default_rate.isnot(None)
    ).order_by(Product.default_rate.desc()).limit(3).all()
    
    top_products_list = [
        {
            "name": p.name,
            "product_type": p.product_type,
            "unit": p.unit,
            "rate": float(p.default_rate or 0),
            "stock": float(p.current_stock or 0),
            "value": float((p.current_stock or 0) * (p.default_rate or 0))
        }
        for p in top_products
    ]
    
    return {
        "customer_count": customer_count,
        "product_count": product_count,
        # Time-based order stats
        "orders_today": stats_today["orders"],
        "orders_week": stats_week["orders"],
        "orders_month": stats_month["orders"],
        "orders_year": stats_year["orders"],
        "orders_total": stats_all["orders"],
        # Time-based revenue stats
        "revenue_today": stats_today["revenue"],
        "revenue_week": stats_week["revenue"],
        "revenue_month": stats_month["revenue"],
        "revenue_year": stats_year["revenue"],
        "revenue_total": stats_all["revenue"],
        # Top products
        "top_products": top_products_list
    }

