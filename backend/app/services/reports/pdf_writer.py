import io
from typing import Any, List
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and print 'Page X of Y' in the document footer."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Footer divider line
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(36, 30, self._pagesize[0] - 36, 30)

        # Footer text
        self.drawString(
            36,
            18,
            "BloodLink — Blood Bank Management & Availability Prediction System | Confidential",
        )
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(self._pagesize[0] - 36, 18, page_str)
        self.restoreState()


def generate_pdf(
    title: str,
    columns: List[str],
    rows: List[List[Any]],
    generated_at_str: str,
) -> bytes:
    """
    Generate an executive PDF report using ReportLab.
    - Title banner and generation timestamp
    - Landscape orientation
    - Repeated table header across page breaks
    - Page X of Y numbering
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=45,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=4,
    )

    meta_style = ParagraphStyle(
        "ReportMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=14,
    )

    cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1e293b"),
    )

    header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.white,
    )

    elements = []

    # Title & Metadata
    title_text = f"<font color='#dc2626'>BloodLink</font> — {title}"
    elements.append(Paragraph(title_text, title_style))
    elements.append(
        Paragraph(
            f"Generated on {generated_at_str} | Official Audit Export",
            meta_style,
        )
    )

    # Format table data
    formatted_headers = [Paragraph(str(col).replace("_", " ").upper(), header_style) for col in columns]
    formatted_rows = []

    for row in rows:
        formatted_row = [Paragraph(str(val) if val is not None else "—", cell_style) for val in row]
        formatted_rows.append(formatted_row)

    if not formatted_rows:
        # Empty table placeholder row
        empty_row = [Paragraph("No records found", cell_style)] * len(columns)
        formatted_rows = [empty_row]

    table_data = [formatted_headers] + formatted_rows

    report_table = Table(table_data, repeatRows=1)
    report_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#ffffff"), colors.HexColor("#f8fafc")]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ]
        )
    )

    elements.append(report_table)

    doc.build(elements, canvasmaker=NumberedCanvas)
    return buffer.getvalue()
