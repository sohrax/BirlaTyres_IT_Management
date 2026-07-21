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


def ensure_assets_table():
    with get_connection() as conn:
        conn.execute(
            """
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
            """
        )
        conn.commit()


def load_departments() -> pd.DataFrame:
    with get_connection() as conn:
        return pd.read_sql_query(
            "SELECT department_id, name FROM departments ORDER BY name",
            conn,
        )


def load_assets(search_text: str, department: str, asset_type: str, status: str, order_by: str) -> pd.DataFrame:
    base_query = """
        SELECT
            a.asset_id,
            a.asset_type,
            a.brand,
            a.model,
            COALESCE(d.name, 'Unassigned') AS department,
            a.assigned_to,
            a.processor,
            a.ram,
            a.storage,
            a.operating_system,
            a.purchase_date,
            a.status
        FROM assets a
        LEFT JOIN departments d ON a.department_id = d.department_id
    """
    conditions = []
    params = []

    if department and department != "All":
        conditions.append("COALESCE(d.name, 'Unassigned') = ?")
        params.append(department)

    if asset_type and asset_type != "All":
        conditions.append("a.asset_type = ?")
        params.append(asset_type)

    if status and status != "All":
        conditions.append("a.status = ?")
        params.append(status)

    if search_text:
        like_term = f"%{search_text}%"
        conditions.append(
            "(a.asset_id LIKE ? OR a.brand LIKE ? OR a.model LIKE ? OR a.assigned_to LIKE ? OR a.operating_system LIKE ? OR d.name LIKE ? OR a.status LIKE ?)")
        params.extend([like_term] * 7)

    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)

    order_map = {
        "Asset ID": "a.asset_id",
        "Purchase Date": "a.purchase_date",
        "Status": "a.status",
        "Department": "department",
        "Asset Type": "a.asset_type",
    }
    direction = "ASC"
    if order_by.endswith("▼"):
        direction = "DESC"
        order_key = order_by.replace(" ▼", "")
    else:
        order_key = order_by.replace(" ▲", "")

    order_column = order_map.get(order_key, "a.asset_id")
    base_query += f" ORDER BY {order_column} {direction}"

    with get_connection() as conn:
        return pd.read_sql_query(base_query, conn, params=params)


def insert_asset(record: dict):
    with get_connection() as conn:
        department_id = None
        if record["department"] and record["department"] != "Unassigned":
            result = conn.execute(
                "SELECT department_id FROM departments WHERE name = ?",
                (record["department"],),
            ).fetchone()
            if result:
                department_id = result[0]

        conn.execute(
            """
            INSERT INTO assets(
                asset_id,
                asset_type,
                brand,
                model,
                department_id,
                assigned_to,
                processor,
                ram,
                storage,
                operating_system,
                purchase_date,
                status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["asset_id"].strip().upper(),
                record["asset_type"],
                record["brand"],
                record["model"],
                department_id,
                record["assigned_to"],
                record["processor"],
                record["ram"],
                record["storage"],
                record["operating_system"],
                record["purchase_date"],
                record["status"],
            ),
        )
        conn.commit()


def update_asset(asset_id: str, record: dict):
    with get_connection() as conn:
        department_id = None
        if record["department"] and record["department"] != "Unassigned":
            result = conn.execute(
                "SELECT department_id FROM departments WHERE name = ?",
                (record["department"],),
            ).fetchone()
            if result:
                department_id = result[0]

        conn.execute(
            """
            UPDATE assets SET
                asset_type = ?,
                brand = ?,
                model = ?,
                department_id = ?,
                assigned_to = ?,
                processor = ?,
                ram = ?,
                storage = ?,
                operating_system = ?,
                purchase_date = ?,
                status = ?
            WHERE asset_id = ?
            """,
            (
                record["asset_type"],
                record["brand"],
                record["model"],
                department_id,
                record["assigned_to"],
                record["processor"],
                record["ram"],
                record["storage"],
                record["operating_system"],
                record["purchase_date"],
                record["status"],
                asset_id,
            ),
        )
        conn.commit()


def delete_asset(asset_id: str):
    with get_connection() as conn:
        conn.execute("DELETE FROM assets WHERE asset_id = ?", (asset_id,))
        conn.commit()


def asset_to_csv(df: pd.DataFrame) -> bytes:
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8")


def main():
    load_css(Path("styles.css"))
    render_cursor_interactions()

    st.title("Asset Inventory")
    st.write("Manage computer assets directly in the SQLite database.")

    if not DB_PATH.exists():
        st.error("Database file not found. Run your seed or setup script to create `data/assets.db`.")
        return

    ensure_assets_table()
    departments = load_departments()
    department_names = ["All"] + departments["name"].tolist() + ["Unassigned"]
    asset_types = ["All", "Laptop", "Desktop", "Server", "Tablet", "Printer"]
    status_values = ["All", "In Use", "In Repair", "Available", "Pending Disposal"]

    with st.sidebar.expander("Search and filters", expanded=True):
        search_text = st.text_input("Search assets", placeholder="Asset ID, Brand, Model, User, Department")
        selected_department = st.selectbox("Department", department_names)
        selected_type = st.selectbox("Asset type", asset_types)
        selected_status = st.selectbox("Status", status_values)
        order_by = st.selectbox(
            "Sort by",
            [
                "Asset ID ▲",
                "Asset ID ▼",
                "Purchase Date ▲",
                "Purchase Date ▼",
                "Status ▲",
                "Status ▼",
                "Department ▲",
                "Department ▼",
                "Asset Type ▲",
                "Asset Type ▼",
            ],
        )

    df_assets = load_assets(search_text, selected_department, selected_type, selected_status, order_by)

    st.markdown("### Inventory Overview")
    st.write(f"Showing {len(df_assets)} assets")
    st.download_button(
        label="⬇ Export visible inventory to CSV",
        data=asset_to_csv(df_assets),
        file_name="asset_inventory.csv",
        mime="text/csv",
    )

    render_enterprise_grid(df_assets, "No assets match the current filters.")

    st.markdown("---")
    st.subheader("Add a new asset")

    with st.form("add_asset_form"):
        col1, col2 = st.columns(2)
        with col1:
            asset_id = st.text_input("Asset ID")
            asset_type = st.selectbox("Asset Type", ["Laptop", "Desktop", "Server", "Tablet", "Printer"], index=0)
            brand = st.text_input("Brand")
            model = st.text_input("Model")
            department = st.selectbox("Department", ["Unassigned"] + departments["name"].tolist())
            assigned_to = st.text_input("Assigned To")
        with col2:
            processor = st.text_input("Processor")
            ram = st.text_input("RAM")
            storage = st.text_input("Storage")
            operating_system = st.text_input("Operating System")
            purchase_date = st.date_input("Purchase Date")
            status = st.selectbox("Status", ["In Use", "In Repair", "Available", "Pending Disposal"], index=0)

        add_button = st.form_submit_button("Add Asset")
        if add_button:
            if not asset_id.strip():
                st.error("Asset ID is required.")
            else:
                try:
                    insert_asset(
                        {
                            "asset_id": asset_id,
                            "asset_type": asset_type,
                            "brand": brand,
                            "model": model,
                            "department": department,
                            "assigned_to": assigned_to,
                            "processor": processor,
                            "ram": ram,
                            "storage": storage,
                            "operating_system": operating_system,
                            "purchase_date": purchase_date.isoformat(),
                            "status": status,
                        }
                    )
                    st.success(f"Asset {asset_id.upper()} added successfully.")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("An asset with this Asset ID already exists.")

    st.markdown("---")
    st.subheader("Edit or delete existing asset")

    editable_ids = df_assets["asset_id"].tolist()
    selected_asset_id = st.selectbox("Select asset to manage", [""] + editable_ids)

    if selected_asset_id:
        selected_asset = df_assets[df_assets["asset_id"] == selected_asset_id].iloc[0]
        with st.form("edit_asset_form"):
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("Asset ID", selected_asset["asset_id"], disabled=True)
                edit_asset_type = st.selectbox(
                    "Asset Type",
                    ["Laptop", "Desktop", "Server", "Tablet", "Printer"],
                    index=["Laptop", "Desktop", "Server", "Tablet", "Printer"].index(selected_asset["asset_type"]) if selected_asset["asset_type"] in ["Laptop", "Desktop", "Server", "Tablet", "Printer"] else 0,
                )
                edit_brand = st.text_input("Brand", selected_asset["brand"])
                edit_model = st.text_input("Model", selected_asset["model"])
                edit_department = st.selectbox(
                    "Department",
                    ["Unassigned"] + departments["name"].tolist(),
                    index=(["Unassigned"] + departments["name"].tolist()).index(selected_asset["department"]) if selected_asset["department"] in ["Unassigned"] + departments["name"].tolist() else 0,
                )
                edit_assigned_to = st.text_input("Assigned To", selected_asset["assigned_to"])
            with col2:
                edit_processor = st.text_input("Processor", selected_asset["processor"])
                edit_ram = st.text_input("RAM", selected_asset["ram"])
                edit_storage = st.text_input("Storage", selected_asset["storage"])
                edit_operating_system = st.text_input("Operating System", selected_asset["operating_system"])
                edit_purchase_date = st.date_input("Purchase Date", pd.to_datetime(selected_asset["purchase_date"]).date() if selected_asset["purchase_date"] else None)
                edit_status = st.selectbox(
                    "Status",
                    ["In Use", "In Repair", "Available", "Pending Disposal"],
                    index=["In Use", "In Repair", "Available", "Pending Disposal"].index(selected_asset["status"]) if selected_asset["status"] in ["In Use", "In Repair", "Available", "Pending Disposal"] else 0,
                )

            save_button = st.form_submit_button("Save Changes")
            delete_button = st.form_submit_button("Delete Asset")

            if save_button:
                update_asset(
                    selected_asset_id,
                    {
                        "asset_type": edit_asset_type,
                        "brand": edit_brand,
                        "model": edit_model,
                        "department": edit_department,
                        "assigned_to": edit_assigned_to,
                        "processor": edit_processor,
                        "ram": edit_ram,
                        "storage": edit_storage,
                        "operating_system": edit_operating_system,
                        "purchase_date": edit_purchase_date.isoformat(),
                        "status": edit_status,
                    },
                )
                st.success(f"Asset {selected_asset_id} updated successfully.")
                st.rerun()

            if delete_button:
                delete_asset(selected_asset_id)
                st.warning(f"Asset {selected_asset_id} deleted.")
                st.rerun()


if __name__ == "__main__":
    main()
