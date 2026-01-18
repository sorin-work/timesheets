"""Invoice PDF rendering with reportlab."""

from decimal import Decimal
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from timesheets.models import Invoice, User
from timesheets.services.money import format_money

STATUS_LABELS = {"draft": "DRAFT", "sent": "", "paid": "PAID", "overdue": "OVERDUE"}


def _multiline(text: str | None) -> str:
    return "<br/>".join(escape(line) for line in (text or "").splitlines())


def _hours(value: Decimal) -> str:
    return f"{value:.2f}"


def render_invoice_pdf(invoice: Invoice, user: User) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"Invoice {invoice.number}",
        author=user.business_name or user.name,
    )
    styles = getSampleStyleSheet()
    small = ParagraphStyle("small", parent=styles["Normal"], fontSize=9, leading=12)
    right = ParagraphStyle("right", parent=small, alignment=2)
    money = lambda amount: format_money(amount, invoice.currency)  # noqa: E731

    story = []
    label = STATUS_LABELS.get(invoice.display_status, "")
    title = f"Invoice {escape(invoice.number)}"
    if label:
        title += f' <font color="#b91c1c" size="12">{label}</font>'
    story.append(Paragraph(title, styles["Title"]))

    seller = (
        f"<b>{escape(user.business_name or user.name)}</b><br/>{_multiline(user.business_address)}"
    )
    if user.tax_id:
        seller += f"<br/>Tax ID: {escape(user.tax_id)}"
    buyer = f"<b>{escape(invoice.client.name)}</b><br/>{_multiline(invoice.client.address)}"
    dates = f"Issued: {invoice.issue_date:%d %b %Y}<br/>Due: {invoice.due_date:%d %b %Y}"
    if invoice.period_start and invoice.period_end:
        dates += f"<br/>Period: {invoice.period_start:%d %b} - {invoice.period_end:%d %b %Y}"
    header = Table(
        [
            [Paragraph("From", small), Paragraph("Bill to", small), ""],
            [Paragraph(seller, small), Paragraph(buyer, small), Paragraph(dates, right)],
        ],
        colWidths=[62 * mm, 62 * mm, 50 * mm],
    )
    header.setStyle(
        TableStyle(
            [("VALIGN", (0, 0), (-1, -1), "TOP"), ("TEXTCOLOR", (0, 0), (-1, 0), colors.grey)]
        )
    )
    story += [header, Spacer(1, 10 * mm)]

    rows = [["Description", "Hours", "Rate", "Amount"]]
    for line in invoice.lines:
        rows.append(
            [
                Paragraph(escape(line.description), small),
                _hours(line.quantity),
                money(line.unit_price),
                money(line.amount),
            ]
        )
    rows.append(["", "", "Subtotal", money(invoice.subtotal)])
    for tax in invoice.taxes:
        rows.append(["", "", f"{tax.name} ({tax.rate.normalize():f}%)", money(tax.amount)])
    rows.append(["", "", "Total", money(invoice.total)])

    table = Table(rows, colWidths=[90 * mm, 20 * mm, 32 * mm, 32 * mm], repeatRows=1)
    last = len(rows) - 1
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("LINEBELOW", (0, 0), (-1, 0), 0.75, colors.black),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                (
                    "LINEABOVE",
                    (2, last - len(invoice.taxes) - 1),
                    (-1, last - len(invoice.taxes) - 1),
                    0.5,
                    colors.grey,
                ),
                ("FONTNAME", (2, last), (-1, last), "Helvetica-Bold"),
                ("LINEABOVE", (2, last), (-1, last), 0.75, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(table)

    if invoice.notes:
        story += [Spacer(1, 8 * mm), Paragraph(_multiline(invoice.notes), small)]

    doc.build(story)
    return buffer.getvalue()
