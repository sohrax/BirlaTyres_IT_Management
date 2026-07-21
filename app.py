import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from ui_interactions import render_cursor_interactions
from ui_tables import render_enterprise_grid

st.set_page_config(
    page_title="Birla Tyres IT Management",
    page_icon="🏭",
    layout="wide",
)

DB_PATH = Path("data") / "assets.db"


def get_connection(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def load_dataframe(query: str, params=None) -> pd.DataFrame:
    params = params or ()
    with get_connection(DB_PATH) as conn:
        return pd.read_sql_query(query, conn, params=params)


def load_css(path: Path) -> None:
    css_path = Path(path)
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as file:
            st.markdown(f"<style>{file.read()}</style>", unsafe_allow_html=True)


def fetch_value(query: str, params=None):
    params = params or ()
    with get_connection(DB_PATH) as conn:
        cursor = conn.execute(query, params)
        row = cursor.fetchone()
    return row[0] if row is not None else None


def kpi_card(label: str, value: int) -> str:
    numeric_value = int(value or 0)
    return (
        "<div class='kpi-card'>"
        f"<span class='kpi-label'>{label}</span>"
        f"<span class='kpi-value' style='--target: {numeric_value};' aria-label='{numeric_value}'>{numeric_value}</span>"
        "</div>"
    )


def main():
    load_css(Path("styles.css"))
    render_cursor_interactions()

    st.markdown(
        "<div class='hero-panel'>"
        "<div class='hero-copy'>"
        "<div class='eyebrow'>Birla Tyres Digital IT Asset & Infrastructure Management</div>"
        "<h1>Enterprise SOC Dashboard</h1>"
        "<p class='hero-description'>A premium industrial-grade monitoring surface for IT assets, infrastructure, and maintenance operations.</p>"
        "</div>"
        "<div class='hero-pill'>"
        "<span>Futuristic Control Room</span>"
        "<span>Cyberpunk Visibility</span>"
        "<span>Dark Industrial Interface</span>"
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    if not DB_PATH.exists():
        st.error(f"Database not found at `{DB_PATH}`. Run `seed_database.py` first to create the data.")
        return

    departments = load_dataframe("SELECT department_id, name FROM departments ORDER BY name")
    department_options = ["All Departments"] + departments["name"].tolist()

    st.sidebar.markdown(
        "<div class='sidebar-panel'>"
        "<div class='sidebar-title'>Control Surface</div>"
        "<p class='sidebar-note'>Scope the dashboard to a department and operate with precision from the command console.</p>"
        "</div>",
        unsafe_allow_html=True,
    )
    selected_department = st.sidebar.selectbox("Filter by department", department_options, label_visibility="collapsed")
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "<div class='sidebar-panel'>"
        "<div class='sidebar-title'>Operational Mode</div>"
        "<p class='sidebar-note'>Use these controls to refine asset and maintenance visibility for mission-critical decisions.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    if selected_department == "All Departments":
        department_filter = ""
        params = ()
    else:
        department_id = int(departments.loc[departments["name"] == selected_department, "department_id"].item())
        department_filter = "WHERE department_id = ?"
        params = (department_id,)

    total_assets = fetch_value("SELECT COUNT(*) FROM assets")
    total_printers = fetch_value("SELECT COUNT(*) FROM printers")
    total_ups = fetch_value("SELECT COUNT(*) FROM ups")
    total_network_devices = fetch_value("SELECT COUNT(*) FROM network_devices")
    total_departments = fetch_value("SELECT COUNT(*) FROM departments")
    maintenance_events = fetch_value("SELECT COUNT(*) FROM maintenance")
    maintenance_open = fetch_value("SELECT COUNT(*) FROM maintenance WHERE status != 'Completed'")

    st.markdown(
        "<div class='kpi-cards-grid'>"
        f"{kpi_card('Total Assets', total_assets)}"
        f"{kpi_card('Network Devices', total_network_devices)}"
        f"{kpi_card('Printers', total_printers)}"
        f"{kpi_card('UPS Units', total_ups)}"
        f"{kpi_card('Departments', total_departments)}"
        f"{kpi_card('Maintenance Records', maintenance_events)}"
        f"{kpi_card('Open Maintenance', maintenance_open)}"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("---")

    asset_status = load_dataframe(
        f"SELECT status, COUNT(*) AS count FROM assets {department_filter} GROUP BY status ORDER BY count DESC",
        params,
    )
    assets_by_department = load_dataframe(
        "SELECT d.name AS department, COUNT(a.asset_id) AS count FROM assets a JOIN departments d ON a.department_id = d.department_id GROUP BY d.name ORDER BY count DESC"
    )
    maintenance_by_status = load_dataframe(
        "SELECT status, COUNT(*) AS count FROM maintenance GROUP BY status ORDER BY count DESC"
    )
    net_device_types = load_dataframe(
        "SELECT device_type, COUNT(*) AS count FROM network_devices GROUP BY device_type ORDER BY count DESC"
    )
    printer_toner = load_dataframe(
        "SELECT toner_level, COUNT(*) AS count FROM printers GROUP BY toner_level ORDER BY count DESC"
    )

    row1_col1, row1_col2 = st.columns((2, 1))
    with row1_col1:
        st.markdown("<div class='section-heading-row'><h2>Asset Distribution</h2><p>Department-level inventory insights for tactical resource allocation.</p></div>", unsafe_allow_html=True)
        fig_assets_department = px.bar(
            assets_by_department,
            x="department",
            y="count",
            text="count",
            labels={"department": "Department", "count": "Assets"},
            color_discrete_sequence=["#B026FF", "#8A2BE2", "#00FFB2", "#FF4D7D", "#6F1DCE"],
        )
        fig_assets_department.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            hoverlabel_bgcolor="#171722",
            hoverlabel_bordercolor="#B026FF",
            font=dict(color="#FBFAFF", family="Space Grotesk, Sora, Plus Jakarta Sans", size=14),
            showlegend=False,
            xaxis_title=None,
            yaxis_title="Assets",
            margin=dict(t=20, r=20, l=20, b=30),
        )
        fig_assets_department.update_traces(marker_line_color="rgba(255,255,255,0.18)", marker_line_width=1.5)
        st.plotly_chart(fig_assets_department, use_container_width=True)

        st.markdown("<div class='section-heading-row'><h2>Status Heatmap</h2><p>Live breakdown of asset operational condition.</p></div>", unsafe_allow_html=True)
        fig_asset_status = px.pie(
            asset_status,
            names="status",
            values="count",
            color_discrete_sequence=["#B026FF", "#8A2BE2", "#FF4D7D", "#00FFB2"],
        )
        fig_asset_status.update_traces(textposition="inside", textinfo="percent+label")
        fig_asset_status.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            legend_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#FBFAFF", family="Space Grotesk, Sora, Plus Jakarta Sans", size=14),
            margin=dict(t=10, r=10, l=10, b=10),
        )
        st.plotly_chart(fig_asset_status, use_container_width=True)

    with row1_col2:
        st.markdown("<div class='section-heading-row'><h2>Networking Topology</h2><p>Device classifications across the operational estate.</p></div>", unsafe_allow_html=True)
        fig_network_types = px.bar(
            net_device_types,
            x="device_type",
            y="count",
            text="count",
            labels={"device_type": "Device Type", "count": "Devices"},
            color_discrete_sequence=["#FF4D7D", "#B026FF", "#8A2BE2", "#00FFB2"],
        )
        fig_network_types.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            hoverlabel_bgcolor="#171722",
            hoverlabel_bordercolor="#B026FF",
            font=dict(color="#FBFAFF", family="Space Grotesk, Sora, Plus Jakarta Sans", size=14),
            showlegend=False,
            xaxis_title=None,
            yaxis_title="Devices",
            margin=dict(t=20, r=20, l=20, b=30),
        )
        fig_network_types.update_traces(marker_line_color="rgba(255,255,255,0.18)", marker_line_width=1.5)
        st.plotly_chart(fig_network_types, use_container_width=True)

        st.markdown("<div class='section-heading-row'><h2>Printer Toner Status</h2><p>Supply readiness for peripheral fleet maintenance.</p></div>", unsafe_allow_html=True)
        fig_printer_toner = px.bar(
            printer_toner,
            x="toner_level",
            y="count",
            text="count",
            labels={"toner_level": "Toner Level", "count": "Printers"},
            color_discrete_sequence=["#8A2BE2", "#B026FF", "#FF4D7D"],
        )
        fig_printer_toner.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            hoverlabel_bgcolor="#171722",
            hoverlabel_bordercolor="#B026FF",
            font=dict(color="#FBFAFF", family="Space Grotesk, Sora, Plus Jakarta Sans", size=14),
            showlegend=False,
            xaxis_title=None,
            yaxis_title="Printers",
            margin=dict(t=20, r=20, l=20, b=30),
        )
        fig_printer_toner.update_traces(marker_line_color="rgba(255,255,255,0.18)", marker_line_width=1.5)
        st.plotly_chart(fig_printer_toner, use_container_width=True)

    st.markdown("---")

    maintenance_table = load_dataframe(
        "SELECT maintenance_id, asset_id, maintenance_date, vendor, cost, status FROM maintenance ORDER BY maintenance_date DESC LIMIT 10"
    )

    st.subheader("Recent Maintenance Records")
    render_enterprise_grid(maintenance_table, "No maintenance records found.")

    st.markdown("---")
    st.caption("Data is read directly from the SQLite database and refreshed whenever the app reloads.")


if __name__ == "__main__":
    main()
