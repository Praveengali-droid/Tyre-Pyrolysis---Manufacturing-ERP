# Master Architecture Document
## Tyre Pyrolysis Plant - 360° ERP System

**Version:** 3.0  
**Created:** December 31, 2025  
**Last Updated:** December 31, 2025  
**Author:** System Architect

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Technology Stack](#technology-stack)
3. [Data Schema](#data-schema)
4. [Modular Folder Structure](#modular-folder-structure)
5. [API Strategy](#api-strategy)
6. [Integration Points](#integration-points)
7. [Sustainability Principles](#sustainability-principles)
8. [Getting Started](#getting-started)

---

## Executive Summary

This document defines the complete architecture for a **360-degree ERP system** tailored to a tyre pyrolysis manufacturing plant. The system covers:

- **Procurement** - Vendor management, purchase orders, scrap tyre sourcing
- **Inventory** - Raw material tracking, byproduct storage, **Tank Farm management**
- **Production** - Batch processing, reactor monitoring, yield tracking, **utilities costing**
- **Secondary Processing** - Carbon grinding, stock conversion
- **Sales** - Customer management, byproduct sales (Oil, Steel, Carbon Black)

> [!IMPORTANT]
> This architecture prioritizes **low cost**, **minimal dependencies**, and **ease of maintenance** for a non-technical user.

---

## Technology Stack

### Recommended Stack (Low-Cost & Beginner-Friendly)

| Layer | Technology | Why This Choice |
|-------|------------|-----------------|
| **Backend** | Python 3.11+ with FastAPI | Simple syntax, excellent documentation, auto-generates API docs |
| **Database** | SQLite (Development) → PostgreSQL (Production) | SQLite is file-based (no setup). Free-tier PostgreSQL on Supabase/Neon/Railway for production |
| **Frontend** | Vue 3 with Composition API | Simpler learning curve than React, single-file components |
| **Authentication** | Simple JWT tokens | No external auth service needed |
| **Deployment** | Railway.app or Render.com | Free tiers available, simple deployment from Git |

### Alternative Options

```
┌─────────────────────────────────────────────────────────────┐
│  SIMPLER OPTION (If Vue feels complex):                    │
│  • Use plain HTML + Alpine.js + Tailwind CSS               │
│  • Server-rendered templates with Jinja2                   │
│  • No build step required                                  │
└─────────────────────────────────────────────────────────────┘
```

### Core Dependencies (Minimal)

```text
# Backend (requirements.txt)
fastapi==0.109.0      # Web framework
uvicorn==0.27.0       # ASGI server
sqlalchemy==2.0.25    # Database ORM
pydantic==2.5.3       # Data validation
python-jose==3.3.0    # JWT authentication
passlib==1.7.4        # Password hashing
python-multipart==0.0.6  # Form data handling

# Total: 7 dependencies (intentionally minimal)
```

---

## Data Schema

### Entity Relationship Diagram

```mermaid
erDiagram
    VENDOR ||--o{ PURCHASE_ORDER : supplies
    PURCHASE_ORDER ||--|{ GOODS_RECEIPT_NOTE : receives
    GOODS_RECEIPT_NOTE }|--|| WEIGHBRIDGE_RECORD : links_to
    RAW_MATERIAL ||--o{ GOODS_RECEIPT_NOTE : received_as
    RAW_MATERIAL ||--o{ PRODUCTION_BATCH : feeds_into
    PRODUCTION_BATCH ||--|{ BATCH_BYPRODUCT : produces
    BATCH_BYPRODUCT }|--|| BYPRODUCT : records_output_of
    BATCH_BYPRODUCT }o--|| STORAGE_TANK : stored_in
    STORAGE_TANK ||--o{ TANK_TRANSFER : source_of
    STORAGE_TANK ||--o{ TANK_TRANSFER : destination_of
    BYPRODUCT ||--o{ PROCESSING_JOB : input_to
    PROCESSING_JOB ||--o{ BYPRODUCT : produces
    BYPRODUCT ||--o{ SALES_ORDER_ITEM : sold_as
    CUSTOMER ||--o{ SALES_ORDER : places
    SALES_ORDER ||--|{ SALES_ORDER_ITEM : contains
    REACTOR ||--o{ PRODUCTION_BATCH : processes
    REACTOR ||--o{ MAINTENANCE_LOG : requires
```

### Table Definitions

#### 1. Vendors Table
Tracks domestic and international suppliers of scrap tyres with **Indian GST and EPR compliance**.

> [!IMPORTANT]
> **EPR Compliance**: Extended Producer Responsibility (EPR) is mandatory for waste tyre processors in India. Track vendor's EPC license to ensure legal sourcing.

```sql
CREATE TABLE vendors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_code VARCHAR(20) UNIQUE NOT NULL,      -- e.g., "VND-DOM-001"
    name VARCHAR(100) NOT NULL,
    vendor_type VARCHAR(20) NOT NULL,             -- 'DOMESTIC' or 'INTERNATIONAL'
    
    -- Contact Information
    contact_person VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(100),
    
    -- Address
    address_line1 VARCHAR(200),
    address_line2 VARCHAR(200),
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100) DEFAULT 'India',
    pincode VARCHAR(10),
    
    -- Indian GST Compliance
    gst_number VARCHAR(20),                       -- GSTIN for domestic vendors
    gst_vendor_type VARCHAR(30),                  -- 'REGULAR', 'COMPOSITION', 'UNREGISTERED', 'SEZ'
    pan_number VARCHAR(15),
    
    -- EPR Compliance (Extended Producer Responsibility)
    epc_license_number VARCHAR(30),               -- EPC Authorization from CPCB/SPCB
    epc_validity_date DATE,                       -- Expiry date of EPC license
    is_epr_compliant BOOLEAN DEFAULT FALSE,       -- Quick filter for compliant vendors
    
    -- Banking
    bank_account_number VARCHAR(30),
    bank_ifsc_code VARCHAR(15),
    
    -- For International Vendors
    import_export_code VARCHAR(20),               -- IEC for international
    currency VARCHAR(3) DEFAULT 'INR',            -- 'INR', 'USD', 'EUR'
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    rating INTEGER CHECK(rating >= 1 AND rating <= 5),
    notes TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. Raw Materials Table
Tracks scrap tyres inventory (primary input material) with **HSN codes for GST invoicing**.

```sql
CREATE TABLE raw_materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    material_code VARCHAR(20) UNIQUE NOT NULL,    -- e.g., "RM-SCRAP-001"
    name VARCHAR(100) NOT NULL,                   -- e.g., "Truck Tyre Scrap"
    material_type VARCHAR(50) NOT NULL,           -- 'TRUCK_TYRE', 'CAR_TYRE', 'TWO_WHEELER', 'OTR'
    
    -- Indian GST/HSN Compliance
    hsn_code VARCHAR(10) NOT NULL,                -- HSN 4004 (Waste Rubber) or 4012 (Retreaded Tyres)
    gst_rate DECIMAL(4,2) DEFAULT 5.00,           -- GST rate percentage (typically 5% or 18%)
    
    -- Inventory
    current_stock_kg DECIMAL(12,2) DEFAULT 0,
    minimum_stock_kg DECIMAL(12,2) DEFAULT 0,     -- Reorder level
    
    -- Quality Parameters
    average_rubber_content DECIMAL(5,2),          -- Percentage
    average_steel_content DECIMAL(5,2),           -- Percentage
    average_carbon_content DECIMAL(5,2),          -- Percentage (for yield estimation)
    moisture_content_max DECIMAL(5,2),            -- Maximum acceptable moisture %
    
    -- Pricing
    standard_rate_per_kg DECIMAL(10,2),
    
    -- Location
    storage_location VARCHAR(50),                 -- Warehouse/Yard section
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Common HSN Codes Reference:
-- 4004: Waste, parings and scrap of rubber (waste tyres)
-- 4012: Retreaded or used pneumatic tyres
-- 40040000: Waste/scrap rubber (more specific)
```

#### 3. Production Batches Table
Tracks each reactor feed/production run with **pyrolysis phase tracking and mass balance**.

> [!NOTE]
> **Pyrolysis Process Phases**: A typical batch goes through HEATING → DISTILLATION → COOLING phases. Each phase has distinct temperature profiles and durations that affect yield quality.

```sql
CREATE TABLE production_batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_number VARCHAR(30) UNIQUE NOT NULL,     -- e.g., "BATCH-2025-001"
    
    -- Reactor Reference
    reactor_id INTEGER REFERENCES reactors(id),   -- Link to specific reactor
    
    -- Timing
    start_datetime TIMESTAMP,
    end_datetime TIMESTAMP,
    
    -- Pyrolysis Phase Status (reflects actual reactor operation)
    status VARCHAR(20) DEFAULT 'PLANNED',         
    -- Status Enum:
    -- 'PLANNED'      - Batch created, awaiting loading
    -- 'LOADING'      - Raw material being fed into reactor
    -- 'HEATING'      - Reactor heating up (typically 30-60 mins to reach 350°C)
    -- 'DISTILLATION' - Active pyrolysis at 400-500°C (main production phase)
    -- 'COOLING'      - Cooling down post-reaction (2-4 hours)
    -- 'UNLOADING'    - Removing char/carbon black
    -- 'COMPLETED'    - Batch fully processed, all outputs recorded
    -- 'ABORTED'      - Emergency stop or failure
    
    phase_start_time TIMESTAMP,                   -- When current phase started
    heating_duration_mins INTEGER,                -- Actual heating phase duration
    distillation_duration_mins INTEGER,           -- Actual distillation phase duration
    cooling_duration_mins INTEGER,                -- Actual cooling phase duration
    
    -- Input
    raw_material_id INTEGER REFERENCES raw_materials(id),
    input_weight_kg DECIMAL(12,2) NOT NULL,       -- Scrap tyres fed into reactor
    
    -- Reactor Parameters
    target_temperature_celsius INTEGER DEFAULT 450,
    peak_temperature_celsius INTEGER,             -- Highest temp recorded
    avg_distillation_temp_celsius INTEGER,        -- Average during distillation
    pressure_bar DECIMAL(5,2),                    -- Reactor pressure
    
    -- ═══════════════════════════════════════════════════════════
    -- UTILITIES COSTING (Critical for true cost calculation)
    -- ═══════════════════════════════════════════════════════════
    electricity_meter_start DECIMAL(12,2),        -- kWh reading at batch start
    electricity_meter_end DECIMAL(12,2),          -- kWh reading at batch end
    electricity_consumed_kwh DECIMAL(12,2),       -- Auto: end - start
    electricity_rate_per_kwh DECIMAL(8,2),        -- Rate at time of batch (₹/kWh)
    electricity_cost DECIMAL(12,2),               -- Auto: consumed * rate
    
    fuel_consumed_litres DECIMAL(10,2),           -- If using diesel/furnace oil for startup
    fuel_cost DECIMAL(10,2),
    
    labor_hours DECIMAL(6,2),                     -- Total labor hours for batch
    labor_cost DECIMAL(10,2),
    
    total_batch_cost DECIMAL(12,2),               -- electricity + fuel + labor
    cost_per_kg_oil DECIMAL(8,2),                 -- total_cost / oil_output_kg
    
    -- ═══════════════════════════════════════════════════════════
    -- MASS BALANCE TRACKING (Critical for yield analysis)
    -- ═══════════════════════════════════════════════════════════
    -- Output quantities (collected from batch_byproducts table)
    oil_output_kg DECIMAL(12,2) DEFAULT 0,        -- Pyrolysis oil produced
    carbon_black_output_kg DECIMAL(12,2) DEFAULT 0, -- Carbon black/char
    steel_wire_output_kg DECIMAL(12,2) DEFAULT 0, -- Extracted steel
    
    -- Calculated fields (updated on batch completion)
    total_solid_output_kg DECIMAL(12,2),          -- carbon_black + steel_wire
    total_liquid_output_kg DECIMAL(12,2),         -- oil (may add water later)
    total_output_weight_kg DECIMAL(12,2),         -- Sum of all measurable outputs
    
    -- Syn-Gas Loss (Non-condensable gases consumed internally or flared)
    -- Formula: syn_gas_loss_kg = input_weight_kg - total_output_weight_kg
    syn_gas_loss_kg DECIMAL(12,2),                -- Calculated: Input - All Outputs
    syn_gas_loss_percentage DECIMAL(5,2),         -- (syn_gas_loss / input) * 100
    
    -- Yield Percentages
    oil_yield_percentage DECIMAL(5,2),            -- (oil / input) * 100
    carbon_yield_percentage DECIMAL(5,2),         -- (carbon / input) * 100
    steel_yield_percentage DECIMAL(5,2),          -- (steel / input) * 100
    overall_yield_percentage DECIMAL(5,2),        -- (total_output / input) * 100
    
    -- Quality Check
    quality_grade VARCHAR(10),                    -- 'A', 'B', 'C' based on yield & quality
    quality_notes TEXT,
    
    -- Operator
    operator_name VARCHAR(100),
    shift VARCHAR(20),                            -- 'MORNING', 'AFTERNOON', 'NIGHT'
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trigger or Application Logic to calculate:
-- electricity_consumed_kwh = electricity_meter_end - electricity_meter_start
-- electricity_cost = electricity_consumed_kwh * electricity_rate_per_kwh
-- total_batch_cost = electricity_cost + fuel_cost + labor_cost
-- cost_per_kg_oil = total_batch_cost / oil_output_kg
-- syn_gas_loss_kg = input_weight_kg - total_output_weight_kg
```

#### 4. Byproducts Table
Tracks outputs from pyrolysis with **HSN codes and industry-standard quality parameters**.

> [!NOTE]
> **Byproduct Types**: 
> - **Pyrolysis Oil** (TDO - Tyre Derived Oil): ~40-45% yield, used as furnace fuel
> - **Carbon Black** (Char): ~30-35% yield, used in rubber/plastic industry
> - **Steel Wire**: ~10-15% yield, sold as scrap
> - **Syn-Gas**: ~10-15% (consumed internally for heating reactor)

```sql
CREATE TABLE byproducts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    byproduct_code VARCHAR(20) UNIQUE NOT NULL,   -- e.g., "BP-OIL-001"
    
    -- Classification
    byproduct_type VARCHAR(30) NOT NULL,          
    -- Enum: 'PYROLYSIS_OIL', 'CARBON_BLACK', 'STEEL_WIRE', 'WASTE'
    name VARCHAR(100) NOT NULL,
    
    -- Indian GST/HSN Compliance
    hsn_code VARCHAR(10) NOT NULL,                -- See HSN reference below
    gst_rate DECIMAL(4,2) DEFAULT 18.00,          -- GST rate percentage
    
    -- Inventory
    current_stock DECIMAL(12,2) DEFAULT 0,
    unit_of_measure VARCHAR(20) NOT NULL,         -- 'KG', 'LITRE', 'MT' (Metric Ton)
    minimum_stock DECIMAL(12,2) DEFAULT 0,
    
    -- ═══════════════════════════════════════════════════════════
    -- QUALITY PARAMETERS BY BYPRODUCT TYPE
    -- ═══════════════════════════════════════════════════════════
    
    -- Common
    quality_grade VARCHAR(10),                    -- 'A', 'B', 'C' (plant-specific grading)
    
    -- FOR PYROLYSIS OIL (TDO - Tyre Derived Oil)
    density_kg_per_litre DECIMAL(6,4),            -- Typically 0.85-0.95 kg/L
    viscosity_cst DECIMAL(8,2),                   -- Kinematic viscosity in centistokes (cSt)
    flash_point_celsius INTEGER,                  -- Min 40-60°C (safety critical!)
    pour_point_celsius INTEGER,                   -- Lowest temp oil can flow
    calorific_value_mj_kg DECIMAL(10,2),          -- Gross Calorific Value (MJ/kg), typically 40-44
    sulphur_content_pct DECIMAL(5,3),             -- Sulphur % (important for emissions)
    water_content_pct DECIMAL(5,2),               -- Water contamination %
    ash_content_oil_pct DECIMAL(5,3),             -- Ash content in oil %
    
    -- FOR CARBON BLACK (Pyrolysis Char)
    mesh_size VARCHAR(20),                        -- Particle size: '200 mesh', '325 mesh' etc.
    ash_content_pct DECIMAL(5,2),                 -- Ash content % (lower is better, <15% ideal)
    volatile_matter_pct DECIMAL(5,2),             -- Volatile matter %
    fixed_carbon_pct DECIMAL(5,2),                -- Fixed carbon content % (higher is better)
    moisture_content_pct DECIMAL(5,2),            -- Moisture %
    iodine_absorption DECIMAL(8,2),               -- Iodine number (mg/g) - indicates surface area
    
    -- FOR STEEL WIRE
    steel_purity DECIMAL(5,2),                    -- Steel content % (after cleaning)
    rubber_contamination_pct DECIMAL(5,2),        -- Residual rubber attached
    wire_type VARCHAR(30),                        -- 'BEAD_WIRE', 'BELT_WIRE', 'MIXED'
    
    -- Pricing
    selling_rate_per_unit DECIMAL(10,2),
    
    -- Storage
    storage_location VARCHAR(50),
    storage_conditions TEXT,                      -- e.g., "Keep away from ignition sources"
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- HSN Codes Reference for Byproducts:
-- 2710.19.90 : Pyrolysis Oil / Furnace Oil (Petroleum-like products)
-- 2803.00.10 : Carbon Black
-- 7204.49.00 : Ferrous waste/scrap (Steel wire)
-- 3915.90.00 : Waste plastics (if any)
```

#### 5. Byproduct Production Records
Links batches to their outputs with **batch-specific quality measurements and tank destination**.

```sql
CREATE TABLE batch_byproducts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id INTEGER REFERENCES production_batches(id) ON DELETE CASCADE,
    byproduct_id INTEGER REFERENCES byproducts(id),
    
    quantity_produced DECIMAL(12,2) NOT NULL,
    unit_of_measure VARCHAR(20) NOT NULL,
    
    -- Quality for this specific batch output
    quality_grade VARCHAR(10),
    quality_notes TEXT,
    
    -- Batch-specific quality readings (overrides byproduct defaults)
    -- For Oil batches
    batch_density DECIMAL(6,4),
    batch_flash_point INTEGER,
    batch_calorific_value DECIMAL(10,2),
    
    -- For Carbon Black batches  
    batch_ash_content DECIMAL(5,2),
    batch_mesh_size VARCHAR(20),
    
    -- Storage Destination (Tank Farm Integration)
    destination_tank_id INTEGER REFERENCES storage_tanks(id),  -- Which tank/silo it went into
    destination_silo_id INTEGER,                  -- For carbon black storage
    collection_datetime TIMESTAMP,                -- When this output was collected
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 6. Reactors Table
Tracks individual pyrolysis reactors/vessels.

```sql
CREATE TABLE reactors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reactor_code VARCHAR(20) UNIQUE NOT NULL,     -- e.g., "REACTOR-01"
    name VARCHAR(100) NOT NULL,                   -- e.g., "Main Reactor Unit 1"
    
    -- Specifications
    capacity_kg INTEGER NOT NULL,                 -- Max batch size in kg
    reactor_type VARCHAR(30),                     -- 'BATCH', 'CONTINUOUS', 'ROTARY'
    manufacturer VARCHAR(100),
    installation_date DATE,
    
    -- Operating Parameters
    max_temperature_celsius INTEGER DEFAULT 550,
    max_pressure_bar DECIMAL(5,2) DEFAULT 2.0,
    typical_cycle_hours DECIMAL(5,2) DEFAULT 8,   -- Typical batch cycle time
    
    -- Status
    status VARCHAR(20) DEFAULT 'OPERATIONAL',     -- 'OPERATIONAL', 'MAINTENANCE', 'OUT_OF_SERVICE'
    last_maintenance_date DATE,
    next_maintenance_due DATE,
    total_batches_processed INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 7. Maintenance Logs Table
Tracks reactor maintenance and cleaning schedules **(safety-critical)**.

> [!CAUTION]
> **Safety Requirement**: Reactors must be cleaned regularly to prevent carbon buildup which can cause fires and reduce efficiency. This table helps track compliance with safety protocols.

```sql
CREATE TABLE maintenance_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    maintenance_code VARCHAR(30) UNIQUE NOT NULL, -- e.g., "MAINT-2025-001"
    
    reactor_id INTEGER REFERENCES reactors(id) NOT NULL,
    
    -- Maintenance Type
    maintenance_type VARCHAR(30) NOT NULL,        
    -- Types: 'REACTOR_CLEANING', 'CONDENSER_CLEANING', 'SEAL_REPLACEMENT', 
    --        'INSPECTION', 'SAFETY_AUDIT', 'OIL_TANK_CLEANING', 'OTHER'
    
    -- Scheduling
    scheduled_date DATE NOT NULL,
    actual_start_datetime TIMESTAMP,
    actual_end_datetime TIMESTAMP,
    status VARCHAR(20) DEFAULT 'SCHEDULED',       -- 'SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'OVERDUE', 'CANCELLED'
    
    -- Details
    description TEXT,
    findings TEXT,                                -- What was found during maintenance
    actions_taken TEXT,                           -- What repairs/cleaning was done
    parts_replaced TEXT,                          -- Any parts that were replaced
    
    -- Downtime Tracking
    downtime_hours DECIMAL(6,2),                  -- Hours reactor was offline
    batches_missed INTEGER DEFAULT 0,             -- Estimated batches that could not run
    
    -- Cost
    labor_cost DECIMAL(10,2) DEFAULT 0,
    parts_cost DECIMAL(10,2) DEFAULT 0,
    total_cost DECIMAL(10,2),                     -- labor + parts
    
    -- Personnel
    technician_name VARCHAR(100),
    supervisor_name VARCHAR(100),
    
    -- Next Maintenance
    next_maintenance_due DATE,                    -- Auto-schedule next cleaning
    
    -- Attachments (paths to photos/documents)
    photo_before VARCHAR(200),
    photo_after VARCHAR(200),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Maintenance Schedule Templates (for recurring maintenance)
CREATE TABLE maintenance_schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reactor_id INTEGER REFERENCES reactors(id) NOT NULL,
    maintenance_type VARCHAR(30) NOT NULL,
    frequency_days INTEGER NOT NULL,              -- Every X days
    last_performed DATE,
    next_due DATE,
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Common Maintenance Frequencies:
-- Reactor Cleaning: Every 30-45 days or after 50 batches
-- Condenser Cleaning: Every 15-20 days
-- Seal Inspection: Every 60 days
-- Safety Audit: Every 90 days
```

---

### Tank Farm & Secondary Processing Tables

#### 8. Storage Tanks Table (Tank Farm Management)
Tracks oil storage tanks and their current levels for **liquid inventory management**.

> [!NOTE]
> **Tank Farm Operations**: Pyrolysis oil is collected in settling tanks first, then transferred to storage tanks. Water separation and blending operations require accurate tank level tracking.

```sql
CREATE TABLE storage_tanks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tank_code VARCHAR(20) UNIQUE NOT NULL,        -- e.g., "TANK-OIL-01"
    name VARCHAR(100) NOT NULL,                   -- e.g., "Primary Oil Storage Tank 1"
    
    -- Tank Specifications
    tank_type VARCHAR(30) NOT NULL,               
    -- Types: 'OIL_SETTLING', 'OIL_STORAGE', 'OIL_DISPATCH', 'WATER_COLLECTION', 'SILO_CARBON'
    material_type VARCHAR(30),                    -- 'PYROLYSIS_OIL', 'CARBON_BLACK', 'WATER'
    
    capacity_litres DECIMAL(12,2) NOT NULL,       -- Maximum capacity
    current_level_litres DECIMAL(12,2) DEFAULT 0, -- Current fill level
    available_capacity_litres DECIMAL(12,2),      -- Auto: capacity - current_level
    fill_percentage DECIMAL(5,2),                 -- Auto: (current / capacity) * 100
    
    -- Thresholds
    min_level_litres DECIMAL(12,2) DEFAULT 0,     -- Alert when below this
    max_safe_level_litres DECIMAL(12,2),          -- Alert when above this (overflow risk)
    
    -- Physical Location
    location VARCHAR(100),                        -- e.g., "Tank Farm Area A"
    
    -- Last Activity
    last_inflow_datetime TIMESTAMP,
    last_outflow_datetime TIMESTAMP,
    last_dip_reading_datetime TIMESTAMP,          -- Manual level check
    
    -- Status
    status VARCHAR(20) DEFAULT 'ACTIVE',          -- 'ACTIVE', 'CLEANING', 'MAINTENANCE', 'OFFLINE'
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 9. Tank Transfers Table
Logs all oil movements between tanks for **blending, settling, and dispatch tracking**.

```sql
CREATE TABLE tank_transfers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transfer_code VARCHAR(30) UNIQUE NOT NULL,    -- e.g., "TRF-2025-001"
    
    -- Source & Destination
    source_tank_id INTEGER REFERENCES storage_tanks(id),
    destination_tank_id INTEGER REFERENCES storage_tanks(id),
    
    -- Transfer Details
    transfer_type VARCHAR(30) NOT NULL,           
    -- Types: 'SETTLING_TO_STORAGE', 'BLENDING', 'WATER_SEPARATION', 
    --        'DISPATCH_LOADING', 'TANK_TO_TANK', 'QUALITY_REJECTION'
    
    quantity_litres DECIMAL(12,2) NOT NULL,
    transfer_datetime TIMESTAMP NOT NULL,
    
    -- Quality at Transfer
    density_at_transfer DECIMAL(6,4),
    water_content_pct DECIMAL(5,2),               -- If water separation
    
    -- For Water Separation
    water_separated_litres DECIMAL(10,2),         -- Amount of water removed
    settled_oil_litres DECIMAL(12,2),             -- Clean oil after settling
    
    -- For Blending
    blending_notes TEXT,                          -- What was blended and why
    
    -- Operator
    operator_name VARCHAR(100),
    
    -- Status
    status VARCHAR(20) DEFAULT 'COMPLETED',       -- 'PENDING', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED'
    remarks TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trigger: Update source_tank.current_level -= quantity_litres
-- Trigger: Update destination_tank.current_level += quantity_litres (or settled_oil_litres)
```

#### 10. Processing Jobs Table (Secondary Processing - Carbon Grinding)
Tracks conversion of raw **Carbon Char → Carbon Black Powder**.

> [!IMPORTANT]
> **Stock Conversion**: This table tracks the transformation of raw carbon char (as-is from reactor) into commercial-grade carbon black powder through grinding. It captures electricity/labor costs for true cost calculation.

```sql
CREATE TABLE processing_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_code VARCHAR(30) UNIQUE NOT NULL,         -- e.g., "GRIND-2025-001"
    
    -- Job Type
    job_type VARCHAR(30) NOT NULL,                
    -- Types: 'CARBON_GRINDING', 'CARBON_SIEVING', 'OIL_FILTERING', 'STEEL_CLEANING'
    
    -- Input Material
    input_byproduct_id INTEGER REFERENCES byproducts(id),  -- Raw carbon char
    input_batch_id INTEGER REFERENCES production_batches(id), -- Optional: link to specific batch
    input_quantity_kg DECIMAL(12,2) NOT NULL,
    input_source VARCHAR(50),                     -- 'BATCH' or 'INVENTORY'
    
    -- Output Material (after processing)
    output_byproduct_id INTEGER REFERENCES byproducts(id), -- Carbon black powder
    output_quantity_kg DECIMAL(12,2),             -- Actual output (less than input due to loss)
    output_mesh_size VARCHAR(20),                 -- e.g., '200 mesh', '325 mesh'
    
    -- Yield/Loss
    processing_loss_kg DECIMAL(10,2),             -- Input - Output
    processing_loss_pct DECIMAL(5,2),             -- (loss / input) * 100
    
    -- Timing
    start_datetime TIMESTAMP,
    end_datetime TIMESTAMP,
    processing_hours DECIMAL(6,2),
    status VARCHAR(20) DEFAULT 'PLANNED',         -- 'PLANNED', 'IN_PROGRESS', 'COMPLETED', 'FAILED'
    
    -- ═══════════════════════════════════════════════════════════
    -- COST TRACKING (for true cost of finished carbon black)
    -- ═══════════════════════════════════════════════════════════
    electricity_meter_start DECIMAL(12,2),
    electricity_meter_end DECIMAL(12,2),
    electricity_consumed_kwh DECIMAL(10,2),
    electricity_rate_per_kwh DECIMAL(8,2),
    electricity_cost DECIMAL(10,2),
    
    labor_hours DECIMAL(6,2),
    labor_rate_per_hour DECIMAL(8,2),
    labor_cost DECIMAL(10,2),
    
    consumables_cost DECIMAL(10,2),               -- Grinding media, screens, etc.
    
    total_processing_cost DECIMAL(12,2),          -- electricity + labor + consumables
    cost_per_kg_output DECIMAL(8,2),              -- total_cost / output_quantity_kg
    
    -- Equipment
    equipment_id VARCHAR(30),                     -- Which grinder/mill was used
    
    -- Quality
    quality_grade VARCHAR(10),
    quality_notes TEXT,
    
    -- Operator
    operator_name VARCHAR(100),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Stock Conversion Logic:
-- On completion:
--   Decrease raw_carbon_char.current_stock -= input_quantity_kg
--   Increase carbon_black_powder.current_stock += output_quantity_kg
```

---

### Procurement & Goods Receipt Tables

#### 11. Goods Receipt Notes (GRN) Table
Tracks actual receipt of materials with **quality deductions for Mud, Water, Rims, etc.**

> [!WARNING]
> **Procurement Deductions**: Scrap tyre loads often contain mud, water, or steel rims that must be deducted from payable weight. This table captures these deductions with full traceability.

```sql
CREATE TABLE goods_receipt_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    grn_number VARCHAR(30) UNIQUE NOT NULL,       -- e.g., "GRN-2025-001"
    
    -- Purchase Order Reference
    purchase_order_id INTEGER REFERENCES purchase_orders(id),
    vendor_id INTEGER REFERENCES vendors(id),
    
    -- Weighbridge Link
    weighbridge_record_id INTEGER REFERENCES weighbridge_records(id),
    
    -- Receipt Details
    receipt_date DATE NOT NULL,
    receipt_datetime TIMESTAMP NOT NULL,
    
    -- Material
    raw_material_id INTEGER REFERENCES raw_materials(id),
    material_description TEXT,
    
    -- Weights from Weighbridge
    gross_weight_kg DECIMAL(12,2) NOT NULL,
    tare_weight_kg DECIMAL(12,2) NOT NULL,
    net_weight_kg DECIMAL(12,2) NOT NULL,         -- gross - tare
    
    -- ═══════════════════════════════════════════════════════════
    -- PROCUREMENT DEDUCTIONS (Critical for accurate costing)
    -- ═══════════════════════════════════════════════════════════
    deduction_1_type VARCHAR(30),                 -- 'MUD', 'WATER', 'RIMS', 'SAND', 'FOREIGN_MATERIAL'
    deduction_1_weight_kg DECIMAL(10,2) DEFAULT 0,
    deduction_1_reason TEXT,
    
    deduction_2_type VARCHAR(30),
    deduction_2_weight_kg DECIMAL(10,2) DEFAULT 0,
    deduction_2_reason TEXT,
    
    deduction_3_type VARCHAR(30),
    deduction_3_weight_kg DECIMAL(10,2) DEFAULT 0,
    deduction_3_reason TEXT,
    
    total_deduction_kg DECIMAL(12,2) DEFAULT 0,   -- Sum of all deductions
    
    -- Net Payable Weight
    net_payable_weight_kg DECIMAL(12,2),          -- net_weight - total_deduction
    
    -- Rate & Amount
    rate_per_kg DECIMAL(10,2),
    gross_amount DECIMAL(14,2),                   -- net_payable_weight * rate
    cgst_amount DECIMAL(12,2),
    sgst_amount DECIMAL(12,2),
    igst_amount DECIMAL(12,2),
    tds_amount DECIMAL(12,2) DEFAULT 0,           -- TDS if applicable
    net_payable_amount DECIMAL(14,2),             -- gross + GST - TDS
    
    -- Quality Assessment
    moisture_content_pct DECIMAL(5,2),
    quality_grade VARCHAR(10),
    quality_remarks TEXT,
    
    -- Inspection
    inspected_by VARCHAR(100),
    inspection_photos TEXT,                       -- Comma-separated photo paths
    
    -- Approval
    status VARCHAR(20) DEFAULT 'DRAFT',           -- 'DRAFT', 'INSPECTED', 'APPROVED', 'REJECTED', 'PAID'
    approved_by VARCHAR(100),
    approved_datetime TIMESTAMP,
    
    -- Notes
    vendor_slip_number VARCHAR(50),               -- Vendor's delivery slip reference
    remarks TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Calculation Logic:
-- total_deduction_kg = deduction_1_weight_kg + deduction_2_weight_kg + deduction_3_weight_kg
-- net_payable_weight_kg = net_weight_kg - total_deduction_kg
-- gross_amount = net_payable_weight_kg * rate_per_kg
```

---

#### 12. Supporting Tables

```sql
-- Customers (for byproduct sales)
CREATE TABLE customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    customer_type VARCHAR(20),                    -- 'WHOLESALER', 'MANUFACTURER', 'TRADER'
    contact_person VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(100),
    gst_number VARCHAR(20),
    pan_number VARCHAR(15),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    pincode VARCHAR(10),
    credit_limit DECIMAL(12,2) DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Purchase Orders (from vendors)
CREATE TABLE purchase_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    po_number VARCHAR(30) UNIQUE NOT NULL,
    vendor_id INTEGER REFERENCES vendors(id),
    order_date DATE NOT NULL,
    expected_delivery_date DATE,
    status VARCHAR(20) DEFAULT 'DRAFT',           -- 'DRAFT', 'CONFIRMED', 'RECEIVED', 'CANCELLED'
    total_amount DECIMAL(14,2),
    cgst_amount DECIMAL(12,2),                    -- Central GST
    sgst_amount DECIMAL(12,2),                    -- State GST
    igst_amount DECIMAL(12,2),                    -- Integrated GST (inter-state)
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sales Orders (to customers)
CREATE TABLE sales_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    so_number VARCHAR(30) UNIQUE NOT NULL,
    customer_id INTEGER REFERENCES customers(id),
    order_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'DRAFT',           -- 'DRAFT', 'CONFIRMED', 'DISPATCHED', 'DELIVERED', 'CANCELLED'
    total_amount DECIMAL(14,2),
    cgst_amount DECIMAL(12,2),
    sgst_amount DECIMAL(12,2),
    igst_amount DECIMAL(12,2),
    payment_status VARCHAR(20) DEFAULT 'PENDING', -- 'PENDING', 'PARTIAL', 'PAID'
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Weighbridge Records (for integration)
CREATE TABLE weighbridge_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_number VARCHAR(30) UNIQUE NOT NULL,
    vehicle_number VARCHAR(20) NOT NULL,
    driver_name VARCHAR(100),
    driver_phone VARCHAR(20),
    
    gross_weight_kg DECIMAL(12,2),
    tare_weight_kg DECIMAL(12,2),
    net_weight_kg DECIMAL(12,2),                  -- Auto: gross - tare
    
    -- Preliminary Deductions (can be detailed in GRN)
    estimated_deduction_kg DECIMAL(10,2) DEFAULT 0,
    deduction_reason VARCHAR(100),                -- Quick note: 'Muddy load', 'Wet tyres'
    
    weighment_type VARCHAR(20),                   -- 'INWARD' or 'OUTWARD'
    material_type VARCHAR(50),                    -- What's being weighed
    first_weight_datetime TIMESTAMP,
    second_weight_datetime TIMESTAMP,
    
    -- Link to PO or SO
    reference_type VARCHAR(20),                   -- 'PURCHASE_ORDER' or 'SALES_ORDER'
    reference_id INTEGER,
    
    operator_name VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Modular Folder Structure

```
tyre-pyrolysis-erp/
│
├── docs/
│   ├── architecture.md          # This document
│   ├── api-reference.md         # API documentation
│   ├── user-guide.md            # End-user manual
│   └── safety-protocols.md      # Maintenance & safety SOPs
│
├── backend/
│   ├── main.py                  # FastAPI app entry point
│   ├── config.py                # Environment configuration
│   ├── database.py              # Database connection setup
│   │
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── vendor.py
│   │   ├── raw_material.py
│   │   ├── production.py        # Includes Reactor model
│   │   ├── byproduct.py
│   │   ├── customer.py
│   │   ├── tank_farm.py         # 🆕 V3: Storage tanks & transfers
│   │   ├── processing.py        # 🆕 V3: Secondary processing jobs
│   │   ├── grn.py               # 🆕 V3: Goods Receipt Notes
│   │   ├── maintenance.py
│   │   └── weighbridge.py
│   │
│   ├── schemas/                 # Pydantic request/response schemas
│   │   ├── __init__.py
│   │   ├── vendor.py
│   │   ├── raw_material.py
│   │   ├── production.py
│   │   ├── byproduct.py
│   │   ├── tank_farm.py         # 🆕 V3: Tank schemas
│   │   ├── processing.py        # 🆕 V3: Processing job schemas
│   │   ├── grn.py               # 🆕 V3: GRN schemas
│   │   ├── maintenance.py
│   │   └── common.py            # Shared schemas (pagination, etc.)
│   │
│   ├── modules/                 # Business logic modules
│   │   ├── __init__.py
│   │   │
│   │   ├── procurement/         # 📦 PROCUREMENT MODULE (incl. GRN)
│   │   │   ├── __init__.py
│   │   │   ├── router.py        # API routes for procurement
│   │   │   ├── service.py       # Business logic
│   │   │   ├── grn_service.py   # 🆕 V3: GRN with deductions
│   │   │   └── crud.py          # Database operations
│   │   │
│   │   ├── inventory/           # 📊 INVENTORY MODULE
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   └── crud.py
│   │   │
│   │   ├── tank_farm/           # 🛢️ TANK FARM MODULE (🆕 V3)
│   │   │   ├── __init__.py
│   │   │   ├── router.py        # Tank & transfer endpoints
│   │   │   ├── service.py       # Level calculations, alerts
│   │   │   └── crud.py
│   │   │
│   │   ├── production/          # 🏭 PRODUCTION MODULE
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   ├── crud.py
│   │   │   ├── mass_balance.py  # Mass balance calculations
│   │   │   └── costing.py       # 🆕 V3: Utilities cost calculation
│   │   │
│   │   ├── secondary_processing/ # ⚙️ SECONDARY PROCESSING MODULE (🆕 V3)
│   │   │   ├── __init__.py
│   │   │   ├── router.py        # Carbon grinding endpoints
│   │   │   ├── service.py       # Stock conversion logic
│   │   │   └── crud.py
│   │   │
│   │   ├── sales/               # 💰 SALES MODULE
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   └── crud.py
│   │   │
│   │   ├── maintenance/         # 🔧 MAINTENANCE MODULE
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── service.py       # Scheduling logic, alerts
│   │   │   └── crud.py
│   │   │
│   │   └── integrations/        # 🔌 EXTERNAL INTEGRATIONS
│   │       ├── __init__.py
│   │       ├── weighbridge.py   # Weighbridge API
│   │       └── gps_tracker.py   # GPS/Fleet tracking API
│   │
│   ├── utils/                   # Helper functions
│   │   ├── __init__.py
│   │   ├── auth.py              # JWT authentication
│   │   ├── helpers.py           # Date, number formatters
│   │   ├── validators.py        # Custom validation rules (GST, HSN, etc.)
│   │   ├── gst_utils.py         # GST calculation helpers
│   │   └── costing_utils.py     # 🆕 V3: Cost calculations
│   │
│   └── tests/                   # Unit tests
│       ├── __init__.py
│       ├── test_vendors.py
│       ├── test_production.py
│       ├── test_mass_balance.py
│       ├── test_tank_farm.py    # 🆕 V3: Tank tests
│       ├── test_processing.py   # 🆕 V3: Processing tests
│       ├── test_grn.py          # 🆕 V3: GRN tests
│       ├── test_maintenance.py
│       └── test_sales.py
│
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   │
│   ├── src/
│   │   ├── main.js              # Vue app entry
│   │   ├── App.vue              # Root component
│   │   ├── router.js            # Vue Router setup
│   │   │
│   │   ├── views/               # Page-level components
│   │   │   ├── Dashboard.vue    # Overview with alerts
│   │   │   ├── procurement/
│   │   │   │   ├── VendorList.vue
│   │   │   │   ├── VendorForm.vue    # EPR compliance fields
│   │   │   │   ├── PurchaseOrders.vue
│   │   │   │   └── GoodsReceipt.vue  # 🆕 V3: GRN with deductions
│   │   │   ├── inventory/
│   │   │   │   ├── RawMaterials.vue
│   │   │   │   └── Byproducts.vue
│   │   │   ├── tank_farm/            # 🆕 V3: TANK FARM VIEWS
│   │   │   │   ├── TankOverview.vue  # Visual tank levels
│   │   │   │   ├── TankTransfer.vue  # Record transfers
│   │   │   │   └── TankHistory.vue
│   │   │   ├── production/
│   │   │   │   ├── ReactorList.vue
│   │   │   │   ├── BatchList.vue
│   │   │   │   ├── BatchForm.vue     # Includes electricity readings
│   │   │   │   ├── MassBalanceReport.vue
│   │   │   │   └── CostAnalysis.vue  # 🆕 V3: Cost per kg oil
│   │   │   ├── secondary_processing/ # 🆕 V3: PROCESSING VIEWS
│   │   │   │   ├── GrindingJobs.vue
│   │   │   │   └── StockConversion.vue
│   │   │   ├── maintenance/
│   │   │   │   ├── MaintenanceCalendar.vue
│   │   │   │   ├── MaintenanceLog.vue
│   │   │   │   └── ScheduleForm.vue
│   │   │   └── sales/
│   │   │       ├── CustomerList.vue
│   │   │       └── SalesOrders.vue
│   │   │
│   │   ├── components/          # Reusable UI components
│   │   │   ├── DataTable.vue
│   │   │   ├── FormInput.vue
│   │   │   ├── Modal.vue
│   │   │   ├── Sidebar.vue
│   │   │   ├── AlertBanner.vue  # 🔧 NEW: Maintenance due alerts
│   │   │   └── BatchPhaseIndicator.vue  # 🔧 NEW: Shows HEATING/DISTILLATION/COOLING
│   │   │
│   │   ├── services/            # API calls
│   │   │   └── api.js
│   │   │
│   │   └── assets/
│   │       └── styles.css
│   │
│   └── public/
│       └── favicon.ico
│
├── scripts/
│   ├── seed_data.py             # Sample data loader
│   ├── backup_db.py             # Database backup script
│   └── maintenance_alerts.py    # 🔧 NEW: Cron job for maintenance reminders
│
├── .env.example                 # Environment variables template
├── .gitignore
├── requirements.txt             # Python dependencies
└── README.md                    # Project setup instructions
```

---

## API Strategy

### Base URL Pattern
```
http://localhost:8000/api/v1/{module}/{resource}
```

### Authentication
All endpoints (except `/api/v1/auth/*`) require JWT Bearer token:
```http
Authorization: Bearer <your_jwt_token>
```

### REST Endpoints by Module

#### 🔐 Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | User login, returns JWT |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| GET | `/api/v1/auth/me` | Get current user info |

---

#### 📦 Procurement Module

**Vendors**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/procurement/vendors` | List all vendors (paginated) |
| GET | `/api/v1/procurement/vendors/{id}` | Get vendor details |
| POST | `/api/v1/procurement/vendors` | Create new vendor |
| PUT | `/api/v1/procurement/vendors/{id}` | Update vendor |
| DELETE | `/api/v1/procurement/vendors/{id}` | Soft delete vendor |
| GET | `/api/v1/procurement/vendors/{id}/orders` | Get vendor's purchase history |

**Purchase Orders**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/procurement/purchase-orders` | List all POs |
| POST | `/api/v1/procurement/purchase-orders` | Create PO |
| PUT | `/api/v1/procurement/purchase-orders/{id}/confirm` | Confirm PO |
| PUT | `/api/v1/procurement/purchase-orders/{id}/receive` | Mark as received |

**Goods Receipt Notes (🆕 V3)**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/procurement/grn` | List all GRNs |
| GET | `/api/v1/procurement/grn/{id}` | Get GRN details |
| POST | `/api/v1/procurement/grn` | Create GRN with deductions |
| PUT | `/api/v1/procurement/grn/{id}/approve` | Approve GRN |
| GET | `/api/v1/procurement/grn/pending-payment` | GRNs awaiting payment |
| GET | `/api/v1/procurement/reports/deductions` | Deduction analysis report |

---

#### 📊 Inventory Module

**Raw Materials**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/inventory/raw-materials` | List raw materials |
| POST | `/api/v1/inventory/raw-materials` | Add new material type |
| PUT | `/api/v1/inventory/raw-materials/{id}/adjust` | Adjust stock |
| GET | `/api/v1/inventory/raw-materials/low-stock` | Materials below minimum |

**Byproducts**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/inventory/byproducts` | List byproducts |
| GET | `/api/v1/inventory/byproducts/stock-report` | Stock summary |
| PUT | `/api/v1/inventory/byproducts/{id}/adjust` | Adjust stock |

---

#### 🛢️ Tank Farm Module (� V3)

**Storage Tanks**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/tank-farm/tanks` | List all tanks with levels |
| GET | `/api/v1/tank-farm/tanks/{id}` | Get tank details |
| POST | `/api/v1/tank-farm/tanks` | Add new tank |
| PUT | `/api/v1/tank-farm/tanks/{id}/level` | Update tank level (dip reading) |
| GET | `/api/v1/tank-farm/tanks/alerts` | Tanks at critical levels |

**Tank Transfers**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/tank-farm/transfers` | List all transfers |
| POST | `/api/v1/tank-farm/transfers` | Record tank-to-tank transfer |
| POST | `/api/v1/tank-farm/transfers/water-separation` | Log water separation |
| POST | `/api/v1/tank-farm/transfers/blending` | Log blending operation |
| GET | `/api/v1/tank-farm/transfers/tank/{id}/history` | Transfer history for a tank |

---

#### �🏭 Production Module

**Reactors**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/production/reactors` | List all reactors |
| GET | `/api/v1/production/reactors/{id}` | Get reactor details |
| POST | `/api/v1/production/reactors` | Add new reactor |
| PUT | `/api/v1/production/reactors/{id}/status` | Update reactor status |

**Batches**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/production/batches` | List all batches |
| POST | `/api/v1/production/batches` | Create new batch (with electricity meter start) |
| PUT | `/api/v1/production/batches/{id}/start` | Start production (LOADING phase) |
| PUT | `/api/v1/production/batches/{id}/phase` | Update phase (HEATING → DISTILLATION → COOLING) |
| PUT | `/api/v1/production/batches/{id}/complete` | Complete with outputs & meter end reading |
| GET | `/api/v1/production/batches/{id}/byproducts` | Get batch outputs |
| GET | `/api/v1/production/batches/{id}/mass-balance` | Get mass balance report for batch |
| GET | `/api/v1/production/batches/{id}/costing` | Get cost breakdown (🆕 V3) |
| GET | `/api/v1/production/reports/daily` | Daily production report |
| GET | `/api/v1/production/reports/yield-analysis` | Yield analysis |
| GET | `/api/v1/production/reports/syn-gas-loss` | Syn-gas loss trends |
| GET | `/api/v1/production/reports/cost-per-kg` | Cost per kg oil trends (🆕 V3) |

---

#### ⚙️ Secondary Processing Module (🆕 V3)

**Processing Jobs (Carbon Grinding)**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/processing/jobs` | List all processing jobs |
| GET | `/api/v1/processing/jobs/{id}` | Get job details |
| POST | `/api/v1/processing/jobs` | Create new grinding job |
| PUT | `/api/v1/processing/jobs/{id}/start` | Start processing |
| PUT | `/api/v1/processing/jobs/{id}/complete` | Complete with output & meter reading |
| GET | `/api/v1/processing/reports/stock-conversion` | Input vs Output report |
| GET | `/api/v1/processing/reports/grinding-cost` | Cost per kg carbon black |

---

#### 💰 Sales Module

**Customers**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/sales/customers` | List customers |
| POST | `/api/v1/sales/customers` | Create customer |
| PUT | `/api/v1/sales/customers/{id}` | Update customer |

**Sales Orders**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/sales/orders` | List sales orders |
| POST | `/api/v1/sales/orders` | Create order |
| PUT | `/api/v1/sales/orders/{id}/dispatch` | Mark dispatched |
| PUT | `/api/v1/sales/orders/{id}/payment` | Record payment |

---

#### 🔧 Maintenance Module

**Maintenance Logs**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/maintenance/logs` | List all maintenance logs |
| GET | `/api/v1/maintenance/logs/{id}` | Get maintenance details |
| POST | `/api/v1/maintenance/logs` | Create maintenance record |
| PUT | `/api/v1/maintenance/logs/{id}/start` | Start maintenance |
| PUT | `/api/v1/maintenance/logs/{id}/complete` | Complete maintenance |
| GET | `/api/v1/maintenance/due` | Get overdue/upcoming maintenance |
| GET | `/api/v1/maintenance/reactor/{id}/history` | Maintenance history for reactor |

**Maintenance Schedules**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/maintenance/schedules` | List all schedules |
| POST | `/api/v1/maintenance/schedules` | Create recurring schedule |
| PUT | `/api/v1/maintenance/schedules/{id}` | Update schedule |
| DELETE | `/api/v1/maintenance/schedules/{id}` | Remove schedule |

---

#### 🔌 Integration APIs

**Weighbridge Integration**
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/integrations/weighbridge/record` | Receive weight data |
| GET | `/api/v1/integrations/weighbridge/pending` | Pending weighments |
| PUT | `/api/v1/integrations/weighbridge/{id}/link` | Link to PO/SO |

**GPS Tracker Integration**
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/integrations/gps/location` | Receive GPS ping |
| GET | `/api/v1/integrations/gps/vehicles` | All tracked vehicles |
| GET | `/api/v1/integrations/gps/vehicles/{id}/history` | Location history |

### Example API Request/Response

**Create Production Batch**
```http
POST /api/v1/production/batches
Content-Type: application/json
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

{
  "raw_material_id": 1,
  "input_weight_kg": 5000,
  "boiler_id": "BOILER-01",
  "target_temperature_celsius": 450,
  "operator_name": "Rajesh Kumar",
  "shift": "MORNING"
}
```

**Response**
```json
{
  "success": true,
  "data": {
    "id": 42,
    "batch_number": "BATCH-2025-042",
    "status": "PLANNED",
    "start_datetime": null,
    "input_weight_kg": 5000.00,
    "created_at": "2025-12-31T10:30:00Z"
  }
}
```

---

## Integration Points

### Weighbridge Integration

Most weighbridges can output data via:
1. **Serial Port (RS-232)** - Use a serial-to-USB adapter + Python serial library
2. **TCP/IP** - Direct network connection
3. **File Export** - Read CSV/TXT files dumped by weighbridge software

```python
# Example: Simple weighbridge integration endpoint
@router.post("/weighbridge/record")
async def receive_weighbridge_data(
    ticket_number: str,
    vehicle_number: str,
    weight_kg: float,
    weight_type: str,  # 'GROSS' or 'TARE'
    timestamp: datetime
):
    # Store in database
    # Auto-calculate net weight when both gross and tare received
    pass
```

### GPS Tracker Integration

Common GPS trackers (Letstrack, Loconav) provide:
1. **API Webhooks** - They push location data to your endpoint
2. **REST API** - You pull data from their servers

```python
# Webhook endpoint for GPS pings
@router.post("/gps/location")
async def receive_gps_ping(
    device_id: str,
    latitude: float,
    longitude: float,
    speed_kmph: float,
    timestamp: datetime,
    vehicle_number: str
):
    # Store location history
    # Optional: Trigger alerts for geofence violations
    pass
```

---

## Sustainability Principles

### 1. Minimal Dependencies
- Only 7 Python packages in core requirements
- No heavy frameworks (no Django, no complex ORMs)
- Frontend uses Vue 3 (< 100KB) instead of heavier alternatives

### 2. Simple Database
- Start with SQLite (zero configuration)
- Migrate to PostgreSQL only when scaling (free tier available)
- No complex migrations or database features initially

### 3. Stateless Architecture
- JWT-based authentication (no session storage)
- Each request is independent
- Easy horizontal scaling if needed later

### 4. Self-Documenting Code
- FastAPI auto-generates OpenAPI/Swagger docs
- Visit `/docs` for interactive API documentation
- Pydantic schemas serve as both validation and documentation

### 5. Easy Deployment
```bash
# One-command deployment to Railway/Render
git push origin main  # Commits trigger auto-deploy
```

### 6. Backup Strategy
```bash
# SQLite backup (just copy the file)
cp erp.db backups/erp_$(date +%Y%m%d).db

# PostgreSQL backup
pg_dump $DATABASE_URL > backups/backup_$(date +%Y%m%d).sql
```

---

## Getting Started

### Prerequisites
- Python 3.11 or higher
- Node.js 18+ (for frontend)
- Git

### Quick Start

```bash
# 1. Clone and setup backend
cd tyre-pyrolysis-erp
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Initialize database
python -c "from database import init_db; init_db()"

# 3. Run backend server
uvicorn main:app --reload --port 8000

# 4. In new terminal, setup frontend
cd frontend
npm install
npm run dev

# 5. Open browser
# Backend API Docs: http://localhost:8000/docs
# Frontend App: http://localhost:5173
```

### Environment Variables

```bash
# .env file
DATABASE_URL=sqlite:///./erp.db
SECRET_KEY=your-super-secret-key-change-in-production
DEBUG=true
CORS_ORIGINS=http://localhost:5173
```

---

## Next Steps

### Implementation Roadmap (Version 3.0)

1. **Phase 1 - Core Setup:** Vendor management with EPR compliance + Raw Materials
2. **Phase 2 - Procurement:** GRN with deductions, Weighbridge integration
3. **Phase 3 - Production:** Reactor tracking, Batch phases, Electricity metering
4. **Phase 4 - Tank Farm:** Storage tanks, Oil transfers, Water separation
5. **Phase 5 - Secondary Processing:** Carbon grinding, Stock conversion
6. **Phase 6 - Sales:** Customers, Sales Orders with GST
7. **Phase 7 - Maintenance:** Reactor cleaning schedules, Safety audits
8. **Phase 8 - Reporting:** Dashboards (Yield, Cost/kg, Syn-gas loss, Deductions)

---

> [!TIP]
> **For Non-Coders:** This document is your reference. When working with a developer, share this document so they understand your requirements clearly.

---

*Document maintained by: System Architect*  
*Last updated: December 2025*
