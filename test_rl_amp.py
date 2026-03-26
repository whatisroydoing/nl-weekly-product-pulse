import sys
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph

styles = getSampleStyleSheet()

try:
    p = Paragraph("This is a test UI & UX issue", styles["Normal"])
    print("Success! Paragraph created.")
except Exception as e:
    print(f"FAILED: {e}")
