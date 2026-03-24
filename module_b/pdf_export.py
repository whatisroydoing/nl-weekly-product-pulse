"""
B1 — PDF Export (reportlab)
Renders a PulsePayload into a clean, branded, multi-page PDF.
"""

import os
from pathlib import Path
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, PageBreak,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

from models.schemas import PulsePayload


# ── Brand colours ────────────────────────────────────────────────────────────
BRAND_BLUE   = colors.HexColor("#1A3C6E")
BRAND_ORANGE = colors.HexColor("#F4801A")
LIGHT_BLUE   = colors.HexColor("#E8EEF5")
LIGHT_GREY   = colors.HexColor("#F7F7F7")
MID_GREY     = colors.HexColor("#CCCCCC")
DARK_TEXT     = colors.HexColor("#1A1A1A")
QUOTE_TEXT    = colors.HexColor("#444444")


def _styles() -> dict:
    """Build and return custom styles."""
    return {
        "title": ParagraphStyle(
            "title",
            fontName="Helvetica-Bold",
            fontSize=22,
            textColor=colors.white,
            leading=28,
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            fontName="Helvetica",
            fontSize=10,
            textColor=colors.HexColor("#AAC4E8"),
            leading=14,
        ),
        "section_header": ParagraphStyle(
            "section_header",
            fontName="Helvetica-Bold",
            fontSize=14,
            textColor=BRAND_BLUE,
            spaceBefore=18,
            spaceAfter=8,
        ),
        "body": ParagraphStyle(
            "body",
            fontName="Helvetica",
            fontSize=10,
            textColor=DARK_TEXT,
            leading=16,
            alignment=TA_JUSTIFY,
            spaceAfter=6,
        ),
        "theme_label": ParagraphStyle(
            "theme_label",
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=DARK_TEXT,
        ),
        "theme_desc": ParagraphStyle(
            "theme_desc",
            fontName="Helvetica",
            fontSize=8,
            textColor=colors.grey,
            leading=11,
        ),
        "quote_theme": ParagraphStyle(
            "quote_theme",
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=BRAND_BLUE,
            spaceBefore=10,
            spaceAfter=4,
        ),
        "quote_text": ParagraphStyle(
            "quote_text",
            fontName="Helvetica-Oblique",
            fontSize=9,
            textColor=QUOTE_TEXT,
            leftIndent=12,
            leading=14,
            spaceAfter=2,
        ),
        "quote_rating": ParagraphStyle(
            "quote_rating",
            fontName="Helvetica",
            fontSize=8,
            textColor=colors.grey,
            leftIndent=12,
            spaceAfter=6,
        ),
        "action_title": ParagraphStyle(
            "action_title",
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=BRAND_BLUE,
            spaceBefore=4,
            spaceAfter=2,
        ),
        "action_desc": ParagraphStyle(
            "action_desc",
            fontName="Helvetica",
            fontSize=9,
            textColor=DARK_TEXT,
            leading=14,
            leftIndent=4,
            spaceAfter=8,
        ),
        "action_linked": ParagraphStyle(
            "action_linked",
            fontName="Helvetica",
            fontSize=8,
            textColor=colors.grey,
            leftIndent=4,
            spaceAfter=4,
        ),
        "footer": ParagraphStyle(
            "footer",
            fontName="Helvetica",
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER,
        ),
    }


def _build_header_table(pulse: PulsePayload, s: dict):
    """Build the branded header as a full-width coloured banner."""
    app_name = pulse.metadata.get("app_name", "IndMoney")
    source   = pulse.metadata.get("source", "")
    reviews  = pulse.metadata.get("review_count", "")
    date_str = pulse.metadata.get("generated_at", "")

    title_p = Paragraph(f"{app_name} — Weekly Product Pulse", s["title"])
    sub_p   = Paragraph(f"{source}  ·  {reviews} reviews  ·  {date_str}", s["subtitle"])

    content = [[title_p], [sub_p]]
    tbl = Table(content, colWidths=[170 * mm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRAND_BLUE),
        ("TOPPADDING",    (0, 0), (0, 0), 14),
        ("BOTTOMPADDING", (0, -1), (0, -1), 12),
        ("LEFTPADDING",   (0, 0), (-1, -1), 16),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 16),
        ("ROUNDEDCORNERS", [6, 6, 0, 0]),
    ]))
    return tbl


def _build_theme_table(pulse: PulsePayload, s: dict):
    """Build the themes table with alternating rows."""
    header = [
        Paragraph("<b>#</b>", s["body"]),
        Paragraph("<b>Theme</b>", s["body"]),
        Paragraph("<b>Reviews</b>", s["body"]),
        Paragraph("<b>Top 3</b>", s["body"]),
    ]
    rows = [header]
    for i, t in enumerate(pulse.themes, 1):
        star = "★" if t.is_top_3 else ""
        desc = t.description if len(t.description) <= 80 else t.description[:80] + "…"
        theme_cell = [
            Paragraph(t.label, s["theme_label"]),
            Paragraph(desc, s["theme_desc"]),
        ]
        # Use a nested table for the theme cell to stack label + description
        inner = Table([[theme_cell[0]], [theme_cell[1]]], colWidths=[100 * mm])
        inner.setStyle(TableStyle([
            ("TOPPADDING",    (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ]))

        rows.append([
            Paragraph(str(i), s["body"]),
            inner,
            Paragraph(str(t.review_count), s["body"]),
            Paragraph(f"<font color='#F4801A'><b>{star}</b></font>", s["body"]),
        ])

    col_widths = [10 * mm, 108 * mm, 22 * mm, 16 * mm]
    tbl = Table(rows, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0), BRAND_BLUE),
        ("TEXTCOLOR",      (0, 0), (-1, 0), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
        ("GRID",           (0, 0), (-1, -1), 0.3, MID_GREY),
        ("TOPPADDING",     (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 6),
        ("LEFTPADDING",    (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 6),
        ("VALIGN",         (0, 0), (-1, -1), "TOP"),
        ("ALIGN",          (2, 0), (2, -1), "CENTER"),
        ("ALIGN",          (3, 0), (3, -1), "CENTER"),
    ]))
    return tbl


def _build_quotes_section(pulse: PulsePayload, s: dict) -> list:
    """Build quotes grouped by top theme — 3 quotes per theme."""
    elements = []
    elements.append(Paragraph("User Quotes (Top Themes)", s["section_header"]))

    # Group quotes by theme
    quotes_by_theme = {}
    for q in pulse.quotes:
        quotes_by_theme.setdefault(q.theme_label, []).append(q)

    for theme_label, quotes in quotes_by_theme.items():
        block = []
        block.append(Paragraph(f"● {theme_label}", s["quote_theme"]))
        for q in quotes[:3]:  # Max 3 per theme
            stars = "★" * q.rating + "☆" * (5 - q.rating)
            block.append(Paragraph(f"❝ {q.text}", s["quote_text"]))
            block.append(Paragraph(f"{stars}  (Rating: {q.rating}/5)", s["quote_rating"]))
        elements.append(KeepTogether(block))

    return elements


def _build_actions_section(pulse: PulsePayload, s: dict) -> list:
    """Build the action items section."""
    elements = []
    elements.append(Paragraph("Action Items", s["section_header"]))

    for item in pulse.action_items:
        block = [
            Paragraph(f"[{item.id}]  {item.title}", s["action_title"]),
            Paragraph(item.description, s["action_desc"]),
            Paragraph(f"Linked theme: {item.linked_theme}", s["action_linked"]),
        ]
        elements.append(KeepTogether(block))

    return elements


def export_pdf(pulse: PulsePayload, output_dir: str = "exports") -> dict:
    """
    Export a PulsePayload to a branded, multi-page PDF.

    Args:
        pulse: PulsePayload to export.
        output_dir: Directory to save the PDF.

    Returns:
        dict with keys: success (bool), pdf_path (str), error (str).
    """
    try:
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        date_str = pulse.metadata.get("generated_at", datetime.now().strftime("%d-%b-%Y %H:%M"))
        safe_date = date_str.split(" ")[0].replace("-", "_")
        filename = f"IndMoney_Pulse_{safe_date}.pdf"
        pdf_path = os.path.join(output_dir, filename)

        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=18 * mm,
            bottomMargin=18 * mm,
        )

        s = _styles()
        story = []

        # ── Header banner ────────────────────────────────────────────────
        story.append(_build_header_table(pulse, s))
        # Orange accent bar
        story.append(HRFlowable(width="100%", thickness=3, color=BRAND_ORANGE, spaceAfter=14))

        # ── Summary ──────────────────────────────────────────────────────
        story.append(Paragraph("Summary", s["section_header"]))
        for para in str(pulse.summary_note).split("\n"):
            if para.strip():
                story.append(Paragraph(para.strip(), s["body"]))

        # ── Themes table ─────────────────────────────────────────────────
        story.append(Paragraph("Themes", s["section_header"]))
        story.append(_build_theme_table(pulse, s))

        # ── Quotes (3 per top theme) ─────────────────────────────────────
        story.extend(_build_quotes_section(pulse, s))

        # ── Action Items ─────────────────────────────────────────────────
        story.extend(_build_actions_section(pulse, s))

        # ── Footer ───────────────────────────────────────────────────────
        story.append(Spacer(1, 16))
        story.append(HRFlowable(width="100%", thickness=0.5, color=MID_GREY))
        story.append(Spacer(1, 6))
        story.append(Paragraph(pulse.footer, s["footer"]))

        doc.build(story)
        return {"success": True, "pdf_path": pdf_path}

    except Exception as e:
        return {"success": False, "pdf_path": "", "error": str(e)}
