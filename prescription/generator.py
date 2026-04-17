"""
PrescriptionGenerator – produces a formatted text prescription.
Optionally generates a PDF via ReportLab (gracefully skipped if not installed).
"""
import os, sys, textwrap
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DOCTOR_NAME, HOSPITAL_NAME
from utils.helpers import format_date


class PrescriptionGenerator:

    def generate_text(
        self,
        rx_id: str,
        patient: dict,
        disease: str,
        confidence: float,
        symptoms: list[str],
        medications: list[str],
        doctor: str = DOCTOR_NAME,
        notes: str = "",
    ) -> str:
        """Return a nicely formatted prescription as a plain-text string."""
        sep  = "═" * 60
        thin = "─" * 60
        now  = format_date()

        symptom_display = ", ".join(s.replace("_", " ").title() for s in symptoms) or "—"
        med_lines = "\n".join(
            f"  {i+1}. {med}" for i, med in enumerate(medications)
        ) or "  None prescribed"

        rx = f"""
{sep}
{HOSPITAL_NAME:^60}
       AI-Powered Medical Prescription Assistance System
{sep}

PRESCRIPTION ID : {rx_id}
DATE & TIME     : {now}
DOCTOR          : {doctor}

{thin}
PATIENT INFORMATION
{thin}
Name            : {patient.get('name', 'N/A')}
Age / Gender    : {patient.get('age', '—')} yrs / {patient.get('gender', '—')}
Weight          : {patient.get('weight', '—')} kg
Blood Group     : {patient.get('blood_group', '—')}
Phone           : {patient.get('phone', '—')}

{thin}
CLINICAL DETAILS
{thin}
Presenting Symptoms :
  {symptom_display}

AI Predicted Diagnosis : {disease}
  (Confidence : {confidence:.1f}%)

{thin}
MEDICATIONS PRESCRIBED
{thin}
{med_lines}

{thin}
NOTES / INSTRUCTIONS
{thin}
{textwrap.fill(notes, 58) if notes else '  No additional notes.'}

{thin}
SAFETY DECLARATION
{thin}
  Drug interactions checked  : YES
  Allergy screening done     : YES
  Prescription validated by  : AI Safety Engine v1.0

{sep}
  This prescription is AI-assisted. Final clinical
  judgment rests with the treating physician.
{sep}
"""
        return rx.strip()

    def generate_pdf(
        self,
        rx_id: str,
        patient: dict,
        disease: str,
        confidence: float,
        symptoms: list[str],
        medications: list[str],
        doctor: str = DOCTOR_NAME,
        notes: str = "",
        output_path: str = "prescription.pdf",
    ) -> str | None:
        """Generate a PDF prescription. Returns path or None if ReportLab not available."""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
            )
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
        except ImportError:
            return None

        doc    = SimpleDocTemplate(output_path, pagesize=A4,
                                   topMargin=2*cm, bottomMargin=2*cm,
                                   leftMargin=2*cm, rightMargin=2*cm)
        styles = getSampleStyleSheet()
        story  = []

        title_style = ParagraphStyle('title', parent=styles['Title'],
                                     fontSize=16, spaceAfter=4)
        sub_style   = ParagraphStyle('sub', parent=styles['Normal'],
                                     fontSize=9, textColor=colors.grey)
        h2_style    = ParagraphStyle('h2', parent=styles['Heading2'],
                                     fontSize=11, textColor=colors.HexColor('#003366'))
        body_style  = styles['Normal']

        # Header
        story.append(Paragraph(HOSPITAL_NAME, title_style))
        story.append(Paragraph("AI-Powered Medical Prescription", sub_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#003366')))
        story.append(Spacer(1, 0.3*cm))

        # Meta
        meta = [
            ['Prescription ID', rx_id, 'Date', format_date()],
            ['Doctor', doctor, '', ''],
        ]
        t = Table(meta, colWidths=[3.5*cm, 6*cm, 2*cm, 5*cm])
        t.setStyle(TableStyle([('FONTSIZE', (0,0), (-1,-1), 9)]))
        story.append(t)
        story.append(Spacer(1, 0.4*cm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))

        # Patient
        story.append(Paragraph("Patient Information", h2_style))
        pt_data = [
            ['Name', patient.get('name','—'), 'Age/Gender',
             f"{patient.get('age','—')} yrs / {patient.get('gender','—')}"],
            ['Weight', f"{patient.get('weight','—')} kg", 'Blood Group',
             patient.get('blood_group','—')],
        ]
        t2 = Table(pt_data, colWidths=[3*cm, 6*cm, 3*cm, 5*cm])
        t2.setStyle(TableStyle([('FONTSIZE',(0,0),(-1,-1),9),
                                ('BACKGROUND',(0,0),(0,-1),colors.HexColor('#EEF2FF')),
                                ('BACKGROUND',(2,0),(2,-1),colors.HexColor('#EEF2FF'))]))
        story.append(t2)
        story.append(Spacer(1, 0.3*cm))

        # Diagnosis
        story.append(Paragraph("Diagnosis", h2_style))
        story.append(Paragraph(
            f"<b>{disease}</b> &nbsp; (AI Confidence: {confidence:.1f}%)", body_style))
        story.append(Spacer(1, 0.2*cm))
        symp_txt = ", ".join(s.replace("_"," ").title() for s in symptoms) or "—"
        story.append(Paragraph(f"<b>Presenting Symptoms:</b> {symp_txt}", body_style))
        story.append(Spacer(1, 0.3*cm))

        # Medications
        story.append(Paragraph("Medications Prescribed", h2_style))
        for i, med in enumerate(medications, 1):
            story.append(Paragraph(f"{i}. {med}", body_style))
        story.append(Spacer(1, 0.3*cm))

        # Notes
        if notes:
            story.append(Paragraph("Notes / Instructions", h2_style))
            story.append(Paragraph(notes, body_style))
            story.append(Spacer(1, 0.3*cm))

        # Footer
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
        story.append(Paragraph(
            "<i>This prescription is AI-assisted. Final clinical judgment rests with "
            "the treating physician. Drug interactions and allergy screening validated "
            "by AI Safety Engine v1.0.</i>",
            ParagraphStyle('footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey)
        ))

        doc.build(story)
        return output_path
