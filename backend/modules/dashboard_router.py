"""
Dashboard Router - Central Command Center APIs.

Provides aggregated stats, alerts, and activity for the main dashboard.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from datetime import datetime, date, timedelta
from typing import Optional

from database import get_db
from auth.dependencies import get_current_user_required
from models.user import User

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


# ═══════════════════════════════════════════════════════════
# SUMMARY ENDPOINT - All KPI Stats in One Call
# ═══════════════════════════════════════════════════════════

@router.get("/summary")
def get_dashboard_summary(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_required)
):
    """
    Aggregated dashboard stats grouped by business flow:
    - INPUT: Procurement metrics (vendors, POs, GRNs, material)
    - PROCESS: Production metrics (batches, reactors, tanks)
    - OUTPUT: Sales metrics (orders, dispatches, revenue, margin)
    """
    from models.vendor import Vendor
    from models.grn import GoodsReceiptNote
    from models.purchase_order import PurchaseOrder
    from models.production_batch import ProductionBatch
    from models.reactor import Reactor
    from models.storage_tank import StorageTank
    from models.dispatch import SalesInvoice, SalesDispatch
    from models.customer import Customer
    from models.inventory_lot import InventoryLot
    
    today = date.today()
    month_start = date(today.year, today.month, 1)
    
    # ─── INPUT ZONE (Procurement) ───
    active_vendors = db.query(func.count(Vendor.id)).filter(Vendor.is_active == True).scalar() or 0
    
    open_pos = db.query(func.count(PurchaseOrder.id)).filter(
        PurchaseOrder.status.in_(["DRAFT", "CONFIRMED", "PARTIALLY_RECEIVED"])
    ).scalar() or 0
    
    today_grns = db.query(func.count(GoodsReceiptNote.id)).filter(
        GoodsReceiptNote.receipt_date == today
    ).scalar() or 0
    
    today_material = db.query(func.sum(GoodsReceiptNote.payable_weight_kg)).filter(
        GoodsReceiptNote.receipt_date == today
    ).scalar() or 0
    
    today_deductions = db.query(func.sum(GoodsReceiptNote.total_deduction_kg)).filter(
        GoodsReceiptNote.receipt_date == today
    ).scalar() or 0
    
    # ─── PROCESS ZONE (Production) ───
    active_batches = db.query(func.count(ProductionBatch.id)).filter(
        ProductionBatch.status.in_(["LOADING", "IN_PROGRESS", "COOLING", "PENDING_QC"])
    ).scalar() or 0
    
    # Reactor statuses
    reactors = db.query(Reactor).filter(Reactor.is_active == True).all()
    reactor_summary = []
    for r in reactors:
        reactor_summary.append({
            "id": r.id,
            "code": r.reactor_code,
            "name": r.name,
            "status": r.status,
            "batches_since_clean": r.batches_since_last_cleaning,
            "max_batches": r.maintenance_frequency
        })
    
    # Tank levels
    tank_result = db.query(
        func.sum(StorageTank.current_level_liters).label("total_liters"),
        func.sum(StorageTank.capacity_liters).label("total_capacity")
    ).filter(StorageTank.is_active == True).first()
    
    oil_in_tanks = float(tank_result.total_liters or 0)
    tank_capacity = float(tank_result.total_capacity or 1)
    tank_fill_pct = round((oil_in_tanks / tank_capacity) * 100, 1) if tank_capacity > 0 else 0
    
    # Raw material stock
    raw_material_stock = db.query(func.sum(InventoryLot.current_qty_kg)).filter(
        InventoryLot.is_exhausted == False,
        InventoryLot.current_qty_kg > 0
    ).scalar() or 0
    
    # Month production outputs
    month_outputs = db.query(
        func.sum(ProductionBatch.oil_liters_to_tank).label("oil"),
        func.sum(ProductionBatch.carbon_output_kg).label("carbon"),
        func.sum(ProductionBatch.steel_output_kg).label("steel")
    ).filter(
        ProductionBatch.status == "COMPLETED",
        ProductionBatch.end_datetime >= month_start
    ).first()
    
    # ─── OUTPUT ZONE (Sales) ───
    active_customers = db.query(func.count(Customer.id)).filter(Customer.is_active == True).scalar() or 0
    
    pending_dispatches = db.query(func.count(SalesDispatch.id)).filter(
        SalesDispatch.status.in_(["PENDING", "READY"])
    ).scalar() or 0
    
    # Financial Year start (April 1)
    fy_start = date(today.year if today.month >= 4 else today.year - 1, 4, 1)
    
    # Trailing 30 days
    thirty_days_ago = today - timedelta(days=30)
    
    # YTD Revenue (from FY start)
    ytd_revenue = db.query(func.sum(SalesInvoice.subtotal)).filter(
        SalesInvoice.invoice_date >= fy_start,
        SalesInvoice.invoice_date <= today
    ).scalar() or 0
    
    # Trailing 30-day revenue
    trailing_revenue = db.query(func.sum(SalesInvoice.subtotal)).filter(
        SalesInvoice.invoice_date >= thirty_days_ago,
        SalesInvoice.invoice_date <= today
    ).scalar() or 0
    
    # YTD Costs (from FY start)
    ytd_costs = db.query(func.sum(GoodsReceiptNote.net_payable_amount)).filter(
        GoodsReceiptNote.receipt_date >= fy_start,
        GoodsReceiptNote.receipt_date <= today
    ).scalar() or 0
    
    # Margin calculation (YTD based)
    revenue = float(ytd_revenue or 0)
    costs = float(ytd_costs or 0)
    margin_pct = round(((revenue - costs) / revenue) * 100, 1) if revenue > 0 else 0
    
    return {
        "as_of": datetime.now().isoformat(),
        "input": {
            "active_vendors": active_vendors,
            "open_purchase_orders": open_pos,
            "todays_grns": today_grns,
            "todays_material_kg": round(float(today_material), 2),
            "todays_deductions_kg": round(float(today_deductions), 2)
        },
        "process": {
            "active_batches": active_batches,
            "reactors": reactor_summary,
            "oil_in_tanks_liters": round(oil_in_tanks, 2),
            "tank_fill_percent": tank_fill_pct,
            "raw_material_stock_kg": round(float(raw_material_stock), 2),
            "month_oil_liters": round(float(month_outputs.oil or 0), 2),
            "month_carbon_kg": round(float(month_outputs.carbon or 0), 2),
            "month_steel_kg": round(float(month_outputs.steel or 0), 2)
        },
        "output": {
            "active_customers": active_customers,
            "pending_dispatches": pending_dispatches,
            "ytd_revenue": round(revenue, 2),
            "trailing_30d_revenue": round(float(trailing_revenue or 0), 2),
            "ytd_costs": round(costs, 2),
            "profit_margin_pct": margin_pct,
            "fy_start": str(fy_start)
        }
    }


# ═══════════════════════════════════════════════════════════
# ALERTS ENDPOINT - Actionable Notifications
# ═══════════════════════════════════════════════════════════

@router.get("/alerts")
def get_dashboard_alerts(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_required)
):
    """
    Actionable alerts grouped by severity.
    Each alert has a type, message, and navigation link.
    """
    from models.reactor import Reactor
    from models.purchase_order import PurchaseOrder
    from models.maintenance import MaintenanceRequest, MaintenanceSchedule
    from models.dispatch import SalesDispatch
    from models.inventory_lot import InventoryLot
    from models.storage_tank import StorageTank
    
    alerts = []
    today = date.today()
    
    # 1. CRITICAL: Reactor cleaning required (interlock)
    locked_reactors = db.query(Reactor).filter(
        Reactor.is_active == True,
        Reactor.status == "BLOCKED"
    ).all()
    for r in locked_reactors:
        alerts.append({
            "severity": "critical",
            "type": "reactor_cleaning",
            "icon": "🔒",
            "message": f"{r.reactor_code} needs cleaning ({r.batches_since_last_cleaning}/{r.maintenance_frequency} batches)",
            "link": "/maintenance",
            "entity_id": r.id
        })
    
    # 2. WARNING: Reactor approaching limit
    warning_reactors = db.query(Reactor).filter(
        Reactor.is_active == True,
        Reactor.status == "WARNING"
    ).all()
    for r in warning_reactors:
        alerts.append({
            "severity": "warning",
            "type": "reactor_warning",
            "icon": "⚠️",
            "message": f"{r.reactor_code} approaching cleaning limit ({r.batches_since_last_cleaning}/{r.maintenance_frequency})",
            "link": "/maintenance",
            "entity_id": r.id
        })
    
    # 3. Pending POs (confirmed but not delivered)
    pending_pos = db.query(func.count(PurchaseOrder.id)).filter(
        PurchaseOrder.status == "CONFIRMED"
    ).scalar() or 0
    if pending_pos > 0:
        alerts.append({
            "severity": "info",
            "type": "pending_po",
            "icon": "📦",
            "message": f"{pending_pos} PO{'s' if pending_pos > 1 else ''} pending delivery",
            "link": "/purchase-orders?status=CONFIRMED",
            "count": pending_pos
        })
    
    # 4. Open maintenance requests
    open_maintenance = db.query(func.count(MaintenanceRequest.id)).filter(
        MaintenanceRequest.status.in_(["OPEN", "IN_PROGRESS"])
    ).scalar() or 0
    if open_maintenance > 0:
        alerts.append({
            "severity": "warning",
            "type": "open_maintenance",
            "icon": "🔧",
            "message": f"{open_maintenance} maintenance request{'s' if open_maintenance > 1 else ''} open",
            "link": "/maintenance",
            "count": open_maintenance
        })
    
    # 5. Pending dispatches
    pending_dispatches = db.query(func.count(SalesDispatch.id)).filter(
        SalesDispatch.status.in_(["PENDING", "READY"])
    ).scalar() or 0
    if pending_dispatches > 0:
        alerts.append({
            "severity": "info",
            "type": "pending_dispatch",
            "icon": "🚚",
            "message": f"{pending_dispatches} dispatch{'es' if pending_dispatches > 1 else ''} pending",
            "link": "/sales?tab=dispatches",
            "count": pending_dispatches
        })
    
    # 6. Low raw material stock (< 500 kg)
    raw_stock = db.query(func.sum(InventoryLot.current_qty_kg)).filter(
        InventoryLot.is_exhausted == False
    ).scalar() or 0
    if float(raw_stock) < 500:
        alerts.append({
            "severity": "warning",
            "type": "low_stock",
            "icon": "📉",
            "message": f"Low raw material stock: {round(float(raw_stock))} kg",
            "link": "/purchase-orders",
            "count": round(float(raw_stock))
        })
    
    # 7. Tank nearly full (> 90%)
    tanks = db.query(StorageTank).filter(StorageTank.is_active == True).all()
    for t in tanks:
        fill_pct = (float(t.current_level_liters or 0) / float(t.capacity_liters or 1)) * 100
        if fill_pct > 90:
            alerts.append({
                "severity": "warning",
                "type": "tank_near_full",
                "icon": "🛢️",
                "message": f"{t.tank_code} is {round(fill_pct)}% full - schedule dispatch",
                "link": "/sales?tab=dispatches",
                "entity_id": t.id
            })
    
    # Sort by severity (critical > warning > info)
    severity_order = {"critical": 0, "warning": 1, "info": 2}
    alerts.sort(key=lambda x: severity_order.get(x["severity"], 3))
    
    return {
        "count": len(alerts),
        "alerts": alerts
    }


# ═══════════════════════════════════════════════════════════
# ACTIVITY ENDPOINT - Recent Transactions Feed
# ═══════════════════════════════════════════════════════════

@router.get("/activity")
def get_dashboard_activity(
    limit: int = 15,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_required)
):
    """
    Recent activity feed showing the last N transactions across all modules.
    """
    from models.grn import GoodsReceiptNote
    from models.production_batch import ProductionBatch
    from models.dispatch import SalesInvoice, SalesDispatch
    from models.purchase_order import PurchaseOrder
    from models.maintenance import MaintenanceRequest
    
    activities = []
    
    # Recent GRNs
    grns = db.query(GoodsReceiptNote).order_by(desc(GoodsReceiptNote.created_at)).limit(5).all()
    for g in grns:
        activities.append({
            "type": "grn",
            "icon": "📥",
            "message": f"GRN {g.grn_number} - {round(float(g.payable_weight_kg or 0))} kg received",
            "timestamp": g.created_at.isoformat() if g.created_at else None,
            "link": f"/grn/{g.id}"
        })
    
    # Recent Completed Batches
    batches = db.query(ProductionBatch).filter(
        ProductionBatch.status == "COMPLETED"
    ).order_by(desc(ProductionBatch.end_datetime)).limit(5).all()
    for b in batches:
        oil_yield = float(b.oil_yield_pct or 0)
        activities.append({
            "type": "batch",
            "icon": "🔥",
            "message": f"Batch {b.batch_number} completed - {round(oil_yield, 1)}% oil yield",
            "timestamp": b.end_datetime.isoformat() if b.end_datetime else None,
            "link": f"/production?batch={b.id}"
        })
    
    # Recent Invoices
    invoices = db.query(SalesInvoice).order_by(desc(SalesInvoice.created_at)).limit(5).all()
    for inv in invoices:
        activities.append({
            "type": "invoice",
            "icon": "📄",
            "message": f"Invoice {inv.invoice_number} - ₹{round(float(inv.grand_total or 0)):,}",
            "timestamp": inv.created_at.isoformat() if inv.created_at else None,
            "link": f"/sales?invoice={inv.id}"
        })
    
    # Recent Dispatches
    dispatches = db.query(SalesDispatch).filter(
        SalesDispatch.status == "DISPATCHED"
    ).order_by(desc(SalesDispatch.dispatch_date)).limit(5).all()
    for d in dispatches:
        activities.append({
            "type": "dispatch",
            "icon": "🚚",
            "message": f"Dispatch {d.dispatch_number} sent",
            "timestamp": d.created_at.isoformat() if d.created_at else None,
            "link": f"/sales?dispatch={d.id}"
        })
    
    # Recent POs created
    pos = db.query(PurchaseOrder).order_by(desc(PurchaseOrder.created_at)).limit(3).all()
    for po in pos:
        activities.append({
            "type": "po",
            "icon": "📝",
            "message": f"PO {po.po_number} created - ₹{round(float(po.total_amount or 0)):,}",
            "timestamp": po.created_at.isoformat() if po.created_at else None,
            "link": f"/purchase-orders?po={po.id}"
        })
    
    # Recent Maintenance
    maintenance = db.query(MaintenanceRequest).order_by(desc(MaintenanceRequest.created_at)).limit(3).all()
    for m in maintenance:
        activities.append({
            "type": "maintenance",
            "icon": "🔧",
            "message": f"Maintenance: {m.title[:40]}{'...' if len(m.title) > 40 else ''}",
            "timestamp": m.created_at.isoformat() if m.created_at else None,
            "link": f"/maintenance?request={m.id}"
        })
    
    # Sort by timestamp (most recent first)
    activities.sort(key=lambda x: x["timestamp"] or "", reverse=True)
    
    return {
        "count": len(activities[:limit]),
        "activities": activities[:limit]
    }
