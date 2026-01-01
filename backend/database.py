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
    
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")
