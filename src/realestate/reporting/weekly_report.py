"""Automated weekly PDF market report.

Generates a self-contained PDF summarising the current state of the Dubai market:
headline sales stats, the custom price-index top movers, off-plan vs ready
inventory, the strongest developers, a Prophet forecast snapshot, and any flagged
anomalies. Built with ReportLab so it runs head-less in Docker / CI.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
)

from ..config import PROJECT_ROOT
from ..logging_config import get_logger
from ..ingestion import ingest
from ..cleaning import clean_transactions, clean_projects
from ..analysis import market, developers, anomaly
from ..analysis.projects_analysis import offplan_vs_ready

log = get_logger(__name__)

# --- Arabic text rendering -------------------------------------------------- #
# Developer names in the DLD data are Arabic. We register the first available
# Arabic-capable TrueType font (Linux Noto, Windows Arial/Tahoma, macOS) and
# shape the text right-to-left. If no Arabic font is present we transliterate to
# Latin so names are always legible (never tofu boxes).
import os as _os
from reportlab.pdfbase import pdfmetrics as _pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont as _TTFont

_ARABIC_FONT = None
_ARABIC_CANDIDATES = [
    "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf",
    "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf",
    "/usr/share/fonts/truetype/fonts-noto/NotoSansArabic-Regular.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/tahoma.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
]
for _cand in _ARABIC_CANDIDATES:
    if _os.path.exists(_cand):
        try:
            _pdfmetrics.registerFont(_TTFont("AppArabic", _cand))
            _ARABIC_FONT = "AppArabic"
            break
        except Exception:
            continue


def ar(text) -> str:
    """Make Arabic text render in the PDF: shape RTL if an Arabic font is
    registered, otherwise transliterate to Latin."""
    s = str(text)
    if not any("\u0600" <= ch <= "\u06FF" for ch in s):
        return s
    if _ARABIC_FONT:
        import arabic_reshaper
        from bidi.algorithm import get_display
        return get_display(arabic_reshaper.reshape(s))
    from unidecode import unidecode
    return unidecode(s)


DEV_FONT = _ARABIC_FONT or "Helvetica"

NAVY = colors.HexColor("#0B2545")
GOLD = colors.HexColor("#C5A253")


def _aed(x: float) -> str:
    if x >= 1e9:
        return f"AED {x/1e9:.2f}B"
    if x >= 1e6:
        return f"AED {x/1e6:.1f}M"
    return f"AED {x:,.0f}"


def _table(data, col_widths=None, body_font="Helvetica") -> Table:
    t = Table(data, colWidths=col_widths, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), body_font),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F4F8")]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def generate_report(output_path: str | Path | None = None) -> Path:
    output_path = Path(output_path) if output_path else (
        PROJECT_ROOT / "artifacts" / "reports" /
        f"weekly_report_{datetime.now():%Y%m%d}.pdf"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    ing = ingest()
    tx = clean_transactions(ing.transactions)
    pr = clean_projects(ing.projects)

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Title"], textColor=NAVY, fontSize=20)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], textColor=NAVY)
    body = styles["BodyText"]

    story = []
    story.append(Paragraph("Dubai Real Estate - Weekly Market Report", h1))
    story.append(Paragraph(
        f"Generated {datetime.now():%d %B %Y}", ParagraphStyle(
            "sub", parent=body, textColor=GOLD, fontSize=10)))
    story.append(Spacer(1, 0.5 * cm))

    # --- Headline sales stats (latest available quarter) ---
    vol = market.volume_trends(tx, "Sales").sort_values("period")
    latest = vol.iloc[-1]
    prev = vol.iloc[-2] if len(vol) > 1 else latest
    yoy = vol.iloc[-5] if len(vol) >= 5 else latest
    story.append(Paragraph("Headline Sales Activity", h2))
    story.append(_table([
        ["Metric", "Latest", "QoQ", "YoY"],
        ["Period", str(latest["period_label"]), str(prev["period_label"]), str(yoy["period_label"])],
        ["Transactions", f"{latest['count']:,.0f}",
         f"{(latest['count']/prev['count']-1)*100:+.1f}%",
         f"{(latest['count']/yoy['count']-1)*100:+.1f}%"],
        ["Sales value", _aed(latest["value_aed"]),
         f"{(latest['value_aed']/prev['value_aed']-1)*100:+.1f}%",
         f"{(latest['value_aed']/yoy['value_aed']-1)*100:+.1f}%"],
    ], col_widths=[4 * cm, 4 * cm, 3 * cm, 3 * cm]))
    story.append(Spacer(1, 0.4 * cm))

    # --- Price index top movers ---
    idx = market.price_index(tx, "Sales")
    movers = []
    for ptype, g in idx.groupby("property_type"):
        g = g.dropna(subset=["index_value"]).sort_values("period")
        if len(g) >= 2:
            change = g["index_value"].iloc[-1] - g["index_value"].iloc[-2]
            movers.append((ptype, g["index_value"].iloc[-1], change))
    movers.sort(key=lambda r: r[2], reverse=True)
    story.append(Paragraph("Custom Price Index - Latest Movers", h2))
    story.append(_table(
        [["Property type", "Index", "QoQ change"]]
        + [[m[0], f"{m[1]:.1f}", f"{m[2]:+.1f}"] for m in movers],
        col_widths=[5 * cm, 4 * cm, 4 * cm]))
    story.append(Spacer(1, 0.4 * cm))

    # --- Off-plan vs ready ---
    ovr = offplan_vs_ready(pr)
    story.append(Paragraph("Off-plan vs Ready Inventory", h2))
    story.append(_table(
        [["Segment", "Projects", "Units", "Avg completion %"]]
        + [[r["segment"], f"{r['n_projects']:,}", f"{r['total_units']:,}",
            f"{r['avg_completion']:.1f}"] for _, r in ovr.iterrows()],
        col_widths=[4 * cm, 3.5 * cm, 4 * cm, 4 * cm]))
    story.append(Spacer(1, 0.4 * cm))

    # --- Top developers ---
    rep = developers.developer_reputation(pr, min_projects=3).head(5)
    story.append(Paragraph("Top Developers by Reputation", h2))
    story.append(_table(
        [["Developer", "Projects", "Delivered %", "Score"]]
        + [[ar(str(r["developer_name"])[:40]), f"{int(r['n_projects'])}",
            f"{r['delivered_rate']:.0f}", f"{r['reputation_score']:.1f}"]
           for _, r in rep.iterrows()],
        col_widths=[7 * cm, 2.5 * cm, 3 * cm, 2.5 * cm], body_font=DEV_FONT))
    story.append(Spacer(1, 0.4 * cm))

    # --- Forecast snapshot (optional) ---
    try:
        from ..models.forecast import forecast_property_type
        fc = forecast_property_type(tx, "Units", periods=1)
        nxt = fc[fc.is_forecast].iloc[0]
        story.append(Paragraph("Forecast Snapshot - Units (next quarter)", h2))
        story.append(Paragraph(
            f"Projected average sale value: {_aed(nxt['yhat'])} "
            f"(80% CI {_aed(nxt['yhat_lower'])} - {_aed(nxt['yhat_upper'])}).", body))
        story.append(Spacer(1, 0.4 * cm))
    except Exception as exc:  # noqa: BLE001
        log.warning("forecast snapshot skipped: %s", exc)

    # --- Anomalies ---
    anom = anomaly.detect_transaction_anomalies(tx)
    n_anom = int(anom["is_anomaly"].sum())
    story.append(Paragraph("Flagged Market Anomalies", h2))
    story.append(Paragraph(
        f"{n_anom} unusual quarter/property-type observations flagged by the "
        f"Isolation Forest model.", body))
    if n_anom:
        top = anom[anom["is_anomaly"]].head(5)
        story.append(_table(
            [["Period", "Type", "Avg value/txn", "Score"]]
            + [[r["period_label"], r["property_type"], _aed(r["avg_value_per_txn"]),
                f"{r['anomaly_score']:.2f}"] for _, r in top.iterrows()],
            col_widths=[3.5 * cm, 3.5 * cm, 4 * cm, 3 * cm]))

    SimpleDocTemplate(
        str(output_path), pagesize=A4,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        leftMargin=1.8 * cm, rightMargin=1.8 * cm,
    ).build(story)
    log.info("Weekly report written -> %s", output_path)
    return output_path


def main() -> None:
    from ..logging_config import configure_logging
    configure_logging()
    print(generate_report())


if __name__ == "__main__":
    main()
