"""
D1 + D2 — Report History Storage & Retrieval
Stores the last N reports in SQLite. Supports re-download and re-send.
Reads db_path, max_reports, and name_format from config.yaml.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

import yaml
from models.schemas import PulsePayload


def _load_config() -> dict:
    """Load history config from config.yaml."""
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f).get("history", {})


def _get_connection() -> sqlite3.Connection:
    """Get a SQLite database connection, creating the table if needed."""
    config = _load_config()
    db_path = config.get("db_path", "reports.db")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_name TEXT NOT NULL,
            source TEXT NOT NULL,
            review_count INTEGER NOT NULL,
            generated_at TEXT NOT NULL,
            pdf_path TEXT,
            pulse_payload JSON NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


def save_report(pulse: PulsePayload, pdf_path: str = None) -> int:
    """
    Save a report to history. Auto-prunes to keep only the last N.

    Args:
        pulse: The PulsePayload to save.
        pdf_path: Optional path to the generated PDF.

    Returns:
        The ID of the saved report.
    """
    config = _load_config()
    max_reports = config.get("max_reports", 3)
    name_format = config.get("name_format", "IndMoney Pulse - {date}")

    conn = _get_connection()

    report_name = name_format.format(date=datetime.now().strftime("%d %b %Y"))

    conn.execute(
        """INSERT INTO reports (report_name, source, review_count, generated_at, pdf_path, pulse_payload)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            report_name,
            pulse.metadata.get("source", "Google Play Store"),
            pulse.metadata.get("review_count", 0),
            pulse.metadata.get("generated_at", ""),
            pdf_path,
            pulse.model_dump_json(),
        ),
    )
    conn.commit()

    report_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    # Prune: keep only the last max_reports
    conn.execute(
        f"""DELETE FROM reports
            WHERE id NOT IN (
                SELECT id FROM reports ORDER BY created_at DESC LIMIT {max_reports}
            )"""
    )
    conn.commit()
    conn.close()

    return report_id


def get_history() -> list[dict]:
    """
    Retrieve the last N reports (metadata only, no full payload).

    Returns:
        List of report metadata dicts (most recent first).
    """
    config = _load_config()
    max_reports = config.get("max_reports", 3)

    conn = _get_connection()
    rows = conn.execute(
        "SELECT id, report_name, source, review_count, generated_at, pdf_path, created_at FROM reports ORDER BY created_at DESC LIMIT ?",
        (max_reports,),
    ).fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_report(report_id: int) -> PulsePayload | None:
    """
    Retrieve a specific report's full PulsePayload by ID.

    Args:
        report_id: The report ID.

    Returns:
        PulsePayload or None if not found.
    """
    conn = _get_connection()
    row = conn.execute(
        "SELECT pulse_payload FROM reports WHERE id = ?", (report_id,)
    ).fetchone()
    conn.close()

    if row:
        return PulsePayload.model_validate_json(row["pulse_payload"])
    return None


def delete_report(report_id: int) -> bool:
    """
    Delete a specific report by ID.

    Args:
        report_id: The report ID.

    Returns:
        True if deleted, False if not found.
    """
    conn = _get_connection()
    cursor = conn.execute("DELETE FROM reports WHERE id = ?", (report_id,))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0


def update_pdf_path(report_id: int, pdf_path: str) -> bool:
    """Updates the PDF path for an existing report."""
    conn = _get_connection()
    cursor = conn.execute("UPDATE reports SET pdf_path = ? WHERE id = ?", (pdf_path, report_id))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0

