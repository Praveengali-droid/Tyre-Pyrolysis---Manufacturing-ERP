"""
Tyre Pyrolysis ERP - FastAPI Main Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import get_settings
from database import init_db
from modules.procurement import procurement_router
from modules.production import production_router
from modules.tank_farm import tank_farm_router
from modules.sales.router import router as sales_router
from modules.sales.quotation_router import router as quotation_router


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events."""
    # Startup
    print("🚀 Starting Tyre Pyrolysis ERP...")
    init_db()
    print(f"✅ Server running at http://localhost:8000")
    print(f"📚 API Docs: http://localhost:8000/docs")
    yield
    # Shutdown
    print("👋 Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="""
    ## Tyre Pyrolysis Plant - 360° ERP System
    
    A comprehensive ERP for managing:
    - **Procurement** - Vendors, Purchase Orders, Goods Receipt with deductions
    - **Production** - Batch tracking, Mass balance, Yield analysis  
    - **Tank Farm** - Storage tanks, Oil transfers, Water separation
    - **Sales** - Customers, Quotations, Orders, Dispatch
    
    ### Currently Implemented:
    
    **Phase 1-2: Procurement**
    - Vendor Master with GST/EPR compliance
    - Purchase Orders, Inward Entry (Weighbridge + GRN)
    - Deduction handling, FIFO Inventory Lots
    
    **Phase 3-4: Production + Tank Farm**
    - Reactor management
    - Batch tracking with mass balance
    - Oil storage tanks with level tracking
    
    **Phase 5: Sales**
    - Quotation → Sale Order → Dispatch workflow
    """,
    lifespan=lifespan,
)

# CORS middleware for frontend
# For demo: allow all origins. In production, restrict to specific domains.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for demo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(procurement_router, prefix="/api/v1")
app.include_router(production_router, prefix="/api/v1")
app.include_router(tank_farm_router, prefix="/api/v1")
app.include_router(sales_router, prefix="/api/v1")
app.include_router(quotation_router, prefix="/api/v1")

# Import and include dispatch router
from modules.sales.dispatch_router import router as dispatch_router
app.include_router(dispatch_router, prefix="/api/v1")

# Import and include returns router
from modules.sales.returns_router import router as returns_router
app.include_router(returns_router, prefix="/api/v1")

# Import and include maintenance router
from modules.maintenance_router import router as maintenance_router
app.include_router(maintenance_router, prefix="/api/v1")

# Import and include auth router
from auth.router import router as auth_router
app.include_router(auth_router, prefix="/api/v1")

# Import and include reports router
from modules.reports_router import router as reports_router
app.include_router(reports_router, prefix="/api/v1")

# Import and include dashboard router
from modules.dashboard_router import router as dashboard_router
app.include_router(dashboard_router, prefix="/api/v1")


# Root endpoint
@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "status": "running"
    }


# Health check
@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
