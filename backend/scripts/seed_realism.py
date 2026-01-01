"""
Comprehensive Database Seed Script for Tyre Pyrolysis ERP (ORM Version).

Generates 90 days of realistic plant history for full report coverage.

Features:
- 3 Character Vendors (Premium/Budget/Risky) with get_or_create
- 5 OPEN Purchase Orders for pending procurement metrics
- 60 GRNs (55 historical + 5 today)
- 58 Production Batches (55 completed + 3 active)
- MaintenanceSchedule + MaintenanceLogs for downtime analysis
- 12 Sale Orders with Dispatches and Invoices
- 1 Sales Return (RECEIVED - Pending QC)

Usage:
    cd backend
    source venv/bin/activate
    python scripts/seed_realism.py          # Append new data
    python scripts/seed_realism.py --wipe   # Wipe existing data first

Author: AI Assistant
Date: 2026-01-01
"""
import sys
import os
import random
from datetime import datetime, timedelta, date
from decimal import Decimal
import argparse

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database import SessionLocal, Base

# Import all models
from models.vendor import Vendor
from models.raw_material import RawMaterial
from models.purchase_order import PurchaseOrder, PurchaseOrderItem
from models.grn import GoodsReceiptNote, GRNStatus
from models.inventory_lot import InventoryLot
from models.reactor import Reactor
from models.production_batch import ProductionBatch, BatchStatus
from models.storage_tank import StorageTank
from models.customer import Customer
from models.product import Product
from models.quotation import SaleOrder, SaleOrderItem
from models.dispatch import SalesDispatch, SalesDispatchItem, SalesInvoice
from models.sales_return import SalesReturn, SalesReturnItem
from models.maintenance import MaintenanceSchedule, MaintenanceLog, MaintenanceRequest

# ═══════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════

DAYS_OF_HISTORY = 90
NUM_BATCHES_HISTORICAL = 55
NUM_ACTIVE_BATCHES = 3
NUM_GRNS_TODAY = 5
NUM_OPEN_POS = 5
NUM_SALE_ORDERS = 12
OIL_DENSITY = 0.85

# Vendor profiles for yield variation
VENDOR_PROFILES = {
    "PREMIUM": {
        "name": "ShreeSai Rubber Industries",
        "city": "Hyderabad",
        "price_range": (13, 15),
        "oil_yield_range": (43, 47),
        "carbon_yield_range": (32, 36),
        "steel_yield_range": (10, 14),
        "deduction_pct": (1, 3),
        "quality_grade": "A",
    },
    "BUDGET": {
        "name": "Bharat Scrap Traders",
        "city": "Vijayawada",
        "price_range": (9, 11),
        "oil_yield_range": (38, 42),
        "carbon_yield_range": (30, 34),
        "steel_yield_range": (12, 16),
        "deduction_pct": (5, 10),
        "quality_grade": "B",
    },
    "RISKY": {
        "name": "Quick Tyres & Rubber",
        "city": "Guntur",
        "price_range": (10, 14),
        "oil_yield_range": (32, 38),
        "carbon_yield_range": (28, 32),
        "steel_yield_range": (14, 18),
        "deduction_pct": (8, 15),
        "quality_grade": "C",
    }
}

LOSS_MONTH = 11  # November will be a loss month


# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════

def random_date_in_range(start_days_ago: int, end_days_ago: int) -> date:
    days_ago = random.randint(end_days_ago, start_days_ago)
    return date.today() - timedelta(days=days_ago)

def random_datetime_in_range(start_days_ago: int, end_days_ago: int) -> datetime:
    d = random_date_in_range(start_days_ago, end_days_ago)
    hour = random.randint(6, 18)
    minute = random.randint(0, 59)
    return datetime.combine(d, datetime.min.time().replace(hour=hour, minute=minute))

def get_or_create_vendor(db: Session, profile_key: str, profile: dict) -> Vendor:
    """Get existing vendor by name or create new one."""
    existing = db.query(Vendor).filter(Vendor.name == profile["name"]).first()
    if existing:
        return existing
    
    vendor = Vendor(
        vendor_code=f"V-{profile_key[:4]}-001",
        name=profile["name"],
        vendor_type="SUPPLIER",
        contact_person=f"Manager - {profile['name'].split()[0]}",
        phone=f"98765{random.randint(10000, 99999)}",
        email=f"sales@{profile['name'].lower().replace(' ', '')[:10]}.com",
        city=profile["city"],
        state="Andhra Pradesh",
        country="India",
        pincode=f"5{random.randint(10000, 99999)}",
        gst_number=f"37{''.join([str(random.randint(0,9)) for _ in range(10)])}1Z{random.randint(0,9)}",
        gst_vendor_type="REGISTERED",
        is_epr_compliant=(profile_key != "RISKY"),
        credit_days=30 if profile_key == "PREMIUM" else 15,
        is_active=True
    )
    db.add(vendor)
    db.flush()
    return vendor


# ═══════════════════════════════════════════════════════════
# SETUP FUNCTIONS
# ═══════════════════════════════════════════════════════════

def setup_vendors(db: Session) -> dict:
    """Setup 3 character vendors using get_or_create."""
    print("📦 Setting up vendors (get_or_create on name)...")
    vendors = {}
    for profile_key, profile in VENDOR_PROFILES.items():
        vendor = get_or_create_vendor(db, profile_key, profile)
        vendors[profile_key] = vendor
        is_new = "(created)" if not vendor.id or vendor.id > 100 else "(existing)"
        print(f"  ✓ {profile_key}: {vendor.name} {is_new}")
    return vendors

def setup_raw_material(db: Session) -> RawMaterial:
    """Get or create waste tyre raw material."""
    existing = db.query(RawMaterial).filter(RawMaterial.material_code == "RM001").first()
    if existing:
        return existing
    material = RawMaterial(
        material_code="RM001", name="Waste Tyres (Mixed)", material_type="WASTE_TYRE",
        hsn_code="4004", gst_rate=Decimal("5.0"), minimum_stock_kg=Decimal("1000"), is_active=True
    )
    db.add(material)
    db.flush()
    return material

def setup_reactors(db: Session) -> list:
    """Setup 3 reactors with maintenance states for interlock testing."""
    print("🏭 Setting up reactors...")
    reactors = []
    configs = [("R1", "Reactor Alpha", 0), ("R2", "Reactor Beta", 2), ("R3", "Reactor Gamma", 3)]
    
    for code, name, batches in configs:
        reactor = db.query(Reactor).filter(Reactor.reactor_code == code).first()
        if reactor:
            reactor.batches_since_last_cleaning = batches
            reactor.maintenance_frequency = 3
            reactor.status = "MAINTENANCE" if batches >= 3 else "IDLE"
        else:
            reactor = Reactor(
                reactor_code=code, name=name, capacity_kg=Decimal("600"),
                status="IDLE" if batches < 3 else "MAINTENANCE",
                batches_since_last_cleaning=batches, maintenance_frequency=3, is_active=True
            )
            db.add(reactor)
            db.flush()
        reactors.append(reactor)
        status = "⚠️ WARNING" if batches == 2 else ("🔒 LOCKED" if batches >= 3 else "✓")
        print(f"  {status} {code}: {name} (batches: {batches}/3)")
    return reactors

def setup_tank(db: Session) -> StorageTank:
    tank = db.query(StorageTank).filter(StorageTank.tank_code == "TK-OIL-01").first()
    if not tank:
        tank = StorageTank(
            tank_code="TK-OIL-01", name="Main Oil Storage", tank_type="STORAGE",
            capacity_liters=Decimal("50000"), current_level_liters=Decimal("5000"), is_active=True
        )
        db.add(tank)
        db.flush()
    return tank

def setup_customers(db: Session) -> list:
    """Setup customer masters."""
    print("👥 Setting up customers...")
    customers = []
    customer_data = [
        ("CUST-001", "Mahalakshmi Oils Pvt Ltd", "Guntur"),
        ("CUST-002", "Andhra Industries", "Vijayawada"),
        ("CUST-003", "Krishna Chemicals", "Hyderabad"),
    ]
    for code, name, city in customer_data:
        existing = db.query(Customer).filter(Customer.customer_code == code).first()
        if existing:
            customers.append(existing)
            print(f"  ✓ {name} (existing)")
            continue
        customer = Customer(
            customer_code=code, name=name, customer_type="ALL",
            contact_person="Purchase Manager", phone=f"98765{random.randint(10000, 99999)}",
            email=f"purchase@{name.lower().split()[0]}.com", city=city, state="Andhra Pradesh",
            pincode=f"5{random.randint(10000, 99999)}",
            gst_number=f"37{''.join([str(random.randint(0,9)) for _ in range(10)])}1Z{random.randint(0,9)}",
            credit_limit=500000, payment_terms_days=30, is_active=True
        )
        db.add(customer)
        db.flush()
        customers.append(customer)
        print(f"  ✓ {name} (created)")
    return customers

def setup_products(db: Session) -> dict:
    """Setup product masters."""
    products = {}
    product_data = [
        ("PRD-OIL-001", "Pyrolysis Oil (TFO)", "OIL", "LITERS", 45.00),
        ("PRD-CBK-001", "Carbon Black", "CARBON", "KG", 18.00),
        ("PRD-STL-001", "Steel Scrap", "STEEL", "KG", 25.00),
    ]
    for code, name, ptype, unit, price in product_data:
        prod = db.query(Product).filter(Product.product_code == code).first()
        if not prod:
            prod = Product(product_code=code, name=name, product_type=ptype,
                           unit=unit, default_rate=Decimal(str(price)), gst_rate=Decimal("18.0"), is_active=True)
            db.add(prod)
            db.flush()
        products[ptype] = prod
    return products

def setup_maintenance_schedules(db: Session, reactors: list) -> dict:
    """Setup maintenance schedules for reactors (required for MaintenanceLog FK)."""
    print("🔧 Setting up maintenance schedules...")
    schedules = {}
    task_names = ["Carbon Cleaning", "Seal Inspection", "Temperature Check", "Pressure Test"]
    
    for reactor in reactors:
        for task_name in task_names:
            existing = db.query(MaintenanceSchedule).filter(
                MaintenanceSchedule.reactor_id == reactor.id,
                MaintenanceSchedule.task_name == task_name
            ).first()
            if not existing:
                schedule = MaintenanceSchedule(
                    reactor_id=reactor.id, equipment_type="REACTOR", task_name=task_name,
                    task_description=f"{task_name} for {reactor.name}",
                    frequency_batches=3, frequency_days=30, warning_batches=2, is_active=True
                )
                db.add(schedule)
                db.flush()
                schedules[(reactor.id, task_name)] = schedule
            else:
                schedules[(reactor.id, task_name)] = existing
    
    print(f"  ✓ Created schedules for {len(task_names)} tasks per reactor")
    return schedules


# ═══════════════════════════════════════════════════════════
# DATA CREATION FUNCTIONS
# ═══════════════════════════════════════════════════════════

def create_purchase_orders(db: Session, vendors: dict, material: RawMaterial) -> list:
    """Create 5 OPEN POs for pending procurement metrics."""
    print(f"\n📋 Creating {NUM_OPEN_POS} OPEN Purchase Orders...")
    pos = []
    po_counter = db.query(PurchaseOrder).count()
    
    vendor_list = list(vendors.values())
    for i in range(NUM_OPEN_POS):
        vendor = random.choice(vendor_list)
        order_date = date.today() - timedelta(days=random.randint(1, 10))
        expected_date = order_date + timedelta(days=random.randint(5, 15))
        qty = Decimal(str(random.randint(500, 2000)))
        rate = Decimal(str(random.uniform(10, 14)))
        
        po_counter += 1
        po = PurchaseOrder(
            po_number=f"PO-{order_date.strftime('%Y%m')}-{po_counter:04d}",
            vendor_id=vendor.id, order_date=order_date, expected_delivery_date=expected_date,
            status="CONFIRMED",  # CONFIRMED = Open, awaiting receipt
            subtotal_amount=qty * rate, total_amount=qty * rate * Decimal("1.05"),
            payment_terms="Net 30", notes=f"Pending delivery from {vendor.name}"
        )
        db.add(po)
        db.flush()
        
        # Add line item
        item = PurchaseOrderItem(
            purchase_order_id=po.id, raw_material_id=material.id,
            ordered_qty_kg=qty, received_qty_kg=Decimal("0"), pending_qty_kg=qty,
            rate_per_kg=rate, hsn_code="4004", gst_rate=Decimal("5.0"),
            line_amount=qty * rate, gst_amount=qty * rate * Decimal("0.05"), total_amount=qty * rate * Decimal("1.05")
        )
        db.add(item)
        pos.append(po)
    
    print(f"  ✓ Created {NUM_OPEN_POS} OPEN/CONFIRMED POs")
    return pos

def create_production_data(db: Session, vendors: dict, material: RawMaterial, 
                           reactors: list, tank: StorageTank, include_today: bool = True) -> list:
    """Create GRNs, Lots, and Batches."""
    total_batches = NUM_BATCHES_HISTORICAL
    print(f"\n🔄 Creating {total_batches} historical + {NUM_GRNS_TODAY} today's GRNs...")
    
    batch_data = []
    grn_counter = db.query(GoodsReceiptNote).count()
    batch_counter = db.query(ProductionBatch).count()
    lot_counter = db.query(InventoryLot).count()
    
    usable_reactors = [r for r in reactors if r.reactor_code != "R3"]
    vendor_dist = ["PREMIUM"] * 22 + ["BUDGET"] * 22 + ["RISKY"] * 11
    random.shuffle(vendor_dist)
    
    def create_batch_chain(profile_key: str, batch_dt: date, batch_datetime: datetime, 
                           status: str = "COMPLETED"):
        nonlocal grn_counter, batch_counter, lot_counter
        
        profile = VENDOR_PROFILES[profile_key]
        vendor = vendors[profile_key]
        
        gross_weight = random.uniform(500, 650)
        tare_weight = random.uniform(50, 80)
        net_weight = gross_weight - tare_weight
        deduction_pct = random.uniform(*profile["deduction_pct"])
        deduction_kg = net_weight * (deduction_pct / 100)
        rate_per_kg = random.uniform(*profile["price_range"])
        
        grn_counter += 1
        grn = GoodsReceiptNote(
            grn_number=f"GRN-{batch_dt.strftime('%Y%m')}-{grn_counter:04d}",
            vendor_id=vendor.id, raw_material_id=material.id,
            receipt_date=batch_dt, receipt_datetime=batch_datetime,
            vehicle_number=f"AP{random.randint(10,39)}T{random.randint(1000,9999)}",
            gross_weight_kg=Decimal(str(round(gross_weight, 2))),
            tare_weight_kg=Decimal(str(round(tare_weight, 2))),
            net_weight_kg=Decimal(str(round(net_weight, 2))),
            deduction_1_type="MUD" if deduction_kg > 0 else None,
            deduction_1_weight_kg=Decimal(str(round(deduction_kg, 2))) if deduction_kg > 0 else None,
            rate_per_kg=Decimal(str(round(rate_per_kg, 2))), gst_rate=Decimal("5.0"),
            quality_grade=profile["quality_grade"], status=GRNStatus.APPROVED.value, inventory_updated=True,
        )
        grn.calculate_financials(is_interstate=False)
        db.add(grn)
        db.flush()
        
        lot_counter += 1
        lot = InventoryLot(
            lot_id=f"LOT-{batch_dt.strftime('%Y%m%d')}-{lot_counter:04d}",
            grn_id=grn.id, vendor_id=vendor.id, raw_material_id=material.id,
            receipt_date=batch_dt, vehicle_number=grn.vehicle_number,
            received_qty_kg=Decimal(str(round(net_weight, 2))),
            current_qty_kg=Decimal("0") if status == "COMPLETED" else Decimal(str(round(net_weight, 2))),
            consumed_qty_kg=Decimal(str(round(net_weight, 2))) if status == "COMPLETED" else Decimal("0"),
            rate_per_kg=grn.rate_per_kg, total_cost=Decimal(str(round(net_weight * rate_per_kg, 2))),
            is_exhausted=(status == "COMPLETED"), is_active=True
        )
        db.add(lot)
        db.flush()
        
        oil_yield = random.uniform(*profile["oil_yield_range"])
        carbon_yield = random.uniform(*profile["carbon_yield_range"])
        steel_yield = random.uniform(*profile["steel_yield_range"])
        oil_kg = net_weight * (oil_yield / 100)
        carbon_kg = net_weight * (carbon_yield / 100)
        steel_kg = net_weight * (steel_yield / 100)
        
        meter_start = random.uniform(10000, 50000)
        power_kwh = (net_weight / 100) * random.uniform(80, 120)
        meter_end = meter_start + power_kwh
        reactor = random.choice(usable_reactors)
        
        batch_counter += 1
        batch = ProductionBatch(
            batch_number=f"BATCH-{batch_dt.strftime('%Y%m%d')}-{batch_counter:03d}",
            reactor_id=reactor.id, input_lot_id=lot.id,
            input_weight_kg=Decimal(str(round(net_weight, 2))),
            batch_date=batch_dt, start_datetime=batch_datetime,
            end_datetime=batch_datetime + timedelta(hours=random.randint(4, 8)) if status == "COMPLETED" else None,
            meter_start=Decimal(str(round(meter_start, 2))),
            meter_end=Decimal(str(round(meter_end, 2))) if status == "COMPLETED" else None,
            electricity_rate=Decimal("8.50"),
            oil_output_kg=Decimal(str(round(oil_kg, 2))) if status == "COMPLETED" else None,
            carbon_output_kg=Decimal(str(round(carbon_kg, 2))) if status == "COMPLETED" else None,
            steel_output_kg=Decimal(str(round(steel_kg, 2))) if status == "COMPLETED" else None,
            destination_tank_id=tank.id, oil_quality_grade=profile["quality_grade"],
            carbon_quality_grade=profile["quality_grade"], status=status,
            completed_by="Operator" if status == "COMPLETED" else None,
        )
        if status == "COMPLETED":
            batch.calculate_electricity()
            batch.calculate_outputs()
            batch.convert_oil_to_liters()
        db.add(batch)
        db.flush()
        
        return {"batch": batch, "grn": grn, "vendor_type": profile_key, 
                "net_payable": float(grn.net_payable_amount or 0), "oil_kg": oil_kg, "date": batch_datetime}
    
    # Historical batches (all COMPLETED)
    for i in range(total_batches):
        profile_key = vendor_dist[i % len(vendor_dist)]
        batch_datetime = random_datetime_in_range(DAYS_OF_HISTORY, 2)
        batch_data.append(create_batch_chain(profile_key, batch_datetime.date(), batch_datetime, "COMPLETED"))
        if (i + 1) % 10 == 0:
            print(f"  ✓ Created {i + 1}/{total_batches} historical batches")
    
    # Today's GRNs + batches
    if include_today:
        today = date.today()
        active_statuses = ["LOADING", "IN_PROGRESS", "COOLING"]
        for i in range(NUM_GRNS_TODAY):
            profile_key = random.choice(list(VENDOR_PROFILES.keys()))
            now = datetime.now().replace(hour=8 + i, minute=random.randint(0, 59))
            status = active_statuses[i] if i < len(active_statuses) else "COMPLETED"
            batch_data.append(create_batch_chain(profile_key, today, now, status))
        print(f"  ✓ Created {NUM_GRNS_TODAY} today's GRNs + batches (3 active)")
    
    print(f"  ✓ All {len(batch_data)} batches created with mass balance")
    return batch_data

def create_maintenance_logs(db: Session, reactors: list, schedules: dict):
    """Create MaintenanceLog entries for downtime analysis."""
    print("\n🔧 Creating MaintenanceLogs for downtime analysis...")
    
    log_count = 0
    task_names = ["Carbon Cleaning", "Seal Inspection", "Temperature Check", "Pressure Test"]
    
    for reactor in reactors:
        num_logs = random.randint(5, 10)
        for _ in range(num_logs):
            task_name = random.choice(task_names)
            schedule = schedules.get((reactor.id, task_name))
            if not schedule:
                continue
            
            performed_date = random_datetime_in_range(DAYS_OF_HISTORY, 5)
            
            log = MaintenanceLog(
                schedule_id=schedule.id, reactor_id=reactor.id,
                performed_date=performed_date,
                performed_by=random.choice(["Rajesh", "Suresh", "Venkat", "Kumar"]),
                notes=f"Completed {task_name} on {reactor.reactor_code}",
                batches_at_maintenance=random.randint(1, 3), counter_reset=True
            )
            db.add(log)
            log_count += 1
    
    # Also add one active breakdown request
    r1 = next((r for r in reactors if r.reactor_code == "R1"), None)
    if r1:
        req_counter = db.query(MaintenanceRequest).count() + 1
        breakdown = MaintenanceRequest(
            request_number=f"REQ-{datetime.now().strftime('%Y%m%d')}-{req_counter:03d}",
            reactor_id=r1.id, equipment_type="REACTOR", request_type="BREAKDOWN",
            priority="HIGH", status="IN_PROGRESS", title="Oil pump leak detected",
            description="Minor leak in hydraulic oil system", requested_by="Operator Venkat",
            assigned_to="Technician Suresh", downtime_hours=Decimal("4"),
            labor_hours=Decimal("4"), labor_cost=Decimal("600"),
            parts_cost=Decimal("1200"), total_cost=Decimal("1800"),
        )
        db.add(breakdown)
        print("  ✓ Created active HIGH breakdown request for R1")
    
    db.flush()
    print(f"  ✓ Created {log_count} MaintenanceLogs for downtime analysis")

def create_sales_flow(db: Session, customers: list, products: dict) -> dict:
    """Create Sale Orders → Dispatches → Invoices."""
    print(f"\n💰 Creating {NUM_SALE_ORDERS} Sale Orders with Dispatches & Invoices...")
    
    so_counter = db.query(SaleOrder).count()
    dc_counter = db.query(SalesDispatch).count()
    inv_counter = db.query(SalesInvoice).count()
    
    oil_product = products.get("OIL")
    created = {"orders": [], "dispatches": [], "invoices": []}
    
    for i in range(NUM_SALE_ORDERS):
        order_date = random_date_in_range(80, 5)
        customer = random.choice(customers)
        qty = Decimal(str(random.randint(500, 2000)))
        
        # November = loss month (low prices)
        if order_date.month == LOSS_MONTH:
            rate = Decimal(str(random.uniform(35, 40)))
        else:
            rate = Decimal(str(random.uniform(44, 48)))
        
        amount = qty * rate
        tax = amount * Decimal("0.18")
        total = amount + tax
        
        so_counter += 1
        so = SaleOrder(
            order_number=f"SO-{order_date.strftime('%Y%m')}-{so_counter:04d}",
            order_date=order_date, customer_id=customer.id, status="DISPATCHED",
            subtotal=amount, tax_amount=tax, total_amount=total,
            expected_delivery_date=order_date + timedelta(days=3), created_by="SalesTeam"
        )
        db.add(so)
        db.flush()
        
        # Add SO item
        so_item = SaleOrderItem(
            sale_order_id=so.id, product_id=oil_product.id,
            description="Pyrolysis Oil", quantity=qty, unit="LITERS", rate=rate,
            dispatched_quantity=qty, pending_quantity=Decimal("0"),
            amount=amount, tax_rate=Decimal("18.0"), tax_amount=tax, total_amount=total
        )
        db.add(so_item)
        db.flush()
        
        # Create Dispatch
        dispatch_date = order_date + timedelta(days=1)
        dc_counter += 1
        dispatch = SalesDispatch(
            dispatch_number=f"DC-{dispatch_date.strftime('%Y%m%d')}-{dc_counter:04d}",
            dispatch_date=dispatch_date, sale_order_id=so.id, customer_id=customer.id,
            status="DELIVERED", truck_number=f"AP{random.randint(10,39)}T{random.randint(1000,9999)}",
            driver_name="Driver", driver_phone="9876500000",
            total_quantity=qty, total_amount=total, shipped_by="Dispatch Team"
        )
        db.add(dispatch)
        db.flush()
        
        # Add Dispatch item
        dc_item = SalesDispatchItem(
            dispatch_id=dispatch.id, sale_order_item_id=so_item.id, product_id=oil_product.id,
            description="Pyrolysis Oil", quantity=qty, unit="LITERS", rate=rate,
            amount=amount, tax_rate=Decimal("18.0"), tax_amount=tax, total_amount=total
        )
        db.add(dc_item)
        db.flush()
        
        # Create Invoice
        inv_counter += 1
        invoice = SalesInvoice(
            invoice_number=f"INV/{order_date.strftime('%y-%y')}/{inv_counter:04d}",
            invoice_date=dispatch_date, dispatch_id=dispatch.id,
            sale_order_id=so.id, customer_id=customer.id,
            seller_name="Tyre Pyrolysis Industries Pvt Ltd", seller_gstin="37XXXXX1234Z5",
            buyer_name=customer.name, is_inter_state=False,
            subtotal=amount, cgst_amount=tax / 2, sgst_amount=tax / 2, total_tax=tax, grand_total=total,
            payment_terms="Net 30", created_by="Accounts"
        )
        db.add(invoice)
        
        created["orders"].append(so)
        created["dispatches"].append(dispatch)
        created["invoices"].append(invoice)
        
    db.flush()
    print(f"  ✓ Created {NUM_SALE_ORDERS} orders, dispatches, and invoices")
    return created

def create_sales_return(db: Session, dispatches: list, invoices: list, customers: list, products: dict):
    """Create 1 Sales Return with RECEIVED status (Pending QC)."""
    print("\n📥 Creating 1 Sales Return (RECEIVED - Pending QC)...")
    
    if not invoices or not dispatches:
        print("  ⚠️ No invoices/dispatches to link return to. Skipping.")
        return None
    
    # Pick a recent dispatch/invoice
    invoice = invoices[-3] if len(invoices) >= 3 else invoices[0]
    dispatch = dispatches[-3] if len(dispatches) >= 3 else dispatches[0]
    customer = customers[0]
    oil_product = products.get("OIL")
    
    return_date = date.today() - timedelta(days=2)
    qty = Decimal("100")
    rate = Decimal("45.00")
    amount = qty * rate
    tax = amount * Decimal("0.18")
    total = amount + tax
    
    sales_return = SalesReturn(
        return_number=f"RMA-{return_date.strftime('%Y%m%d')}-001",
        return_date=return_date, invoice_id=invoice.id, dispatch_id=dispatch.id,
        customer_id=customer.id, status="RECEIVED",  # Pending QC!
        reason="Quality complaint - oil color deviation", reason_category="QUALITY",
        total_quantity=qty, total_amount=total, quarantine_location="QUARANTINE",
        received_at=datetime.now() - timedelta(hours=4), received_by="Operator"
    )
    db.add(sales_return)
    db.flush()
    
    # Add return item
    return_item = SalesReturnItem(
        sales_return_id=sales_return.id, product_id=oil_product.id,
        description="Pyrolysis Oil - Quality Issue", quantity=qty, unit="LITERS", rate=rate,
        amount=amount, tax_rate=Decimal("18.0"), tax_amount=tax, total_amount=total,
        qc_status=None,  # Pending QC!
        qc_notes=None
    )
    db.add(return_item)
    db.flush()
    
    print(f"  ✓ Created Sales Return {sales_return.return_number} - RECEIVED (Pending QC)")
    return sales_return


# ═══════════════════════════════════════════════════════════
# WIPE
# ═══════════════════════════════════════════════════════════

def wipe_production_data(db: Session):
    """Wipe production data (keep base masters)."""
    print("🗑️ Wiping existing production data...")
    tables = [
        SalesReturnItem, SalesReturn, SalesInvoice, SalesDispatchItem, SalesDispatch,
        SaleOrderItem, SaleOrder, ProductionBatch, InventoryLot, GoodsReceiptNote,
        PurchaseOrderItem, PurchaseOrder, MaintenanceLog, MaintenanceRequest,
    ]
    for table in tables:
        try:
            count = db.query(table).delete()
            if count > 0:
                print(f"  ✓ Deleted {count} rows from {table.__tablename__}")
        except Exception as e:
            print(f"  ⚠️ Error deleting {table.__tablename__}: {e}")
    db.commit()
    print("  ✓ Data wipe complete")


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Seed realistic plant data")
    parser.add_argument("--wipe", action="store_true", help="Wipe existing production data first")
    args = parser.parse_args()
    
    print("=" * 60)
    print("🌱 Tyre Pyrolysis ERP - Comprehensive Data Seed (ORM)")
    print("=" * 60)
    print(f"📅 Generating {DAYS_OF_HISTORY} days of history")
    print(f"📊 Target: {NUM_BATCHES_HISTORICAL} historical + {NUM_GRNS_TODAY} today's batches")
    print(f"📋 POs: {NUM_OPEN_POS} OPEN | Sales: {NUM_SALE_ORDERS} orders")
    print()
    
    db = SessionLocal()
    
    try:
        if args.wipe:
            wipe_production_data(db)
            print()
        
        # Setup masters
        vendors = setup_vendors(db)
        material = setup_raw_material(db)
        reactors = setup_reactors(db)
        tank = setup_tank(db)
        customers = setup_customers(db)
        products = setup_products(db)
        schedules = setup_maintenance_schedules(db, reactors)
        db.commit()
        
        # Create transactional data
        create_purchase_orders(db, vendors, material)
        batch_data = create_production_data(db, vendors, material, reactors, tank)
        create_maintenance_logs(db, reactors, schedules)
        sales_data = create_sales_flow(db, customers, products)
        create_sales_return(db, sales_data["dispatches"], sales_data["invoices"], customers, products)
        db.commit()
        
        # Summary
        total_cost = sum(b["net_payable"] for b in batch_data)
        total_oil = sum(b["oil_kg"] for b in batch_data)
        
        print()
        print("=" * 60)
        print("✅ SEED COMPLETE!")
        print("=" * 60)
        print()
        print("📊 Summary:")
        print(f"  • Vendors: 3 (get_or_create by name)")
        print(f"  • Purchase Orders: {NUM_OPEN_POS} OPEN")
        print(f"  • GRNs: {len(batch_data)} (including {NUM_GRNS_TODAY} today)")
        print(f"  • Batches: {len(batch_data)} (3 active, rest completed)")
        print(f"  • Sale Orders: {NUM_SALE_ORDERS}")
        print(f"  • Sales Returns: 1 (RECEIVED - Pending QC)")
        print(f"  • Total Raw Material Cost: ₹{total_cost:,.0f}")
        print(f"  • Total Oil Produced: {total_oil:,.0f} kg")
        print()
        print("🏭 Reactor States:")
        print(f"  • R1: Ready | R2: ⚠️ WARNING | R3: 🔒 LOCKED")
        print()
        print("🔗 Test at: http://localhost:5174")
        print()
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
