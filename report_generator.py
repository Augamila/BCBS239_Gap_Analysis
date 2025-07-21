
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime

def generate_pdf_report(org_name, df, score):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 16)
    c.drawString(30, height - 50, "BCBS239 Gap Analysis Report")

    c.setFont("Helvetica", 12)
    c.drawString(30, height - 80, f"Organization: {org_name}")
    c.drawString(30, height - 100, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    c.drawString(30, height - 120, f"Compliance Score: {score}%")
    c.drawString(30, height - 140, " ")

    c.setFont("Helvetica-Bold", 12)
    c.drawString(30, height - 160, "Principle | Score | Status | Feedback")
    c.setFont("Helvetica", 10)
    y = height - 180

    for _, row in df.iterrows():
        line = f"{row['Principle']} | {row['Score']} | {row['Status']} | {row['Feedback'][:50]}"
        c.drawString(30, y, line)
        y -= 15
        if y < 50:
            c.showPage()
            y = height - 50

    c.save()
    buffer.seek(0)
    return buffer
