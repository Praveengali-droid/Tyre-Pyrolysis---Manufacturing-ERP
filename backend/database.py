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
            # First seed demo data (vendors, batches, sales)
            seed_demo_data()
            
            # Then create admin user (after demo data, so it's not wiped)
            print("🔐 Creating default admin user...")
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
        else:
            print(f"👥 Found {user_count} existing user(s)")
    except Exception as e:
        print(f"⚠️ Error seeding admin user: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def seed_demo_data():
    """
    Seed comprehensive demo data for fresh deployments.
    Creates vendors, batches, sales for reports to work.
    """
    print("🌱 Seeding demo data for reports...")
    try:
        # Run the seed script
        import subprocess
        import os
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(backend_dir, "scripts", "seed_realism.py")
        
        if os.path.exists(script_path):
            result = subprocess.run(
                ["python", script_path],  # No --wipe flag
                cwd=backend_dir,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("✅ Demo data seeded successfully!")
                print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
            else:
                print(f"⚠️ Seed script returned error: {result.stderr[:500]}")
        else:
            print(f"⚠️ Seed script not found at {script_path}")
    except Exception as e:
        print(f"⚠️ Error running seed script: {e}")


