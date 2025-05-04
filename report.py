import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from PIL import Image as PILImage
from datetime import datetime
import io

def generate_report(image_path: str, original_filename: str, num_sheep: int, timestamp: datetime, duration_seconds: float, output_path: str):
    doc = SimpleDocTemplate(output_path, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=60, bottomMargin=40)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    title = Paragraph("Sheep Detection Report", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 20))

    # Info Table
    data = [
        ["Image Filename", original_filename],
        ["Date & Time", timestamp.strftime("%Y-%m-%d %H:%M:%S")],
        ["Number of Sheep", str(num_sheep)],
        ["Processing Duration", f"{duration_seconds:.2f} seconds"]
    ]
    table = Table(data, colWidths=[2.5 * inch, 3.5 * inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))

    # Image insertion
    try:
        pil_img = PILImage.open(image_path)
        img_width, img_height = pil_img.size
        max_width = 5.5 * inch
        aspect = img_height / img_width
        buffer = io.BytesIO()
        pil_img.save(buffer, format='PNG')
        buffer.seek(0)
        report_img = Image(buffer, width=max_width, height=(max_width * aspect))
        elements.append(report_img)
    except Exception as e:
        error_msg = Paragraph(f"Error loading image: {str(e)}", styles['Normal'])
        elements.append(error_msg)

    # Build PDF
    doc.build(elements)
