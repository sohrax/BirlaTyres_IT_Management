import os
import random
import sqlite3
from datetime import date, timedelta

DB_PATH = os.path.join("data", "assets.db")

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

connection = sqlite3.connect(DB_PATH)
connection.execute("PRAGMA foreign_keys = ON")
cursor = connection.cursor()


def create_schema():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS departments (
        department_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        location TEXT,
        manager TEXT
    )
    """)

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
        FOREIGN KEY (department_id) REFERENCES departments(department_id)
    )
    """)

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


def random_date(start_year=2018, end_year=2025):
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    delta = end - start
    return (start + timedelta(days=random.randint(0, delta.days))).isoformat()


def random_ip(subnet="192.168.10"):
    return f"{subnet}.{random.randint(10, 250)}"


def random_mac():
    return ":".join(f"{random.randint(0, 255):02X}" for _ in range(6))


def seed_departments():
    departments = [
        ("IT Operations", "Head Office, Mumbai", "Ramesh Kumar"),
        ("Network", "Pune Data Center", "Sonal Desai"),
        ("Infrastructure", "Nagpur Campus", "Vikram Joshi"),
        ("Support", "Bangalore Site", "Neha Patel"),
        ("Security", "Delhi Office", "Aarti Sharma"),
        ("ERP", "Hyderabad Branch", "Amit Verma"),
        ("Facilities", "Noida Warehouse", "Priya Singh"),
        ("Research", "Chennai Lab", "Arjun Mehta"),
    ]

    cursor.executemany(
        "INSERT OR IGNORE INTO departments(name, location, manager) VALUES (?, ?, ?)",
        departments,
    )
    connection.commit()

    cursor.execute("SELECT department_id, name FROM departments")
    return [row[0] for row in cursor.fetchall()]


def seed_assets(department_ids):
    employee_names = [
        "Aarav Mehta", "Ananya Rao", "Neha Sharma", "Rahul Gupta", "Priya Singh",
        "Rohan Patel", "Isha Desai", "Vikram Joshi", "Sonal Chatterjee", "Amit Verma",
        "Priya Nair", "Arjun Kapoor", "Kavya Iyer", "Manish Kumar", "Shreya Sen",
        "Ritu Malhotra", "Sachin Reddy", "Deepa Joshi", "Nikhil Agarwal", "Karan Sharma",
        "Megha Gupta", "Anil Bhatia", "Sunita Das", "Varun Roy", "Naina Singh",
        "Devika Patel", "Harish Rao", "Mina Kaur", "Tarun Jain", "Rekha Nanda",
    ]

    brands = {
        "Dell": ["Latitude 7420", "OptiPlex 7090", "Vostro 3510"],
        "HP": ["EliteBook 840", "ProBook 450", "Pavilion 15"],
        "Lenovo": ["ThinkPad T14", "ThinkCentre M720", "Yoga Slim 7"],
        "Asus": ["ZenBook 14", "ExpertBook B5", "VivoBook 15"],
        "Acer": ["Aspire 5", "TravelMate P2", "Swift 3"],
        "Apple": ["MacBook Air M1", "MacBook Pro 13", "iMac 24"],
    }

    operating_systems = [
        "Windows 11 Pro", "Windows 10 Pro", "Ubuntu 22.04 LTS", "Windows 11 Home"
    ]

    statuses = ["In Use", "In Repair", "Available", "Pending Disposal"]

    assets = []
    for index in range(1, 81):
        brand = random.choice(list(brands.keys()))
        model = random.choice(brands[brand])
        asset_type = "Laptop" if random.random() < 0.8 else "Desktop"
        department_id = random.choice(department_ids)
        assigned_to = random.choice(employee_names)
        processor = random.choice([
            "Intel Core i5-1135G7", "Intel Core i7-1165G7", "Intel Core i5-1240P",
            "Intel Core i7-12700H", "AMD Ryzen 5 5600U", "AMD Ryzen 7 5800U"
        ])
        ram = random.choice(["8GB", "16GB", "32GB"])
        storage = random.choice(["256GB SSD", "512GB SSD", "1TB HDD", "512GB SSD + 1TB HDD"])
        purchase_date = random_date(2018, 2024)
        status = random.choices(statuses, weights=[70, 10, 15, 5], k=1)[0]

        assets.append(
            (
                f"ASSET-{index:04d}",
                asset_type,
                brand,
                model,
                department_id,
                assigned_to,
                processor,
                ram,
                storage,
                random.choice(operating_systems),
                purchase_date,
                status,
            )
        )

    cursor.executemany(
        "INSERT OR IGNORE INTO assets(asset_id, asset_type, brand, model, department_id, assigned_to, processor, ram, storage, operating_system, purchase_date, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        assets,
    )
    connection.commit()

    return [f"ASSET-{i:04d}" for i in range(1, 81)]


def seed_maintenance(asset_ids):
    vendors = [
        "Cisco Services", "HPE Support", "Dell ProSupport", "Canon Care", "APC Maintenance"
    ]
    statuses = ["Completed", "Scheduled", "In Progress"]
    descriptions = [
        "Preventive maintenance", "Hardware repair", "OS patch update", "Battery replacement", "Network cable replacement",
        "Firmware upgrade", "Printer calibration", "UPS battery test"
    ]

    cursor.execute("DELETE FROM maintenance")
    maintenance_records = []
    for index in range(1, 51):
        asset_id = random.choice(asset_ids)
        maintenance_date = random_date(2021, 2025)
        cost = round(random.uniform(1200, 25000), 2)
        next_due_date = (date.fromisoformat(maintenance_date) + timedelta(days=random.randint(90, 365))).isoformat()
        maintenance_records.append(
            (
                asset_id,
                maintenance_date,
                random.choice(vendors),
                cost,
                random.choice(descriptions),
                next_due_date,
                random.choice(statuses),
            )
        )

    cursor.executemany(
        "INSERT INTO maintenance(asset_id, maintenance_date, vendor, cost, description, next_due_date, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
        maintenance_records,
    )
    connection.commit()


def seed_network_devices(department_ids):
    device_types = ["Switch", "Router", "Firewall", "Access Point"]
    brands = {
        "Cisco": ["Catalyst 9200", "ISR 1100", "Firepower 1010", "Aironet 1850"],
        "Juniper": ["EX2300", "SRX300", "WLA532", "QFX5100"],
        "HPE Aruba": ["2930F", "Aruba 7005", "Aruba 303", "Aruba 7205"]
    }
    statuses = ["In Use", "Maintenance", "Spare"]
    records = []
    for index in range(1, 19):
        brand = random.choice(list(brands.keys()))
        model = random.choice(brands[brand])
        device_type = random.choice(device_types)
        department_id = random.choice(department_ids)
        records.append(
            (
                f"NET-{index:03d}",
                device_type,
                brand,
                model,
                department_id,
                random_ip("10.0.5"),
                random_mac(),
                random.choice(["Mumbai DC", "Pune POP", "Bangalore Office", "Delhi Office", "Chennai Lab"]),
                random_date(2018, 2024),
                random_date(2023, 2026),
                random.choice(statuses),
            )
        )

    cursor.executemany(
        "INSERT OR IGNORE INTO network_devices(device_id, device_type, brand, model, department_id, ip_address, mac_address, location, purchase_date, warranty_expiry, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        records,
    )
    connection.commit()


def seed_ups(department_ids):
    brands = {
        "APC": ["Back-UPS 1500", "Smart-UPS 2200"],
        "Vertiv": ["Liebert GXT4-2200", "Liebert PSA5-1500"],
        "Eaton": ["5P 1550", "9PX 3000"],
    }
    schedules = ["Quarterly", "Semi-Annual", "Annual"]
    statuses = ["In Use", "Standby", "Under Service"]

    records = []
    for index in range(1, 21):
        brand = random.choice(list(brands.keys()))
        model = random.choice(brands[brand])
        department_id = random.choice(department_ids)
        records.append(
            (
                f"UPS-{index:03d}",
                brand,
                model,
                random.choice([1000, 1500, 2000, 3000, 5000]),
                department_id,
                random.choice(["Server Room", "Network Rack", "Office Floor", "Data Center"]),
                random_date(2019, 2024),
                random.choice(schedules),
                random.choice(statuses),
            )
        )

    cursor.executemany(
        "INSERT OR IGNORE INTO ups(ups_id, brand, model, capacity_va, department_id, location, purchase_date, maintenance_schedule, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        records,
    )
    connection.commit()


def seed_printers(department_ids):
    brands = {
        "HP": ["LaserJet Pro M404dn", "OfficeJet Pro 9015"],
        "Canon": ["imageCLASS LBP6030w", "MAXIFY GX5020"],
        "Epson": ["EcoTank L3150", "WorkForce Pro WF-3720"],
        "Brother": ["HL-L2350DW", "MFC-L2710DW"],
    }
    toner_levels = ["Full", "75%", "50%", "25%"]
    statuses = ["In Use", "Idle", "Needs Toner", "Repair"]

    records = []
    for index in range(1, 16):
        brand = random.choice(list(brands.keys()))
        model = random.choice(brands[brand])
        department_id = random.choice(department_ids)
        records.append(
            (
                f"PRN-{index:03d}",
                brand,
                model,
                department_id,
                random.choice(["1st Floor", "2nd Floor", "Ground Floor", "Server Room"]),
                random_ip("10.0.12"),
                f"SN{random.randint(100000, 999999)}",
                random_date(2019, 2024),
                random.choice(statuses),
                random.choice(toner_levels),
            )
        )

    cursor.executemany(
        "INSERT OR IGNORE INTO printers(printer_id, brand, model, department_id, location, ip_address, serial_number, purchase_date, status, toner_level) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        records,
    )
    connection.commit()


def main():
    create_schema()
    department_ids = seed_departments()
    asset_ids = seed_assets(department_ids)
    seed_maintenance(asset_ids)
    seed_network_devices(department_ids)
    seed_ups(department_ids)
    seed_printers(department_ids)
    print("Seed data inserted successfully into", DB_PATH)


if __name__ == "__main__":
    main()
