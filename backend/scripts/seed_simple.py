"""
Simple Database Seed Script - Direct SQL Inserts.

Generates test data for verifying reports.
Usage: python scripts/seed_simple.py
"""
import sqlite3
import random
from datetime import datetime, timedelta, date
import os

# Configuration
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "erp.db")
DAYS_BACK = 90
NUM_BATCHES = 55

print("=" * 60)
print("🌱 Tyre Pyrolysis ERP - Simple Data Seed")
print("=" * 60)
print(f"📅 Database: {DB_PATH}")
print()

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# ═══════════════════════════════════════════════════════════
# VENDORS - Character profiles
# ═══════════════════════════════════════════════════════════
print("📦 Seeding vendors...")

vendors = [
    ("V-PREM-001", "ShreeSai Rubber Industries", "Hyderabad", 1, 30),  # Premium
    ("V-BUDG-001", "Bharat Scrap Traders", "Vijayawada", 1, 15),        # Budget
    ("V-RISK-001", "Quick Tyres & Rubber", "Guntur", 0, 15),            # Risky
]

vendor_ids = {}
for code, name, city, epr, credit_days in vendors:
    cursor.execute("SELECT id FROM vendors WHERE vendor_code = ?", (code,))
    row = cursor.fetchone()
    if row:
        vendor_ids[code] = row[0]
        print(f"  ✓ {name} (existing)")
    else:
        cursor.execute("""
            INSERT INTO vendors (vendor_code, name, vendor_type, city, state, country, 
                                 gst_number, gst_vendor_type, is_epr_compliant, credit_days, is_active)
            VALUES (?, ?, 'SUPPLIER', ?, 'Andhra Pradesh', 'India', 
                    '37' || substr(abs(random()), 1, 10) || '1Z5', 'REGISTERED', ?, ?, 1)
        """, (code, name, city, epr, credit_days))
        vendor_ids[code] = cursor.lastrowid
        print(f"  ✓ {name} (created)")

conn.commit()

# ═══════════════════════════════════════════════════════════
# CUSTOMERS
# ═══════════════════════════════════════════════════════════
print("👥 Seeding customers...")

customers = [
    ("CUST-001", "Mahalakshmi Oils Pvt Ltd", "Guntur"),
    ("CUST-002", "Andhra Industries", "Vijayawada"),
    ("CUST-003", "Krishna Chemicals", "Hyderabad"),
]

customer_ids = []
for code, name, city in customers:
    cursor.execute("SELECT id FROM customers WHERE customer_code = ?", (code,))
    row = cursor.fetchone()
    if row:
        customer_ids.append(row[0])
    else:
        cursor.execute("""
            INSERT INTO customers (customer_code, name, customer_type, city, state, 
                                   gst_number, payment_terms_days, credit_limit, is_active)
            VALUES (?, ?, 'ALL', ?, 'Andhra Pradesh',
                    '37' || substr(abs(random()), 1, 10) || '1Z5', 30, 500000, 1)
        """, (code, name, city))
        customer_ids.append(cursor.lastrowid)
        print(f"  ✓ {name}")

conn.commit()

# ═══════════════════════════════════════════════════════════
# PRODUCTS
# ═══════════════════════════════════════════════════════════
print("📦 Seeding products...")

products = [
    ("PRD-OIL-001", "Pyrolysis Oil", "OIL", "LITERS", 45.00),
    ("PRD-CBK-001", "Carbon Black", "CARBON", "KG", 18.00),
    ("PRD-STL-001", "Steel Scrap", "STEEL", "KG", 25.00),
]

product_ids = {}
for code, name, ptype, unit, rate in products:
    cursor.execute("SELECT id FROM products WHERE product_code = ?", (code,))
    row = cursor.fetchone()
    if row:
        product_ids[ptype] = row[0]
    else:
        cursor.execute("""
            INSERT INTO products (product_code, name, product_type, unit, default_rate, gst_rate, is_active)
            VALUES (?, ?, ?, ?, ?, 18.0, 1)
        """, (code, name, ptype, unit, rate))
        product_ids[ptype] = cursor.lastrowid
        print(f"  ✓ {name}")

conn.commit()

# ═══════════════════════════════════════════════════════════
# REACTORS - Set up maintenance states
# ═══════════════════════════════════════════════════════════
print("🏭 Setting reactor maintenance states...")

# R2 = 2/3 batches (warning)
cursor.execute("""
    UPDATE reactors SET batches_since_last_cleaning = 2, maintenance_frequency = 3, status = 'IDLE'
    WHERE reactor_code = 'R2'
""")
# R3 = 3/3 batches (locked)
cursor.execute("""
    UPDATE reactors SET batches_since_last_cleaning = 3, maintenance_frequency = 3, status = 'MAINTENANCE'
    WHERE reactor_code = 'R3'
""")
conn.commit()
print("  ✓ R2: 2/3 batches (WARNING)")
print("  ✓ R3: 3/3 batches (LOCKED)")

# ═══════════════════════════════════════════════════════════
# GRNs AND BATCHES - Realistic production
# ═══════════════════════════════════════════════════════════
print(f"\n🔄 Seeding {NUM_BATCHES} production batches...")

# Vendor profiles: (oil_yield_min, oil_yield_max, deduction_min, deduction_max, rate_min, rate_max)
vendor_profiles = {
    "V-PREM-001": (43, 47, 1, 3, 13, 15),    # Premium: High yield, low deduction
    "V-BUDG-001": (38, 42, 5, 10, 9, 11),     # Budget: Average yield, high deduction
    "V-RISK-001": (32, 38, 8, 15, 10, 14),    # Risky: Low yield, variable
}

# Get reactor IDs
cursor.execute("SELECT id FROM reactors WHERE reactor_code = 'R1'")
r1_id = cursor.fetchone()[0]
cursor.execute("SELECT id FROM reactors WHERE reactor_code = 'R2'")
r2_id = cursor.fetchone()[0]

vendor_codes = list(vendor_ids.keys())
total_revenue = 0
total_cost = 0

for i in range(NUM_BATCHES):
    # Select vendor (40% Premium, 40% Budget, 20% Risky)
    if i < 22:
        vendor_code = "V-PREM-001"
    elif i < 44:
        vendor_code = "V-BUDG-001"
    else:
        vendor_code = "V-RISK-001"
    
    vendor_id = vendor_ids[vendor_code]
    profile = vendor_profiles[vendor_code]
    
    # Random date in past
    days_ago = random.randint(1, DAYS_BACK)
    batch_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    batch_time = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
    
    # Weights
    gross_weight = random.uniform(500, 650)
    tare_weight = random.uniform(50, 80)
    net_weight = gross_weight - tare_weight
    deduction_pct = random.uniform(profile[2], profile[3])
    deduction_kg = net_weight * (deduction_pct / 100)
    payable_weight = net_weight - deduction_kg
    
    # Pricing
    rate = random.uniform(profile[4], profile[5])
    gross_amount = payable_weight * rate
    gst = gross_amount * 0.05
    net_payable = gross_amount + gst
    total_cost += net_payable
    
    # Create GRN
    grn_number = f"GRN-{batch_date.replace('-', '')[:6]}-{i+1:04d}"
    cursor.execute("""
        INSERT INTO goods_receipt_notes (grn_number, vendor_id, vehicle_number, 
            gross_weight_kg, tare_weight_kg, net_weight_kg, total_deduction_kg, payable_weight_kg,
            rate_per_kg, gross_amount, cgst_amount, sgst_amount, net_payable_amount,
            receipt_date, receipt_datetime, quality_grade, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'APPROVED', ?)
    """, (grn_number, vendor_id, f"AP{random.randint(10,39)}T{random.randint(1000,9999)}",
          gross_weight, tare_weight, net_weight, deduction_kg, payable_weight,
          rate, gross_amount, gst/2, gst/2, net_payable, batch_date, batch_time,
          'A' if vendor_code == "V-PREM-001" else ('B' if vendor_code == "V-BUDG-001" else 'C'),
          batch_time))
    grn_id = cursor.lastrowid
    
    # Create Inventory Lot
    lot_id_str = f"LOT-{batch_date.replace('-', '')}-{i+1:04d}"
    cursor.execute("""
        INSERT INTO inventory_lots (lot_id, grn_id, vendor_id, receipt_date, vehicle_number,
            received_qty_kg, current_qty_kg, consumed_qty_kg, rate_per_kg, total_cost, 
            is_exhausted, is_active, created_at)
        VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?, 1, 1, ?)
    """, (lot_id_str, grn_id, vendor_id, batch_date, f"AP{random.randint(10,39)}T{random.randint(1000,9999)}",
          net_weight, net_weight, rate, net_weight * rate, batch_time))
    lot_id = cursor.lastrowid
    
    # Yields - mass balance
    oil_yield = random.uniform(profile[0], profile[1])
    carbon_yield = random.uniform(30, 35)
    steel_yield = random.uniform(10, 15)
    syngas_loss = 100 - oil_yield - carbon_yield - steel_yield
    
    oil_kg = net_weight * (oil_yield / 100)
    carbon_kg = net_weight * (carbon_yield / 100)
    steel_kg = net_weight * (steel_yield / 100)
    syngas_kg = net_weight * (syngas_loss / 100)
    
    power_kwh = (net_weight / 100) * random.uniform(80, 120)
    
    # Create Batch
    batch_number = f"BATCH-{batch_date.replace('-', '')}-{i+1:03d}"
    reactor_id = random.choice([r1_id, r2_id])
    
    cursor.execute("""
        INSERT INTO production_batches (batch_number, reactor_id, input_lot_id, status, 
            input_weight_kg, batch_date, start_datetime, end_datetime,
            electricity_used_kwh, oil_output_kg, carbon_output_kg, steel_output_kg,
            syn_gas_loss_kg, oil_yield_pct, carbon_yield_pct, steel_yield_pct, loss_pct,
            created_at)
        VALUES (?, ?, ?, 'COMPLETED', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (batch_number, reactor_id, lot_id, net_weight, batch_date, batch_time, batch_time,
          power_kwh, oil_kg, carbon_kg, steel_kg, syngas_kg, 
          oil_yield, carbon_yield, steel_yield, syngas_loss, batch_time))
    
    if (i + 1) % 10 == 0:
        print(f"  ✓ Created {i + 1}/{NUM_BATCHES} batches")

conn.commit()
print(f"  ✓ All {NUM_BATCHES} batches created")

# ═══════════════════════════════════════════════════════════
# SALES INVOICES
# ═══════════════════════════════════════════════════════════
print("\n💰 Seeding sales invoices...")

# Create invoices - one per 5 batches
oil_product_id = product_ids.get("OIL", 1)

for i in range(12):  # 12 invoices over 3 months
    days_ago = random.randint(1, 90)
    inv_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    inv_time = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
    
    customer_id = random.choice(customer_ids)
    
    # Qty: 1000-3000 liters per invoice
    qty = random.uniform(1000, 3000)
    
    # Price: Make November a loss month
    inv_month = (datetime.now() - timedelta(days=days_ago)).month
    if inv_month == 11:  # November - loss
        rate = random.uniform(35, 40)
    else:
        rate = random.uniform(44, 48)
    
    subtotal = qty * rate
    gst = subtotal * 0.18
    total = subtotal + gst
    total_revenue += subtotal
    
    inv_number = f"INV-{inv_date.replace('-', '')[:6]}-{i+1:04d}"
    
    # Create dispatch first
    cursor.execute("""
        INSERT INTO sales_dispatches (challan_number, customer_id, dispatch_date, 
            vehicle_number, driver_name, status, created_at)
        VALUES (?, ?, ?, ?, 'Driver', 'COMPLETED', ?)
    """, (f"DC-{inv_date.replace('-', '')}-{i+1:04d}", customer_id, inv_date,
          f"AP{random.randint(10,39)}T{random.randint(1000,9999)}", inv_time))
    dispatch_id = cursor.lastrowid
    
    # Create invoice
    cursor.execute("""
        INSERT INTO sales_invoices (invoice_number, dispatch_id, customer_id, invoice_date,
            subtotal, cgst_amount, sgst_amount, total_amount, payment_status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (inv_number, dispatch_id, customer_id, inv_date, 
          subtotal, gst/2, gst/2, total, 
          'PAID' if random.random() > 0.3 else 'PENDING', inv_time))

conn.commit()
print(f"  ✓ Created 12 invoices")
print(f"  ✓ Total Revenue (taxable): ₹{total_revenue:,.0f}")
print(f"  ✓ Total Material Cost: ₹{total_cost:,.0f}")

# ═══════════════════════════════════════════════════════════
# MAINTENANCE LOGS
# ═══════════════════════════════════════════════════════════
print("\n🔧 Seeding maintenance logs...")

cursor.execute("SELECT id FROM reactors WHERE is_active = 1")
reactor_ids = [row[0] for row in cursor.fetchall()]

for reactor_id in reactor_ids:
    for j in range(random.randint(2, 5)):
        days_ago = random.randint(5, 80)
        log_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
        downtime = random.uniform(1, 6)
        
        cursor.execute("""
            INSERT INTO maintenance_logs (reactor_id, task_name, performed_by,
                started_at, completed_at, downtime_hours, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'Routine maintenance', ?)
        """, (reactor_id, random.choice(["Cleaning", "Inspection", "Seal Check"]),
              random.choice(["Rajesh", "Suresh", "Venkat"]), log_date, log_date, downtime, log_date))

conn.commit()
print("  ✓ Created maintenance logs for all reactors")

# ═══════════════════════════════════════════════════════════
# DONE
# ═══════════════════════════════════════════════════════════
conn.close()

print()
print("=" * 60)
print("✅ SEED COMPLETE!")
print("=" * 60)
print()
print("📊 Summary:")
print(f"  • Vendors: 3 (Premium, Budget, Risky)")
print(f"  • Batches: {NUM_BATCHES}")
print(f"  • Sales Invoices: 12")
print(f"  • Reactor R2: 2/3 batches (WARNING)")
print(f"  • Reactor R3: 3/3 batches (LOCKED)")
print()
print("🔗 View reports at: http://localhost:5174/reports")
print()
