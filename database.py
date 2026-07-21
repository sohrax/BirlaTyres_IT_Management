import sqlite3

# Connect to database (creates it if it doesn't exist)
conn = sqlite3.connect("data/assets.db")

# Cursor helps execute SQL commands
cursor = conn.cursor()

# Create the departments table to store organizational units.
cursor.execute("""
CREATE TABLE IF NOT EXISTS departments (
    department_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    location TEXT,
    manager TEXT
)
""")

# Create the assets table with a foreign key to departments.
cursor.execute("""
CREATE TABLE IF NOT EXISTS assets (
    asset_id TEXT PRIMARY KEY,
    asset_type TEXT NOT NULL,
    brand TEXT,
    model TEXT,
    department_id INTEGER,
    assigned_to TEXT,
    processor TEXT,
    ram TEXT,
    storage TEXT,
    operating_system TEXT,
    purchase_date TEXT,
    status TEXT,
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
)
""")

# Create the maintenance table to track service events for assets.
cursor.execute("""
CREATE TABLE IF NOT EXISTS maintenance (
    maintenance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id TEXT NOT NULL,
    maintenance_date TEXT,
    vendor TEXT,
    cost REAL,
    description TEXT,
    next_due_date TEXT,
    status TEXT,
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
)
""")

# Create the network_devices table for switches, routers, firewalls, etc.
cursor.execute("""
CREATE TABLE IF NOT EXISTS network_devices (
    device_id TEXT PRIMARY KEY,
    device_type TEXT NOT NULL,
    brand TEXT,
    model TEXT,
    department_id INTEGER,
    ip_address TEXT,
    mac_address TEXT,
    location TEXT,
    purchase_date TEXT,
    warranty_expiry TEXT,
    status TEXT,
    notes TEXT,
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
)
""")

# Create the ups table for UPS infrastructure details.
cursor.execute("""
CREATE TABLE IF NOT EXISTS ups (
    ups_id TEXT PRIMARY KEY,
    brand TEXT,
    model TEXT,
    capacity_va INTEGER,
    department_id INTEGER,
    location TEXT,
    purchase_date TEXT,
    maintenance_schedule TEXT,
    status TEXT,
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
)
""")

# Create the printers table for printer asset tracking.
cursor.execute("""
CREATE TABLE IF NOT EXISTS printers (
    printer_id TEXT PRIMARY KEY,
    brand TEXT,
    model TEXT,
    department_id INTEGER,
    location TEXT,
    ip_address TEXT,
    serial_number TEXT,
    purchase_date TEXT,
    status TEXT,
    toner_level TEXT,
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
)
""")

# Save changes
conn.commit()

# Close connection
conn.close()

print("Database Created Successfully!")