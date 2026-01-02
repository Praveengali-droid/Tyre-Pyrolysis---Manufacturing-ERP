"""
Database connection and session management.
Uses SQLAlchemy with SQLite for development.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import get_settings

settings = get_settings()

# Create SQLite engine
# For SQLite, we need check_same_thread=False for FastAPI's async nature
connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG  # Log SQL queries in debug mode
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()


def get_db():
    """
    Dependency that provides a database session.
    Automatically closes the session after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize the database by creating all tables.
    Call this on application startup.
    """
    # Import all models here to ensure they're registered with Base
    from models import vendor, raw_material, purchase_order, weighbridge, grn, inventory_lot
    from models import reactor, storage_tank, production_batch, tank_transfer
    from models import batch_recipe, recipe_stage, batch_log_entry
    from models import output_dispatch
    from models import customer
    from models import product
    from models import quotation
    from models import dispatch
    from models import sales_return
    from models import user, maintenance, system_settings
    
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")
    
    # Seed admin user if no users exist
    seed_admin_user()


def seed_admin_user():
    """
    Create default admin user if no users exist.
    Called on application startup for fresh deployments.
    """
    from models.user import User
    from auth.security import get_password_hash
    
    db = SessionLocal()
    try:
        # Check if any user exists
        user_count = db.query(User).count()
        if user_count == 0:
            print("🔐 No users found. Creating default admin user...")
            admin = User(
                username="admin",
                email="admin@erp.local",
                password_hash=get_password_hash("admin123"),
                full_name="System Administrator",
                role="ADMIN",
                is_active=True
            )
            db.add(admin)
            db.commit()
            print("✅ Default admin user created: admin / admin123")
            
            # Seed basic demo data inline
            seed_basic_demo_data(db)
        else:
            print(f"👥 Found {user_count} existing user(s)")
    except Exception as e:
        print(f"⚠️ Error seeding: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def seed_basic_demo_data(db):
    """
    Seed minimal demo data inline (no subprocess) for reports to show something.
    """
    from models.vendor import Vendor
    from models.customer import Customer
    from models.product import Product
    from models.reactor import Reactor
    from models.storage_tank import StorageTank
    from decimal import Decimal
    
    print("🌱 Seeding basic demo data...")
    
    try:
        # Vendors
        vendors = [
            Vendor(vendor_code="V-PREM-001", name="ShreeSai Rubber Industries", vendor_type="SUPPLIER", 
                   city="Hyderabad", state="Andhra Pradesh", country="India", 
                   gst_number="37AADCS1234A1Z5", is_epr_compliant=True, is_active=True),
            Vendor(vendor_code="V-BUDG-001", name="Bharat Scrap Traders", vendor_type="SUPPLIER",
                   city="Vijayawada", state="Andhra Pradesh", country="India",
                   gst_number="37AADBS5678B1Z3", is_epr_compliant=True, is_active=True),
        ]
        for v in vendors:
            db.add(v)
        
        # Customers
        customers = [
            Customer(customer_code="CUST-001", name="Mahalakshmi Oils Pvt Ltd", customer_type="ALL",
                     city="Guntur", state="Andhra Pradesh", gst_number="37AADCM9012C1Z1",
                     credit_limit=500000, payment_terms_days=30, is_active=True),
            Customer(customer_code="CUST-002", name="Andhra Industries", customer_type="ALL",
                     city="Vijayawada", state="Andhra Pradesh", gst_number="37AADAI3456D1Z9",
                     credit_limit=300000, payment_terms_days=30, is_active=True),
        ]
        for c in customers:
            db.add(c)
        
        # Products
        products = [
            Product(product_code="PRD-OIL-001", name="Pyrolysis Oil (TFO)", product_type="OIL",
                    unit="LITERS", default_rate=Decimal("45.00"), gst_rate=Decimal("18.0"), is_active=True),
            Product(product_code="PRD-CBK-001", name="Carbon Black", product_type="CARBON",
                    unit="KG", default_rate=Decimal("18.00"), gst_rate=Decimal("18.0"), is_active=True),
            Product(product_code="PRD-STL-001", name="Steel Scrap", product_type="STEEL",
                    unit="KG", default_rate=Decimal("25.00"), gst_rate=Decimal("18.0"), is_active=True),
        ]
        for p in products:
            db.add(p)
        
        # Reactors
        reactors = [
            Reactor(reactor_code="R1", name="Reactor Alpha", capacity_kg=Decimal("600"),
                    status="IDLE", batches_since_last_cleaning=0, maintenance_frequency=3, is_active=True),
            Reactor(reactor_code="R2", name="Reactor Beta", capacity_kg=Decimal("600"),
                    status="IDLE", batches_since_last_cleaning=2, maintenance_frequency=3, is_active=True),
        ]
        for r in reactors:
            db.add(r)
        
        # Storage Tank
        tank = StorageTank(tank_code="TK-OIL-01", name="Main Oil Storage", tank_type="STORAGE",
                           capacity_liters=Decimal("50000"), current_level_liters=Decimal("5000"), is_active=True)
        db.add(tank)
        
        db.commit()
        print("✅ Basic demo data seeded: 2 vendors, 2 customers, 3 products, 2 reactors, 1 tank")
    except Exception as e:
        print(f"⚠️ Error seeding demo data: {e}")
        db.rollback()
