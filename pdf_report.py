# pdf_report.py
# Generates a branded PDF report using reportlab and matplotlib
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Frame, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
import io
import matplotlib.pyplot as plt
from config_loader import AIR_SIAL_BLUE

def create_summary_chart(stats: dict):
    labels = list(stats.keys())
    values = list(stats.values())
    fig, ax = plt.subplots(figsize=(6,2.5))
    ax.bar(labels, values, color=AIR_SIAL_BLUE)
    ax.set_title("Report Summary")
    buf = io.BytesIO()
    plt.tight_layout()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return buf

def generate_pdf(report_data: dict):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Header
    c.setFillColor(AIR_SIAL_BLUE)
    c.rect(0, height-60, width, 60, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(20, height-42, "Air Sial Safety Management System")
    c.setFont("Helvetica", 10)
    c.drawString(20, height-56, f"Report ID: {report_data.get('report_id','-')}")

    # Summary
    styles = getSampleStyleSheet()
    styleN = styles["Normal"]
    p = Paragraph(report_data.get("summary","No summary provided."), styleN)
    f = Frame(20, height-300, width-40, 200, showBoundary=0)
    f.addFromList([p], c)

    # Chart
    chart_buf = create_summary_chart(report_data.get("stats", {}))
    c.drawImage(chart_buf, 20, height-420, width=width-40, height=100)

    # Table of entries
    entries = report_data.get("entries", [])
    if entries:
        keys = list(entries[0].keys())
        data = [keys] + [[str(row.get(k,"")) for k in keys] for row in entries]
        table = Table(data, colWidths=[(width-40)/len(keys)]*len(keys))
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), AIR_SIAL_BLUE),
            ('TEXTCOLOR',(0,0),(-1,0),colors.white),
            ('GRID',(0,0),(-1,-1),0.5,colors.grey),
            ('FONT',(0,0),(-1,-1),'Helvetica',8),
        ]))
        table.wrapOn(c, width-40, 200)
        table.drawOn(c, 20, 60)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer
