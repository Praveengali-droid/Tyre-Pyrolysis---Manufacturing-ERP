# Developer Guide — Tyre Pyrolysis Manufacturing ERP

Welcome to the Tyre Pyrolysis ERP codebase! This guide explains the system architecture, data flows, and everything you need to develop new features or integrations.

---

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Getting Started](#getting-started)
4. [Data Flow](#data-flow)
5. [Backend Deep Dive](#backend-deep-dive)
6. [Frontend Structure](#frontend-structure)
7. [API Reference](#api-reference)
8. [Database Schema](#database-schema)
9. [Authentication & Authorization](#authentication--authorization)
10. [Integration Points](#integration-points)
11. [Development Workflow](#development-workflow)

---

## System Overview

This is a **Manufacturing ERP** system designed specifically for tyre pyrolysis plants. It manages the complete value chain:

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ PROCUREMENT │ →  │ PRODUCTION  │ →  │  TANK FARM  │ →  │    SALES    │
│             │    │             │    │             │    │             │
│  • Vendors  │    │  • Reactors │    │  • Storage  │    │ • Customers │
│  • POs      │    │  • Batches  │    │  • Transfers│    │ • Quotations│
│  • GRNs     │    │  • Recipes  │    │             │    │ • Dispatches│
│  • Lots     │    │             │    │             │    │ • Invoices  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

### Key Features
- **Procurement**: Vendor management with GST/EPR compliance, Purchase Orders with approval workflow, Goods Receipt with deduction handling
- **Production**: Multi-reactor management with stage-wise tracking, FIFO inventory consumption, yield analysis
- **Tank Farm**: Oil storage tank management, tank-to-tank transfers, level monitoring
- **Sales**: Customer management, quotation → order → dispatch flow, credit notes, returns
- **Maintenance**: Preventive schedules, request ticketing, spare parts inventory
- **Reports**: Financial reports, production analytics, vendor yield analysis

---

## Architecture

### Technology Stack

| Layer | Technology | Version |
|-------|------------|---------|
| **Backend** | FastAPI (Python) | 3.9+ |
| **Database** | SQLite + SQLAlchemy ORM | 2.0 |
| **Frontend** | Vue.js 3 | Composition API |
| **API Client** | Axios | 1.6+ |
| **Charts** | Chart.js | 4.x |
| **Auth** | JWT (python-jose) | - |

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Vue 3)                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │Dashboard │ │Production│ │  Sales   │ │ Reports  │ ...       │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘           │
│       └────────────┴────────────┴────────────┘                  │
│                          │ api.js (Axios)                       │
└──────────────────────────┼──────────────────────────────────────┘
                           ↓ HTTP REST (JSON)
┌──────────────────────────┼──────────────────────────────────────┐
│                       BACKEND (FastAPI)                         │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                      main.py (Router Registration)          ││
│  └─────────────────────────────────────────────────────────────┘│
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐       │
│  │procurement│ │production │ │  sales    │ │maintenance│ ...   │
│  │  _router  │ │  _router  │ │ _routers  │ │  _router  │       │
│  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └─────┬─────┘       │
│        └─────────────┴─────────────┴─────────────┘              │
│                          │ get_db()                             │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │               SQLAlchemy ORM (models/)                      ││
│  └─────────────────────────────────────────────────────────────┘│
└──────────────────────────┼──────────────────────────────────────┘
                           ↓
                    ┌──────────────┐
                    │   SQLite DB  │
                    │   (erp.db)   │
                    └──────────────┘
```

---

## Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start server (auto-reload enabled)
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000/api/v1
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Frontend runs at http://localhost:5173

### Default Login
- **Username**: `admin`
- **Password**: `admin123`

---

## Data Flow

### 1. Procurement → Inventory Flow

```
Vendor → Purchase Order → Weighbridge Entry → GRN → Inventory Lots
```

**Detailed Flow**:
1. Create a **Vendor** with GST and contact details
2. Create a **Purchase Order** (PO) with line items (qty, rate)
3. When material arrives, record **Weighbridge Entry** (gross/tare weights)
4. System calculates deductions (moisture, wastage) and creates **GRN**
5. GRN approval creates **Inventory Lots** (FIFO tracking)

### 2. Production Flow

```
Inventory Lots → Reactor → Production Batch → Output (Oil/Carbon/Steel)
```

**Detailed Flow**:
1. Select **Reactor** and check availability (not in maintenance)
2. Start **Production Batch** with a **Recipe** (defines stages)
3. System consumes oldest **Inventory Lots** (FIFO)
4. Progress through **Recipe Stages** (charging → heating → pyrolysis → cooling)
5. Complete batch, record outputs:
   - **Oil** → Sent to Storage Tanks
   - **Carbon Black** → Stock
   - **Steel Wire** → Stock

### 3. Tank Farm Flow

```
Production Batch → Storage Tank → Tank-to-Tank Transfer → Ready for Sale
```

**Detailed Flow**:
1. Oil from completed batches fills designated **Storage Tank**
2. Optional: **Tank Transfers** to consolidate or segregate
3. Tank levels tracked in real-time

### 4. Sales Flow

```
Customer → Quotation → Sale Order → Dispatch → Invoice → (Optional: Return → Credit Note)
```

**Detailed Flow**:
1. Create **Customer** with credit limit
2. Create **Quotation** with products and pricing
3. Send quotation, customer accepts → Convert to **Sale Order**
4. Create **Dispatch** (picks from tank/stock)
5. Generate **Invoice** on delivery
6. If return: Create **Sales Return** → QC → **Credit Note**

---

## Backend Deep Dive

### Directory Structure

```
backend/
├── main.py              # FastAPI app, CORS, router registration
├── config.py            # Settings (env vars, database URL, CORS)
├── database.py          # SQLAlchemy engine, session, Base class
│
├── auth/
│   ├── router.py        # Login, user management endpoints
│   ├── dependencies.py  # get_current_user, require_admin, etc.
│   └── security.py      # JWT encoding/decoding, password hashing
│
├── models/              # SQLAlchemy ORM models (23 files)
│   ├── __init__.py      # Re-exports all models
│   ├── vendor.py        # Vendor + VendorBankDetail
│   ├── purchase_order.py
│   ├── grn.py           # GRN + GRN Details + WeighbridgeEntry
│   ├── inventory_lot.py # FIFO inventory
│   ├── reactor.py
│   ├── production_batch.py
│   ├── storage_tank.py
│   ├── customer.py
│   ├── quotation.py     # Quotation + QuotationItem + SaleOrder
│   ├── dispatch.py      # Dispatch + DispatchItem + SalesInvoice
│   ├── sales_return.py  # SalesReturn + CreditNote
│   ├── maintenance.py   # MaintenanceSchedule, Request, Log, SparePart
│   └── ...
│
├── modules/             # API routers by business domain
│   ├── procurement/     # vendor_routes.py, po_routes.py, grn_routes.py
│   ├── production/      # reactor_routes.py, batch_routes.py
│   ├── tank_farm/       # tank_routes.py
│   ├── sales/           # router.py, quotation_router.py, dispatch_router.py
│   ├── dashboard_router.py
│   ├── maintenance_router.py
│   └── reports_router.py
│
├── schemas/             # Pydantic schemas (request/response validation)
│   ├── vendor.py
│   ├── production.py
│   └── ...
│
├── services/            # Business logic (minimal usage currently)
│   └── inward_service.py
│
└── scripts/
    └── seed_data.py     # Script to populate test data
```

### Adding a New Feature

**Example: Adding a new "Equipment" module**

1. **Create the model** (`backend/models/equipment.py`):
```python
from sqlalchemy import Column, Integer, String, Float, DateTime
from database import Base
from datetime import datetime

class Equipment(Base):
    __tablename__ = "equipment"
    
    id = Column(Integer, primary_key=True, index=True)
    equipment_code = Column(String(50), unique=True)
    name = Column(String(100))
    location = Column(String(100))
    last_serviced = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
```

2. **Register with database** (`backend/database.py`):
```python
# Add import in init_db()
from models import equipment
```

3. **Create the router** (`backend/modules/equipment_router.py`):
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.equipment import Equipment

router = APIRouter(prefix="/equipment", tags=["Equipment"])

@router.get("/")
def list_equipment(db: Session = Depends(get_db)):
    return db.query(Equipment).all()

@router.post("/")
def create_equipment(code: str, name: str, db: Session = Depends(get_db)):
    item = Equipment(equipment_code=code, name=name)
    db.add(item)
    db.commit()
    return item
```

4. **Register the router** (`backend/main.py`):
```python
from modules.equipment_router import router as equipment_router
app.include_router(equipment_router, prefix="/api/v1")
```

5. **Add frontend API** (`frontend/src/services/api.js`):
```javascript
export const equipmentApi = {
    list: () => api.get('/equipment/'),
    create: (data) => api.post('/equipment/', null, { params: data })
}
```

---

## Frontend Structure

```
frontend/src/
├── main.js          # Vue app bootstrap
├── App.vue          # Root component (sidebar layout)
├── router.js        # Vue Router (all routes defined here)
├── style.css        # Global styles
│
├── assets/          # Static assets
│
├── components/      # Reusable components
│   ├── AppSidebar.vue
│   ├── Notification.vue
│   └── ...
│
├── composables/     # Vue 3 composables
│   └── useNotification.js
│
├── services/
│   ├── api.js       # Centralized Axios API client
│   └── auth.js      # Auth helper functions
│
└── views/           # Page components
    ├── Dashboard.vue       # Main dashboard
    ├── Login.vue           # Login page
    ├── Reports.vue         # Analytics
    ├── MaintenanceHub.vue  # Maintenance module
    │
    ├── procurement/
    │   ├── VendorMaster.vue
    │   ├── PurchaseOrders.vue
    │   ├── InwardEntry.vue
    │   └── GRNList.vue
    │
    ├── production/
    │   └── ControlRoom.vue  # Reactor management, batches
    │
    ├── sales/
    │   ├── SalesDashboard.vue
    │   ├── CustomerMaster.vue
    │   ├── Quotations.vue
    │   ├── Dispatches.vue
    │   ├── SalesReturns.vue
    │   └── ...
    │
    └── settings/
        ├── UserManagement.vue
        └── SystemSettings.vue
```

### Key Frontend Patterns

#### API Calls (Composition API)
```vue
<script setup>
import { ref, onMounted } from 'vue'
import { vendorApi } from '@/services/api'

const vendors = ref([])
const loading = ref(false)

const loadVendors = async () => {
    loading.value = true
    try {
        const { data } = await vendorApi.list()
        vendors.value = data.items
    } finally {
        loading.value = false
    }
}

onMounted(loadVendors)
</script>
```

#### Route Guards (in router.js)
```javascript
router.beforeEach((to, from, next) => {
    const token = localStorage.getItem('token')
    if (to.meta.requiresAuth && !token) {
        next('/login')
    } else {
        next()
    }
})
```

---

## API Reference

### Base URL
```
http://localhost:8000/api/v1
```

### Authentication
All endpoints except `/auth/login` require a JWT token:
```
Authorization: Bearer <token>
```

### Core Endpoints

| Module | Endpoint | Methods | Description |
|--------|----------|---------|-------------|
| Auth | `/auth/login` | POST | Get JWT token |
| Auth | `/auth/me` | GET | Current user |
| Vendors | `/procurement/vendors` | GET, POST | List/Create |
| POs | `/procurement/purchase-orders` | GET, POST | List/Create |
| GRNs | `/procurement/grn` | GET | List GRNs |
| Reactors | `/production/reactors` | GET, POST | Reactor management |
| Batches | `/production/batches` | GET, POST | Batch list/start |
| Tanks | `/tank-farm/tanks` | GET, POST | Tank management |
| Customers | `/sales/customers` | GET, POST | Customer master |
| Quotations | `/quotations/` | GET, POST | Quotation lifecycle |
| Dispatches | `/dispatches/` | GET, POST | Dispatch management |
| Dashboard | `/dashboard/summary` | GET | KPI data |
| Reports | `/reports/vendor-yield` | GET | Analytics |

### Common Query Parameters

| Parameter | Used In | Description |
|-----------|---------|-------------|
| `period` | Reports | `this_month`, `last_month`, `this_quarter`, `custom` |
| `start_date` | Reports | Custom range start (YYYY-MM-DD) |
| `end_date` | Reports | Custom range end |
| `status` | Quotations, Dispatches | Filter by status |
| `export_csv` | Reports | Set `true` to download CSV |

---

## Database Schema

### Entity Relationship Diagram (Simplified)

```
┌────────────┐     ┌─────────────────┐     ┌───────────────┐
│   Vendor   │←────│  PurchaseOrder  │────→│  POLineItem   │
└────────────┘     └─────────────────┘     └───────────────┘
                            ↓
                   ┌─────────────────┐
                   │ WeighbridgeEntry│
                   └────────┬────────┘
                            ↓
                   ┌─────────────────┐     ┌───────────────┐
                   │       GRN       │────→│  InventoryLot │
                   └─────────────────┘     └───────┬───────┘
                                                   ↓ (consumed by)
┌────────────┐     ┌─────────────────┐     ┌───────────────┐
│   Reactor  │←────│ ProductionBatch │────→│  BatchRecipe  │
└────────────┘     └────────┬────────┘     └───────────────┘
                            ↓
                   ┌─────────────────┐
                   │   StorageTank   │ (receives oil)
                   └─────────────────┘
                            ↓
┌────────────┐     ┌─────────────────┐     ┌───────────────┐
│  Customer  │←────│   Quotation     │────→│QuotationItem  │
└────────────┘     └────────┬────────┘     └───────────────┘
                            ↓ (convert)
                   ┌─────────────────┐
                   │    SaleOrder    │
                   └────────┬────────┘
                            ↓
                   ┌─────────────────┐     ┌───────────────┐
                   │    Dispatch     │────→│ DispatchItem  │
                   └────────┬────────┘     └───────────────┘
                            ↓
                   ┌─────────────────┐
                   │  SalesInvoice   │
                   └─────────────────┘
```

### Key Tables

| Table | Purpose | Primary Key |
|-------|---------|-------------|
| `vendors` | Supplier master | id (auto) |
| `purchase_orders` | PO header | id |
| `goods_receipt_notes` | Material inward | id |
| `inventory_lots` | FIFO stock tracking | id |
| `reactors` | Plant equipment | id |
| `production_batches` | Batch operations | id |
| `storage_tanks` | Oil storage | id |
| `customers` | Customer master | id |
| `quotations` | Sales quotes | id |
| `sale_orders` | Confirmed sales | id |
| `output_dispatches` | Delivery records | id |
| `sales_invoices` | Billing | id |

---

## Authentication & Authorization

### JWT Flow
1. POST `/auth/login` with `{username, password}`
2. Receive `{access_token, user: {...}}`
3. Store token in `localStorage`
4. Attach to requests: `Authorization: Bearer <token>`

### Roles
| Role | Access Level |
|------|--------------|
| `admin` | Full access |
| `manager` | Reports + most operations |
| `operator` | Production, inward entry |
| `viewer` | Read-only |

### Using Role Requirements
```python
from auth.dependencies import require_admin, require_manager_or_above

# Admin only
@router.delete("/users/{id}", dependencies=[Depends(require_admin())])

# Manager or Admin
@router.get("/reports", dependencies=[Depends(require_manager_or_above())])
```

---

## Integration Points

### External System Integration

#### 1. REST API Integration
All endpoints are REST-ful. Use the API for:
- ERP integrations (Tally, SAP)
- Mobile apps
- Third-party services

#### 2. Webhook Pattern (Not Yet Implemented)
For event-driven integrations, you could add:
```python
# Example: Notify external system on invoice generation
async def send_webhook(event_type, payload):
    async with httpx.AsyncClient() as client:
        await client.post(WEBHOOK_URL, json={"event": event_type, **payload})
```

#### 3. Database Direct Access
For BI/reporting tools:
- Database: SQLite (`backend/erp.db`)
- Can be migrated to PostgreSQL by changing `DATABASE_URL`

### Common Integration Scenarios

| Scenario | Approach |
|----------|----------|
| Tally sync | Call `/sales/invoices` API on invoice generation |
| IoT sensors | POST to `/production/batches/{id}/log-entry` |
| Weighbridge | POST to `/procurement/inward-entry/calculate` |
| Mobile app | Use existing REST API with JWT auth |
| Dashboard BI | Query `/dashboard/summary` or direct DB |

---

## Development Workflow

### Common Tasks

#### Running Seed Data
```bash
cd backend
python scripts/seed_data.py
```

#### Checking API Docs
Visit http://localhost:8000/docs for interactive Swagger UI.

#### Database Inspection
```bash
sqlite3 backend/erp.db
.tables
.schema vendors
SELECT * FROM vendors LIMIT 5;
```

### Debugging Tips

1. **Backend logs**: Check terminal running uvicorn
2. **Database queries**: Set `DEBUG=True` in `config.py` for SQL logging
3. **Frontend errors**: Browser DevTools → Console + Network tabs
4. **API testing**: Use Swagger UI or Postman

### Before Committing

- [ ] Backend runs without errors
- [ ] Frontend compiles without errors
- [ ] API endpoints return correct data
- [ ] No hardcoded test values left

---

## Questions?

- **API Documentation**: http://localhost:8000/docs
- **Database Schema**: Check `backend/models/` files
- **Frontend Routes**: See `frontend/src/router.js`

Happy coding! 🚀
