import io
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

from ui_interactions import render_cursor_interactions
from ui_tables import render_enterprise_grid

DB_PATH = Path("data") / "assets.db"


def load_css(path: Path) -> None:
    css_path = Path(path)
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as file:
            st.markdown(f"<style>{file.read()}</style>", unsafe_allow_html=True)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_network_devices_table():
    with get_connection() as conn:
        conn.execute(
            """
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
            """
        )
        conn.commit()


def load_departments() -> pd.DataFrame:
    with get_connection() as conn:
        return pd.read_sql_query("SELECT department_id, name FROM departments ORDER BY name", conn)


def load_devices(filters: dict, order_by: str) -> pd.DataFrame:
    base_query = """
        SELECT
            n.device_id,
            n.device_type,
            n.brand,
            n.model,
            COALESCE(d.name, 'Unassigned') AS department,
            n.ip_address,
            n.mac_address,
            n.location,
            n.purchase_date,
            n.warranty_expiry,
            n.status,
            n.notes
        FROM network_devices n
        LEFT JOIN departments d ON n.department_id = d.department_id
    """
    conditions = []
    params = []

    if filters["device_type"] != "All":
        conditions.append("n.device_type = ?")
        params.append(filters["device_type"])

    if filters["status"] != "All":
        conditions.append("n.status = ?")
        params.append(filters["status"])

    if filters["department"] != "All":
        conditions.append("COALESCE(d.name, 'Unassigned') = ?")
        params.append(filters["department"])

    if filters["search"]:
        search_term = f"%{filters['search']}%"
        conditions.append(
            "(n.device_id LIKE ? OR n.brand LIKE ? OR n.model LIKE ? OR n.ip_address LIKE ? OR n.mac_address LIKE ? OR COALESCE(d.name, 'Unassigned') LIKE ? OR n.location LIKE ? OR n.status LIKE ? OR n.notes LIKE ?)"
        )
        params.extend([search_term] * 9)

    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)

    order_map = {
        "Device ID": "n.device_id",
        "Device Type": "n.device_type",
        "Department": "department",
        "Purchase Date": "n.purchase_date",
        "Status": "n.status",
    }
    direction = "ASC"
    if order_by.endswith("▼"):
        direction = "DESC"
        order_key = order_by.replace(" ▼", "")
    else:
        order_key = order_by.replace(" ▲", "")

    order_column = order_map.get(order_key, "n.device_id")
    base_query += f" ORDER BY {order_column} {direction}"

    with get_connection() as conn:
        return pd.read_sql_query(base_query, conn, params=params)


def insert_device(record: dict):
    with get_connection() as conn:
        department_id = None
        if record["department"] != "Unassigned":
            row = conn.execute("SELECT department_id FROM departments WHERE name = ?", (record["department"],)).fetchone()
            if row:
                department_id = row[0]

        conn.execute(
            """
            INSERT INTO network_devices(
                device_id,
                device_type,
                brand,
                model,
                department_id,
                ip_address,
                mac_address,
                location,
                purchase_date,
                warranty_expiry,
                status,
                notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["device_id"].strip().upper(),
                record["device_type"],
                record["brand"],
                record["model"],
                department_id,
                record["ip_address"],
                record["mac_address"],
                record["location"],
                record["purchase_date"],
                record["warranty_expiry"],
                record["status"],
                record["notes"],
            ),
        )
        conn.commit()


def update_device(device_id: str, record: dict):
    with get_connection() as conn:
        department_id = None
        if record["department"] != "Unassigned":
            row = conn.execute("SELECT department_id FROM departments WHERE name = ?", (record["department"],)).fetchone()
            if row:
                department_id = row[0]

        conn.execute(
            """
            UPDATE network_devices SET
                device_type = ?,
                brand = ?,
                model = ?,
                department_id = ?,
                ip_address = ?,
                mac_address = ?,
                location = ?,
                purchase_date = ?,
                warranty_expiry = ?,
                status = ?,
                notes = ?
            WHERE device_id = ?
            """,
            (
                record["device_type"],
                record["brand"],
                record["model"],
                department_id,
                record["ip_address"],
                record["mac_address"],
                record["location"],
                record["purchase_date"],
                record["warranty_expiry"],
                record["status"],
                record["notes"],
                device_id,
            ),
        )
        conn.commit()


def delete_device(device_id: str):
    with get_connection() as conn:
        conn.execute("DELETE FROM network_devices WHERE device_id = ?", (device_id,))
        conn.commit()


def dataframe_to_csv(df: pd.DataFrame) -> bytes:
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8")


def main():
    load_css(Path("styles.css"))
    render_cursor_interactions()

    st.title("Network Infrastructure")
    st.write("Manage switches, routers, patch panels and other network infrastructure assets.")

    if not DB_PATH.exists():
        st.error("Database not found at data/assets.db. Please create the database before using this page.")
        return

    ensure_network_devices_table()
    departments = load_departments()
    department_options = ["All", "Unassigned"] + departments["name"].tolist()
    device_types = ["All", "Switch", "Router", "Firewall", "Access Point", "Patch Panel"]
    status_options = ["All", "Operational", "Maintenance", "Decommissioned", "Spare"]

    with st.sidebar.expander("Search, filter, and sort", expanded=True):
        search_text = st.text_input("Search infrastructure", placeholder="Device ID, brand, model, location, IP")
        selected_type = st.selectbox("Device type", device_types)
        selected_status = st.selectbox("Status", status_options)
        selected_department = st.selectbox("Department", department_options)
        order_by = st.selectbox(
            "Sort by",
            [
                "Device ID ▲",
                "Device ID ▼",
                "Device Type ▲",
                "Device Type ▼",
                "Department ▲",
                "Department ▼",
                "Purchase Date ▲",
                "Purchase Date ▼",
                "Status ▲",
                "Status ▼",
            ],
        )

    filters = {
        "search": search_text,
        "device_type": selected_type,
        "status": selected_status,
        "department": selected_department,
    }

    df_devices = load_devices(filters, order_by)

    st.markdown("### Network Inventory")
    st.write(f"{len(df_devices)} network records found.")
    st.download_button(
        "⬇ Export visible records to CSV",
        dataframe_to_csv(df_devices),
        file_name="network_infrastructure.csv",
        mime="text/csv",
    )

    render_enterprise_grid(df_devices, "No network records match the current filters.")
    st.markdown("---")

    st.subheader("Add new network device")
    with st.form("add_device_form"):
        col1, col2 = st.columns(2)
        with col1:
            device_id = st.text_input("Device ID")
            device_type = st.selectbox("Device Type", ["Switch", "Router", "Firewall", "Access Point", "Patch Panel"])
            brand = st.text_input("Brand")
            model = st.text_input("Model")
            department = st.selectbox("Department", ["Unassigned"] + departments["name"].tolist())
            ip_address = st.text_input("IP Address")
        with col2:
            mac_address = st.text_input("MAC Address")
            location = st.text_input("Location")
            purchase_date = st.date_input("Purchase Date")
            warranty_expiry = st.date_input("Warranty Expiry")
            status = st.selectbox("Status", ["Operational", "Maintenance", "Decommissioned", "Spare"])
            notes = st.text_area("Notes", height=100)

        submitted = st.form_submit_button("Add Device")
        if submitted:
            if not device_id.strip():
                st.error("Device ID is required.")
            else:
                try:
                    insert_device(
                        {
                            "device_id": device_id,
                            "device_type": device_type,
                            "brand": brand,
                            "model": model,
                            "department": department,
                            "ip_address": ip_address,
                            "mac_address": mac_address,
                            "location": location,
                            "purchase_date": purchase_date.isoformat(),
                            "warranty_expiry": warranty_expiry.isoformat(),
                            "status": status,
                            "notes": notes,
                        }
                    )
                    st.success(f"Device {device_id.upper()} added successfully.")
                    st.experimental_rerun()
                except sqlite3.IntegrityError:
                    st.error("A device with this Device ID already exists.")

    st.markdown("---")
    st.subheader("Manage existing network device")
    device_ids = df_devices["device_id"].tolist()
    selected_device = st.selectbox("Choose device", [""] + device_ids)

    if selected_device:
        row = df_devices[df_devices["device_id"] == selected_device].iloc[0]
        with st.form("edit_device_form"):
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("Device ID", row["device_id"], disabled=True)
                edit_type = st.selectbox(
                    "Device Type",
                    ["Switch", "Router", "Firewall", "Access Point", "Patch Panel"],
                    index=["Switch", "Router", "Firewall", "Access Point", "Patch Panel"].index(row["device_type"]) if row["device_type"] in ["Switch", "Router", "Firewall", "Access Point", "Patch Panel"] else 0,
                )
                edit_brand = st.text_input("Brand", row["brand"])
                edit_model = st.text_input("Model", row["model"])
                edit_department = st.selectbox(
                    "Department",
                    ["Unassigned"] + departments["name"].tolist(),
                    index=(["Unassigned"] + departments["name"].tolist()).index(row["department"]) if row["department"] in ["Unassigned"] + departments["name"].tolist() else 0,
                )
                edit_ip = st.text_input("IP Address", row["ip_address"])
            with col2:
                edit_mac = st.text_input("MAC Address", row["mac_address"])
                edit_location = st.text_input("Location", row["location"])
                edit_purchase = st.date_input("Purchase Date", pd.to_datetime(row["purchase_date"]).date() if row["purchase_date"] else None)
                edit_warranty = st.date_input("Warranty Expiry", pd.to_datetime(row["warranty_expiry"]).date() if row["warranty_expiry"] else None)
                edit_status = st.selectbox(
                    "Status",
                    ["Operational", "Maintenance", "Decommissioned", "Spare"],
                    index=["Operational", "Maintenance", "Decommissioned", "Spare"].index(row["status"]) if row["status"] in ["Operational", "Maintenance", "Decommissioned", "Spare"] else 0,
                )
                edit_notes = st.text_area("Notes", row["notes"], height=120)

            update_button = st.form_submit_button("Save Changes")
            delete_button = st.form_submit_button("Delete Device")

            if update_button:
                update_device(
                    selected_device,
                    {
                        "device_type": edit_type,
                        "brand": edit_brand,
                        "model": edit_model,
                        "department": edit_department,
                        "ip_address": edit_ip,
                        "mac_address": edit_mac,
                        "location": edit_location,
                        "purchase_date": edit_purchase.isoformat(),
                        "warranty_expiry": edit_warranty.isoformat(),
                        "status": edit_status,
                        "notes": edit_notes,
                    },
                )
                st.success(f"Device {selected_device} updated successfully.")
                st.experimental_rerun()

            if delete_button:
                delete_device(selected_device)
                st.warning(f"Device {selected_device} deleted.")
                st.experimental_rerun()


if __name__ == "__main__":
    main()
