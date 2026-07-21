from html import escape
from typing import Any

import pandas as pd
import streamlit as st


TYPE_ICONS = {
    "desktop": "🖥️",
    "laptop": "💻",
    "printer": "🖨️",
    "ups": "🔋",
    "router": "📡",
    "switch": "🌐",
    "server": "🗄️",
}

DEPARTMENT_ACCENTS = {
    "it": "#B026FF",
    "network": "#2F80FF",
    "hr": "#FF4DCD",
    "security": "#FF4D7D",
    "infrastructure": "#00E5FF",
    "facilities": "#FF9F2F",
}

STATUS_CLASSES = {
    "working": "status-working",
    "operational": "status-working",
    "in use": "status-working",
    "available": "status-working",
    "completed": "status-working",
    "spare": "status-working",
    "maintenance": "status-maintenance",
    "in repair": "status-maintenance",
    "pending": "status-maintenance",
    "scheduled": "status-maintenance",
    "offline": "status-offline",
    "faulty": "status-offline",
    "down": "status-offline",
    "retired": "status-retired",
    "decommissioned": "status-retired",
    "pending disposal": "status-retired",
}


def _display_value(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value)


def _slug(value: str) -> str:
    return "".join(character.lower() if character.isalnum() else "-" for character in value).strip("-")


def _department_accent(value: str) -> str:
    normalized = value.lower()
    for department, accent in DEPARTMENT_ACCENTS.items():
        if department in normalized:
            return accent
    palette = ["#B026FF", "#2F80FF", "#FF4DCD", "#FF4D7D", "#00E5FF", "#FF9F2F"]
    return palette[sum(ord(character) for character in normalized) % len(palette)]


def _status_class(value: str) -> str:
    normalized = value.lower()
    for status, class_name in STATUS_CLASSES.items():
        if status in normalized:
            return class_name
    return "status-neutral"


def _format_cell(column: str, value: Any) -> str:
    text = _display_value(value)
    safe_text = escape(text)
    normalized_column = column.lower()
    normalized_value = text.lower()

    if not text:
        return "<span class='cell-muted'>&mdash;</span>"

    if normalized_column in {"asset_id", "device_id", "maintenance_id"} or normalized_column.endswith("_id"):
        return f"<span class='id-tag'>{safe_text}</span>"

    if normalized_column in {"asset_type", "device_type", "type"}:
        icon = next((icon for key, icon in TYPE_ICONS.items() if key in normalized_value), "")
        return f"<span class='type-cell'><span class='type-icon'>{icon}</span><span>{safe_text}</span></span>"

    if "status" in normalized_column:
        return f"<span class='status-pill {_status_class(text)}'>{safe_text}</span>"

    if "department" in normalized_column:
        accent = _department_accent(text)
        return f"<span class='department-chip' style='--dept-accent: {accent};'>{safe_text}</span>"

    return safe_text


def render_enterprise_grid(df: pd.DataFrame, empty_message: str = "No records found.") -> None:
    if df.empty:
        st.markdown(
            "<div class='enterprise-empty-state'>"
            "<div class='empty-orb'></div>"
            "<div class='empty-kicker'>No Signal</div>"
            f"<div class='empty-title'>{escape(empty_message)}</div>"
            "<p>The grid is ready. Adjust filters or add records to populate this control surface.</p>"
            "</div>",
            unsafe_allow_html=True,
        )
        return

    headers = "".join(
        f"<th><span>{escape(column.replace('_', ' '))}</span></th>"
        for column in df.columns
    )
    rows = []
    for row_index, row in enumerate(df.to_dict(orient="records"), start=1):
        cells = "".join(
            f"<td data-label='{escape(column.replace('_', ' '))}'>{_format_cell(column, value)}</td>"
            for column, value in row.items()
        )
        rows.append(f"<tr style='--row-index: {row_index};'>{cells}</tr>")

    st.markdown(
        "<div class='enterprise-grid-card'>"
        "<div class='enterprise-grid-scroll'>"
        "<table class='enterprise-grid'>"
        f"<thead><tr>{headers}</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table>"
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )
