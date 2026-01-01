# AI Agent Context — Tyre Pyrolysis ERP

> **Purpose**: Machine-readable context for AI coding agents to understand and modify this codebase.

## Quick Reference

| Aspect | Details |
|--------|---------|
| **Type** | Full-stack Manufacturing ERP |
| **Backend** | FastAPI (Python 3.9+), SQLAlchemy ORM, SQLite |
| **Frontend** | Vue 3 (Composition API), Axios, Chart.js |
| **API Base** | `http://localhost:8000/api/v1` |
| **Auth** | JWT Bearer tokens, role-based (admin/manager/operator) |

---

## Directory Structure

```
/backend
├── main.py             # FastAPI app entry, router registration
├── config.py           # Settings (APP_NAME, VERSION, CORS, DATABASE_URL)
├── database.py         # SQLAlchemy engine, Base, get_db dependency
├── auth/               # Authentication router + security helpers
├── models/             # 23 SQLAlchemy ORM models
├── modules/            # API routers by domain
│   ├── procurement/    # vendors, POs, GRNs
│   ├── production/     # reactors, batches, recipes
│   ├── tank_farm/      # storage tanks, transfers
│   ├── sales/          # customers, quotations, dispatches, returns
│   ├── dashboard_router.py
│   ├── maintenance_router.py
│   └── reports_router.py
├── schemas/            # Pydantic request/response models
├── services/           # Business logic helpers
└── scripts/            # Seed data, migrations

/frontend
├── index.html
├── vite.config.js
└── src/
    ├── main.js         # Vue app bootstrap
    ├── router.js       # Vue Router configuration
    ├── style.css       # Global CSS
    ├── services/
    │   └── api.js      # Axios API client (all endpoints)
    ├── components/     # Reusable Vue components
    └── views/          # Page components by module
        ├── Dashboard.vue
        ├── Login.vue
        ├── Reports.vue
        ├── MaintenanceHub.vue
        ├── procurement/
        ├── production/
        ├── sales/
        └── settings/
```

---

## Data Models (23 Total)

### Core Entities
| Model | Key Fields | Notes |
|-------|------------|-------|
| `Vendor` | vendor_code, name, gst_number, epr_status | GST/EPR compliance |
| `Customer` | customer_code, name, gst_number, credit_limit | Sales party |
| `RawMaterial` | material_code, name, density, moisture_threshold | Input material specs |
| `Product` | product_code, name, category (OIL/CARBON/STEEL) | Output product catalog |
| `User` | username, email, role, is_active | Login accounts |

### Procurement Flow
| Model | Key Fields | Relationships |
|-------|------------|---------------|
| `PurchaseOrder` | po_number, status, vendor_id | FK → Vendor |
| `PurchaseOrderLine` | quantity_kg, rate_per_kg | FK → PurchaseOrder |
| `WeighbridgeEntry` | gross_weight, tare_weight | FK → PO |
| `GoodsReceiptNote` | grn_number, net_payable_amount | FK → WeighbridgeEntry |
| `InventoryLot` | lot_code, available_qty_kg | FIFO tracking |

### Production Flow
| Model | Key Fields | Notes |
|-------|------------|-------|
| `Reactor` | reactor_code, status, current_batch_id | IDLE/CHARGING/RUNNING/etc |
| `BatchRecipe` | recipe_name, target_oil_yield_pct | Process templates |
| `RecipeStage` | stage_number, duration_minutes | FK → Recipe |
| `ProductionBatch` | batch_number, status, oil_liters_to_tank | FK → Reactor |
| `BatchLogEntry` | stage_number, temperature, notes | FK → Batch |

### Tank Farm
| Model | Key Fields | Notes |
|-------|------------|-------|
| `StorageTank` | tank_code, capacity_liters, current_level_liters | Oil storage |
| `TankTransfer` | from_tank_id, to_tank_id, volume_liters | Movement log |

### Sales Flow
| Model | Key Fields | Notes |
|-------|------------|-------|
| `Quotation` | quotation_number, status, customer_id | DRAFT→SENT→ACCEPTED |
| `SaleOrder` | so_number, status, quotation_id | Created from quotation |
| `OutputDispatch` | dispatch_number, status, sale_order_id | Delivery tracking |
| `SalesInvoice` | invoice_number, total_amount | FK → Dispatch |
| `SalesReturn` | return_number, status | RMA workflow |
| `CreditNote` | credit_number, amount | FK → Return |

### Maintenance
| Model | Key Fields | Notes |
|-------|------------|-------|
| `MaintenanceSchedule` | task_name, frequency_days | Recurring tasks |
| `MaintenanceRequest` | priority, status, downtime_hours | Tickets |
| `MaintenanceLog` | performed_date, technician_name | Completed work |
| `SparePart` | part_code, current_stock | Inventory |

---

## API Endpoints Summary

All endpoints are prefixed with `/api/v1`.

### Authentication
| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/login` | Returns JWT token |
| GET | `/auth/me` | Current user info |
| GET | `/auth/users` | List users (admin) |
| POST | `/auth/users` | Create user (admin) |

### Procurement (`/procurement/`)
| Method | Path | Description |
|--------|------|-------------|
| GET/POST | `/vendors` | List/Create vendors |
| GET/PUT | `/vendors/{id}` | Get/Update vendor |
| GET/POST | `/purchase-orders` | List/Create POs |
| PUT | `/purchase-orders/{id}/confirm` | Confirm PO |
| POST | `/inward-entry/calculate` | Preview GRN deductions |
| POST | `/inward-entry` | Create GRN |
| GET | `/grn` | List GRNs |

### Production (`/production/`)
| Method | Path | Description |
|--------|------|-------------|
| GET/POST | `/reactors` | List/Create reactors |
| PUT | `/reactors/{id}/status` | Update reactor status |
| GET/POST | `/batches` | List/Start batches |
| POST | `/batches/{id}/complete` | Complete with outputs |
| PUT | `/batches/{id}/hold` | Hold batch |
| PUT | `/batches/{id}/advance-stage` | Advance recipe stage |
| GET/POST | `/recipes` | Recipe management |
| GET | `/lots/available` | FIFO lots |

### Tank Farm (`/tank-farm/`)
| Method | Path | Description |
|--------|------|-------------|
| GET/POST | `/tanks` | Tank management |
| GET/POST | `/transfers` | Tank-to-tank transfers |

### Sales (`/sales/`, `/quotations/`, `/dispatches/`, `/returns/`)
| Method | Path | Description |
|--------|------|-------------|
| GET/POST | `/customers` | Customer master |
| GET/POST | `/products` | Product catalog |
| POST | `/quotations/` | Create quotation |
| PUT | `/quotations/{id}/send` | Send to customer |
| POST | `/quotations/{id}/convert` | Convert to SO |
| POST | `/dispatches/` | Create dispatch |
| PUT | `/dispatches/{id}/ship` | Mark shipped |
| POST | `/dispatches/{id}/generate-invoice` | Create invoice |
| POST | `/returns/` | Create return |
| GET | `/returns/{id}/credit-note` | Get credit note |

### Dashboard (`/dashboard/`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/summary` | All KPIs + reactor status |
| GET | `/alerts` | Pending action items |
| GET | `/activity` | Recent transactions |

### Reports (`/reports/`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/vendor-yield` | Yield by vendor |
| GET | `/inventory-valuation` | Stock value |
| GET | `/downtime-analysis` | Reactor downtime |
| GET | `/profitability` | Revenue/costs/margin |
| GET | `/production-summary` | Output stats |
| GET | `/sales-performance` | Sales metrics |

### Maintenance (`/maintenance/`)
| Method | Path | Description |
|--------|------|-------------|
| GET/POST | `/schedules` | Scheduled tasks |
| GET | `/due-tasks` | Overdue + upcoming |
| GET/POST | `/requests` | Maintenance tickets |
| PUT | `/requests/{id}/complete` | Close request |
| GET | `/spare-parts` | Parts inventory |
| POST | `/spare-parts/{id}/issue` | Issue parts |

---

## Common Patterns

### Adding a New API Endpoint
1. Define model in `backend/models/{module}.py`
2. Import model in `backend/database.py` → `init_db()`
3. Create/update router in `backend/modules/{module}/`
4. Register router in `backend/main.py`
5. Add frontend methods in `frontend/src/services/api.js`
6. Create Vue component in `frontend/src/views/`

### Database Queries
```python
from database import get_db
from sqlalchemy.orm import Session
from fastapi import Depends

@router.get("/items")
def get_items(db: Session = Depends(get_db)):
    return db.query(Model).filter(Model.active == True).all()
```

### Authentication
```python
from auth.dependencies import get_current_user, require_manager_or_above

@router.get("/protected")
def protected(user: User = Depends(get_current_user)):
    return {"user": user.username}

@router.delete("/admin-only", dependencies=[Depends(require_admin())])
def admin_action():
    pass
```

### Frontend API Call
```javascript
import { salesApi } from '@/services/api'

const loadData = async () => {
    const { data } = await salesApi.listCustomers()
    customers.value = data
}
```

---

## Key Business Logic

### FIFO Inventory
- `InventoryLot` tracks individual receipt lots
- Consumption uses oldest lots first
- `ProductionBatch.consume_lots()` handles allocation

### Reactor State Machine
```
IDLE → CHARGING → RUNNING → COOLING → DISCHARGING → CLEANING → IDLE
         ↓
    MAINTENANCE (from any active state)
```

### Sales Workflow
```
Quotation(DRAFT) → send() → SENT → accept() → ACCEPTED → convert() → SaleOrder
    ↓
Dispatch(PENDING) → ship() → SHIPPED → deliver() → DELIVERED → generate_invoice()
```

### Maintenance Interlock
- Reactor cannot start batch if `status == MAINTENANCE`
- Check via `GET /maintenance/check-interlock/{reactor_id}`

---

## Environment Setup

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev  # Port 5173
```

---

## Testing Commands

```bash
# API Health
curl http://localhost:8000/health

# Login (get token)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Authenticated request
curl http://localhost:8000/api/v1/dashboard/summary \
  -H "Authorization: Bearer <token>"
```

---

## Modification Checklist

When modifying this codebase:

- [ ] Check model column names in `backend/models/` before querying
- [ ] Update `database.py` imports when adding new models
- [ ] Register new routers in `main.py`
- [ ] Add API methods to `frontend/src/services/api.js`
- [ ] Use existing auth dependencies for protected routes
- [ ] Follow existing patterns for consistency
