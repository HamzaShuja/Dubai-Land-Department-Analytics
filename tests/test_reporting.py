"""Weekly PDF report generation."""
from pypdf import PdfReader

from realestate.reporting.weekly_report import generate_report


def test_generate_report(tmp_path):
    out = tmp_path / "report.pdf"
    path = generate_report(out)
    assert path.exists()
    reader = PdfReader(str(path))
    assert len(reader.pages) >= 1
    text = "\n".join(p.extract_text() or "" for p in reader.pages)
    assert "Dubai Real Estate" in text
    assert "Price Index" in text
