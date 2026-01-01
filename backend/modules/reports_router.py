"""
Reports Router - Business Intelligence Endpoints.

Time filters: 7d, this_month, last_month, ytd, custom
Role protection: MANAGER+ for most, ADMIN ONLY for profitability
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, case
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional
import csv
import io

from database import get_db
from auth.dependencies import require_role, require_admin, require_manager_or_above, get_current_user
from models.user import User, UserRole
from models.system_settings import SystemSetting

router = APIRouter(prefix="/reports", tags=["Reports"])


# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════

def get_date_range(period: str, start_date: str = None, end_date: str = None):
    """
    Get date range based on period filter.
    
    Periods: 7d, this_month, last_month, ytd, custom
    """
    today = date.today()
    
    if period == "7d":
        return today - timedelta(days=7), today
    elif period == "this_month":
        return date(today.year, today.month, 1), today
    elif period == "last_month":
        first_of_this = date(today.year, today.month, 1)
        last_month_end = first_of_this - timedelta(days=1)
        last_month_start = date(last_month_end.year, last_month_end.month, 1)
        return last_month_start, last_month_end
    elif period == "ytd":
        return date(today.year, 1, 1), today
    elif period == "custom" and start_date and end_date:
        return datetime.strptime(start_date, "%Y-%m-%d").date(), datetime.strptime(end_date, "%Y-%m-%d").date()
    else:
        # Default to this month
        return date(today.year, today.month, 1), today


def get_setting(db: Session, key: str, default=None):
    """Get a system setting value with fallback."""
    setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if setting:
        return setting.typed_value
    return default


def generate_csv(data: list, columns: list) -> StreamingResponse:
    """Generate CSV file from data."""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns)
    writer.writeheader()
    for row in data:
        writer.writerow({k: row.get(k, '') for k in columns})
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
    )


# ═══════════════════════════════════════════════════════════
# SETTINGS API (Admin Only)
# ═══════════════════════════════════════════════════════════

@router.get("/settings")
def get_system_settings(db: Session = Depends(get_db), admin: User = Depends(require_admin())):
    """Get all system settings (Admin only)."""
    settings = db.query(SystemSetting).order_by(SystemSetting.category, SystemSetting.key).all()
    return [{
        "id": s.id,
        "key": s.key,
        "value": s.value,
        "typed_value": s.typed_value,
        "value_type": s.value_type,
        "description": s.description,
        "category": s.category
    } for s in settings]


@router.put("/settings/{key}")
def update_system_setting(
    key: str,
    value: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin())
):
    """Update a system setting (Admin only)."""
    setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if not setting:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")
    
    setting.value = value
    setting.updated_by = admin.username
    db.commit()
    
    return {"message": f"Setting '{key}' updated to '{value}'"}


# ═══════════════════════════════════════════════════════════
# REPORT 1: VENDOR YIELD ANALYSIS
# ═══════════════════════════════════════════════════════════

@router.get("/vendor-yield")
def get_vendor_yield_report(
    period: str = Query("this_month", regex="^(7d|this_month|last_month|ytd|custom)$"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    export_csv: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(require_manager_or_above())
):
    """
    Vendor ranking by average yield percentage.
    Helps identify best quality scrap suppliers.
    """
    from models.production_batch import ProductionBatch
    from models.inventory_lot import InventoryLot
    from models.grn import GoodsReceiptNote
    from models.vendor import Vendor
    
    date_start, date_end = get_date_range(period, start_date, end_date)
    
    # Query: Batches → Lots → GRN → Vendor
    results = db.query(
        Vendor.id.label("vendor_id"),
        Vendor.name.label("vendor_name"),
        func.count(ProductionBatch.id).label("batch_count"),
        func.avg(ProductionBatch.oil_yield_pct).label("avg_oil_yield"),
        func.avg(ProductionBatch.carbon_yield_pct).label("avg_carbon_yield"),
        func.avg(ProductionBatch.steel_yield_pct).label("avg_steel_yield"),
        func.sum(ProductionBatch.input_weight_kg).label("total_input_kg")
    ).join(
        InventoryLot, ProductionBatch.input_lot_id == InventoryLot.id
    ).join(
        GoodsReceiptNote, InventoryLot.grn_id == GoodsReceiptNote.id
    ).join(
        Vendor, GoodsReceiptNote.vendor_id == Vendor.id
    ).filter(
        ProductionBatch.status == "COMPLETED",
        ProductionBatch.end_datetime >= date_start,
        ProductionBatch.end_datetime <= date_end
    ).group_by(
        Vendor.id
    ).order_by(
        desc("avg_oil_yield")
    ).all()
    
    # Format results with ranking
    data = []
    for i, r in enumerate(results, 1):
        data.append({
            "rank": i,
            "vendor_id": r.vendor_id,
            "vendor_name": r.vendor_name,
            "batch_count": r.batch_count,
            "total_input_kg": float(r.total_input_kg or 0),
            "avg_oil_yield": round(float(r.avg_oil_yield or 0), 2),
            "avg_carbon_yield": round(float(r.avg_carbon_yield or 0), 2),
            "avg_steel_yield": round(float(r.avg_steel_yield or 0), 2)
        })
    
    if export_csv:
        return generate_csv(data, ["rank", "vendor_name", "batch_count", "total_input_kg", 
                                   "avg_oil_yield", "avg_carbon_yield", "avg_steel_yield"])
    
    return {
        "period": period,
        "date_range": {"start": str(date_start), "end": str(date_end)},
        "target_oil_yield": get_setting(db, "target_oil_yield", 42),
        "vendors": data
    }


# ═══════════════════════════════════════════════════════════
# REPORT 2: INVENTORY VALUATION
# ═══════════════════════════════════════════════════════════

@router.get("/inventory-valuation")
def get_inventory_valuation(
    db: Session = Depends(get_db),
    user: User = Depends(require_manager_or_above())
):
    """
    Current inventory valuation by category.
    Raw materials at purchase price, finished goods at selling price.
    """
    from models.inventory_lot import InventoryLot
    from models.storage_tank import StorageTank
    
    # Raw Materials (Input lots with stock)
    # Simplified: Group all raw material lots together
    raw_result = db.query(
        func.sum(InventoryLot.current_qty_kg).label("total_qty"),
        func.sum(InventoryLot.current_qty_kg * InventoryLot.rate_per_kg).label("total_value")
    ).filter(
        InventoryLot.current_qty_kg > 0,
        InventoryLot.is_exhausted == False
    ).first()
    
    raw_qty = float(raw_result.total_qty or 0)
    raw_total = float(raw_result.total_value or 0)
    
    raw_data = []
    if raw_qty > 0:
        raw_data.append({
            "type": "Scrap Tyres",
            "qty_kg": raw_qty,
            "value": raw_total
        })
    
    # Finished Goods (Tank levels) 
    # Estimate oil price at ₹45/litre for valuation
    OIL_PRICE_PER_LITRE = 45.0
    
    tanks = db.query(
        StorageTank.tank_type,
        func.sum(StorageTank.current_level_liters).label("qty")
    ).filter(
        StorageTank.is_active == True
    ).group_by(
        StorageTank.tank_type
    ).all()
    
    finished_data = []
    finished_total = 0
    for t in tanks:
        qty = float(t.qty or 0)
        val = qty * OIL_PRICE_PER_LITRE  # Estimate value
        finished_data.append({
            "type": t.tank_type,
            "qty_litres": qty,
            "value": val
        })
        finished_total += val
    
    # Carbon and Steel stock (if tracked separately)
    # For now, we'll assume they're in tanks or dispatch records
    
    return {
        "as_of": datetime.now().isoformat(),
        "raw_materials": {
            "items": raw_data,
            "total_value": round(raw_total, 2)
        },
        "finished_goods": {
            "items": finished_data,
            "total_value": round(finished_total, 2)
        },
        "grand_total": round(raw_total + finished_total, 2),
        "composition": {
            "raw_materials_pct": round((raw_total / (raw_total + finished_total) * 100) if (raw_total + finished_total) > 0 else 0, 1),
            "finished_goods_pct": round((finished_total / (raw_total + finished_total) * 100) if (raw_total + finished_total) > 0 else 0, 1)
        }
    }


# ═══════════════════════════════════════════════════════════
# REPORT 3: DOWNTIME ANALYSIS
# ═══════════════════════════════════════════════════════════

@router.get("/downtime-analysis")
def get_downtime_analysis(
    period: str = Query("this_month", regex="^(7d|this_month|last_month|ytd|custom)$"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    export_csv: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(require_manager_or_above())
):
    """
    Maintenance downtime hours by reactor.
    Helps identify equipment needing attention.
    """
    from models.reactor import Reactor
    from models.maintenance import MaintenanceRequest
    
    date_start, date_end = get_date_range(period, start_date, end_date)
    
    results = db.query(
        Reactor.id.label("reactor_id"),
        Reactor.reactor_code,
        Reactor.name.label("reactor_name"),
        func.count(MaintenanceRequest.id).label("maintenance_count"),
        func.sum(func.coalesce(MaintenanceRequest.downtime_hours, 0)).label("total_downtime"),
        func.avg(func.coalesce(MaintenanceRequest.downtime_hours, 0)).label("avg_downtime")
    ).outerjoin(
        MaintenanceRequest, and_(
            Reactor.id == MaintenanceRequest.reactor_id,
            MaintenanceRequest.status == "COMPLETED",
            MaintenanceRequest.resolved_at >= date_start,
            MaintenanceRequest.resolved_at <= date_end
        )
    ).filter(
        Reactor.is_active == True
    ).group_by(
        Reactor.id
    ).order_by(
        desc("total_downtime")
    ).all()
    
    data = []
    for r in results:
        data.append({
            "reactor_id": r.reactor_id,
            "reactor_code": r.reactor_code,
            "reactor_name": r.reactor_name,
            "maintenance_count": r.maintenance_count or 0,
            "total_downtime_hours": round(float(r.total_downtime or 0), 2),
            "avg_downtime_hours": round(float(r.avg_downtime or 0), 2)
        })
    
    if export_csv:
        return generate_csv(data, ["reactor_code", "reactor_name", "maintenance_count", 
                                   "total_downtime_hours", "avg_downtime_hours"])
    
    total_downtime = sum(d["total_downtime_hours"] for d in data)
    
    return {
        "period": period,
        "date_range": {"start": str(date_start), "end": str(date_end)},
        "total_downtime_hours": round(total_downtime, 2),
        "reactors": data
    }


# ═══════════════════════════════════════════════════════════
# REPORT 4: PROFITABILITY (ADMIN ONLY)
# ═══════════════════════════════════════════════════════════

@router.get("/profitability")
def get_profitability_report(
    period: str = Query("this_month", regex="^(7d|this_month|last_month|ytd|custom)$"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin())
):
    """
    Profitability analysis - Revenue vs Costs.
    ADMIN ONLY - Uses taxable subtotal, excludes GST.
    """
    from models.dispatch import SalesInvoice
    from models.grn import GoodsReceiptNote
    from models.production_batch import ProductionBatch
    from models.maintenance import MaintenanceRequest
    
    date_start, date_end = get_date_range(period, start_date, end_date)
    
    # Get configurable rates
    electricity_rate = get_setting(db, "electricity_rate_per_kwh", 8.0)
    labor_rate = get_setting(db, "avg_labor_cost_per_hour", 150.0)
    
    # REVENUE: Sum of taxable subtotal (before GST)
    revenue_result = db.query(
        func.sum(SalesInvoice.subtotal).label("total_revenue"),
        func.count(SalesInvoice.id).label("invoice_count")
    ).filter(
        SalesInvoice.invoice_date >= date_start,
        SalesInvoice.invoice_date <= date_end
    ).first()
    
    revenue = float(revenue_result.total_revenue or 0)
    invoice_count = revenue_result.invoice_count or 0
    
    # COSTS
    # 1. Raw Material Cost (from GRNs - net payable amount)
    grn_result = db.query(
        func.sum(GoodsReceiptNote.net_payable_amount).label("raw_material_cost")
    ).filter(
        GoodsReceiptNote.receipt_date >= date_start,
        GoodsReceiptNote.receipt_date <= date_end
    ).first()
    raw_material_cost = float(grn_result.raw_material_cost or 0)
    
    # 2. Power Cost (from batches)
    power_result = db.query(
        func.sum(ProductionBatch.electricity_used_kwh).label("total_kwh")
    ).filter(
        ProductionBatch.status == "COMPLETED",
        ProductionBatch.end_datetime >= date_start,
        ProductionBatch.end_datetime <= date_end
    ).first()
    total_kwh = float(power_result.total_kwh or 0)
    power_cost = total_kwh * electricity_rate
    
    # 3. Labor Cost (from maintenance requests)
    labor_result = db.query(
        func.sum(MaintenanceRequest.labor_hours).label("total_hours"),
        func.sum(MaintenanceRequest.labor_cost).label("recorded_cost")
    ).filter(
        MaintenanceRequest.status == "COMPLETED",
        MaintenanceRequest.resolved_at >= date_start,
        MaintenanceRequest.resolved_at <= date_end
    ).first()
    # Use recorded cost if available, otherwise calculate
    labor_cost = float(labor_result.recorded_cost or 0) or (float(labor_result.total_hours or 0) * labor_rate)
    
    # 4. Maintenance Parts Cost
    parts_result = db.query(
        func.sum(MaintenanceRequest.parts_cost).label("parts_cost")
    ).filter(
        MaintenanceRequest.status == "COMPLETED",
        MaintenanceRequest.resolved_at >= date_start,
        MaintenanceRequest.resolved_at <= date_end
    ).first()
    parts_cost = float(parts_result.parts_cost or 0)
    
    # CALCULATIONS
    total_costs = raw_material_cost + power_cost + labor_cost + parts_cost
    gross_profit = revenue - raw_material_cost
    operating_profit = revenue - total_costs
    margin_percent = (operating_profit / revenue * 100) if revenue > 0 else 0
    
    return {
        "period": period,
        "date_range": {"start": str(date_start), "end": str(date_end)},
        "revenue": {
            "total": round(revenue, 2),
            "invoice_count": invoice_count,
            "note": "Taxable subtotal (excludes GST)"
        },
        "costs": {
            "raw_materials": round(raw_material_cost, 2),
            "power": round(power_cost, 2),
            "power_kwh": round(total_kwh, 2),
            "labor": round(labor_cost, 2),
            "maintenance_parts": round(parts_cost, 2),
            "total": round(total_costs, 2)
        },
        "profit": {
            "gross_profit": round(gross_profit, 2),
            "operating_profit": round(operating_profit, 2),
            "margin_percent": round(margin_percent, 2)
        },
        "rates_used": {
            "electricity_per_kwh": electricity_rate,
            "labor_per_hour": labor_rate
        }
    }


# ═══════════════════════════════════════════════════════════
# REPORT 5: PRODUCTION SUMMARY
# ═══════════════════════════════════════════════════════════

@router.get("/production-summary")
def get_production_summary(
    period: str = Query("this_month", regex="^(7d|this_month|last_month|ytd|custom)$"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_manager_or_above())
):
    """
    Production throughput and efficiency summary.
    Includes syn-gas loss tracking.
    """
    from models.production_batch import ProductionBatch
    from models.reactor import Reactor
    
    date_start, date_end = get_date_range(period, start_date, end_date)
    target_oil = get_setting(db, "target_oil_yield", 42)
    syngas_threshold = get_setting(db, "syngas_loss_threshold", 8)
    
    # Batch statistics
    batch_stats = db.query(
        func.count(ProductionBatch.id).label("batch_count"),
        func.sum(ProductionBatch.input_weight_kg).label("total_input"),
        func.sum(ProductionBatch.oil_liters_to_tank).label("total_oil"),
        func.sum(ProductionBatch.carbon_output_kg).label("total_carbon"),
        func.sum(ProductionBatch.steel_output_kg).label("total_steel"),
        func.avg(ProductionBatch.oil_yield_pct).label("avg_oil_yield"),
        func.avg(ProductionBatch.carbon_yield_pct).label("avg_carbon_yield"),
        func.avg(ProductionBatch.electricity_used_kwh).label("avg_power_per_batch")
    ).filter(
        ProductionBatch.status == "COMPLETED",
        ProductionBatch.end_datetime >= date_start,
        ProductionBatch.end_datetime <= date_end
    ).first()
    
    # Calculate syn-gas loss (input - outputs = lost to gas/leaks)
    total_input = float(batch_stats.total_input or 0)
    total_oil = float(batch_stats.total_oil or 0) * 0.85  # Convert litres to kg approx
    total_carbon = float(batch_stats.total_carbon or 0)
    total_steel = float(batch_stats.total_steel or 0)
    total_outputs = total_oil + total_carbon + total_steel
    syngas_loss = total_input - total_outputs
    syngas_loss_pct = (syngas_loss / total_input * 100) if total_input > 0 else 0
    
    # Reactor utilization (compare active reactors vs batches)
    active_reactors = db.query(Reactor).filter(Reactor.is_active == True).count()
    days_in_period = (date_end - date_start).days + 1
    max_batches = active_reactors * days_in_period  # 1 batch/reactor/day theoretical
    utilization = (batch_stats.batch_count / max_batches * 100) if max_batches > 0 else 0
    
    return {
        "period": period,
        "date_range": {"start": str(date_start), "end": str(date_end)},
        "batches": {
            "count": batch_stats.batch_count or 0,
            "total_input_kg": round(total_input, 2),
            "avg_power_kwh": round(float(batch_stats.avg_power_per_batch or 0), 2)
        },
        "outputs": {
            "oil_litres": round(float(batch_stats.total_oil or 0), 2),
            "carbon_kg": round(total_carbon, 2),
            "steel_kg": round(total_steel, 2)
        },
        "yields": {
            "avg_oil_yield": round(float(batch_stats.avg_oil_yield or 0), 2),
            "avg_carbon_yield": round(float(batch_stats.avg_carbon_yield or 0), 2),
            "target_oil_yield": target_oil,
            "vs_target": round(float(batch_stats.avg_oil_yield or 0) - target_oil, 2)
        },
        "syngas": {
            "loss_kg": round(syngas_loss, 2),
            "loss_percent": round(syngas_loss_pct, 2),
            "threshold": syngas_threshold,
            "alert": syngas_loss_pct > syngas_threshold
        },
        "utilization": {
            "active_reactors": active_reactors,
            "capacity_utilization_pct": round(utilization, 1)
        }
    }


# ═══════════════════════════════════════════════════════════
# REPORT 6: SALES PERFORMANCE
# ═══════════════════════════════════════════════════════════

@router.get("/sales-performance")
def get_sales_performance(
    period: str = Query("this_month", regex="^(7d|this_month|last_month|ytd|custom)$"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    export_csv: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(require_manager_or_above())
):
    """
    Sales performance analysis.
    Includes top customers, product mix, and avg realization rates.
    """
    from models.dispatch import SalesInvoice, SalesDispatch, SalesDispatchItem
    from models.customer import Customer
    from models.product import Product
    
    date_start, date_end = get_date_range(period, start_date, end_date)
    
    # Top customers by revenue
    top_customers = db.query(
        Customer.id,
        Customer.name,
        func.sum(SalesInvoice.subtotal).label("revenue"),
        func.count(SalesInvoice.id).label("order_count")
    ).join(
        SalesDispatch, SalesInvoice.dispatch_id == SalesDispatch.id
    ).join(
        Customer, SalesDispatch.customer_id == Customer.id
    ).filter(
        SalesInvoice.invoice_date >= date_start,
        SalesInvoice.invoice_date <= date_end
    ).group_by(Customer.id).order_by(desc("revenue")).limit(10).all()
    
    customer_data = [{
        "rank": i+1,
        "customer_name": c.name,
        "revenue": round(float(c.revenue or 0), 2),
        "order_count": c.order_count
    } for i, c in enumerate(top_customers)]
    
    # Product mix (by quantity dispatched)
    product_mix = db.query(
        Product.name,
        Product.product_code,
        func.sum(SalesDispatchItem.quantity).label("qty"),
        func.sum(SalesDispatchItem.quantity * SalesDispatchItem.rate).label("value")
    ).join(
        SalesDispatchItem, Product.id == SalesDispatchItem.product_id
    ).join(
        SalesDispatch, SalesDispatchItem.dispatch_id == SalesDispatch.id
    ).filter(
        SalesDispatch.dispatch_date >= date_start,
        SalesDispatch.dispatch_date <= date_end
    ).group_by(Product.id).all()
    
    total_value = sum(float(p.value or 0) for p in product_mix)
    mix_data = [{
        "product": p.name,
        "code": p.product_code,
        "qty": float(p.qty or 0),
        "value": round(float(p.value or 0), 2),
        "pct": round((float(p.value or 0) / total_value * 100) if total_value > 0 else 0, 1)
    } for p in product_mix]
    
    # Average realization rates (selling price per kg/litre)
    realization = {}
    for p in product_mix:
        qty = float(p.qty or 0)
        val = float(p.value or 0)
        if qty > 0:
            realization[p.name] = round(val / qty, 2)
    
    if export_csv:
        return generate_csv(customer_data, ["rank", "customer_name", "revenue", "order_count"])
    
    return {
        "period": period,
        "date_range": {"start": str(date_start), "end": str(date_end)},
        "top_customers": customer_data,
        "product_mix": mix_data,
        "avg_realization_rates": realization,
        "total_sales_value": round(total_value, 2)
    }
