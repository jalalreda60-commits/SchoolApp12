"""
==================================================================
 RECEIPT PDF GENERATOR
==================================================================
Generates a professional PDF payment receipt using ReportLab.
Includes school logo (if available), school name, receipt number,
student info, payment details and a signature area.
==================================================================
"""

import os
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

from database.db_manager import db_manager, BASE_DIR


PRIMARY_COLOR = colors.HexColor("#2563EB")
SUCCESS_COLOR = colors.HexColor("#22C55E")
MUTED_COLOR = colors.HexColor("#64748B")
BORDER_COLOR = colors.HexColor("#E2E8F0")


def generate_receipt_pdf(payment_data: dict, student_data: dict, output_path: str = None) -> str:
    """
    Generate a PDF receipt for a payment.

    payment_data keys: receipt_number, payment_type, mois, montant,
                        date_paiement, notes, annee_scolaire, remaining
    student_data keys: matricule, eleve_nom, eleve_prenom, classe

    Returns the absolute path to the generated PDF.
    """
    receipts_dir = os.path.join(BASE_DIR, "exports", "receipts")
    os.makedirs(receipts_dir, exist_ok=True)

    if not output_path:
        filename = f"recu_{payment_data['receipt_number']}.pdf"
        output_path = os.path.join(receipts_dir, filename)

    school_name = db_manager.get_setting("school_name", "Mon Établissement Scolaire")
    logo_path = os.path.join(BASE_DIR, "assets", "icons", "school_emblem.png")

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        topMargin=20 * mm, bottomMargin=20 * mm,
        leftMargin=20 * mm, rightMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        "ReceiptTitle", parent=styles["Title"],
        fontSize=20, textColor=PRIMARY_COLOR, alignment=TA_CENTER,
        spaceAfter=2,
    )
    school_style = ParagraphStyle(
        "SchoolName", parent=styles["Normal"],
        fontSize=14, alignment=TA_CENTER, spaceAfter=10,
        textColor=colors.HexColor("#1E293B"),
    )
    label_style = ParagraphStyle(
        "Label", parent=styles["Normal"],
        fontSize=10, textColor=MUTED_COLOR,
    )
    value_style = ParagraphStyle(
        "Value", parent=styles["Normal"],
        fontSize=11, textColor=colors.HexColor("#1E293B"),
    )
    receipt_no_style = ParagraphStyle(
        "ReceiptNo", parent=styles["Normal"],
        fontSize=11, alignment=TA_RIGHT, textColor=PRIMARY_COLOR,
    )

    # ---- Header: logo + school name ----
    if os.path.exists(logo_path):
        try:
            from PIL import Image as PILImage
            with PILImage.open(logo_path) as pil_img:
                img_w, img_h = pil_img.size
            target_h = 20 * mm
            target_w = target_h * (img_w / img_h)
            logo = Image(logo_path, width=target_w, height=target_h)
            header_table = Table(
                [[logo, Paragraph(f"<b>{school_name}</b>", school_style)]],
                colWidths=[target_w + 5 * mm, None]
            )
            header_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (1, 0), (1, 0), "CENTER"),
            ]))
            story.append(header_table)
        except Exception:
            story.append(Paragraph(f"<b>{school_name}</b>", school_style))
    else:
        story.append(Paragraph(f"<b>{school_name}</b>", school_style))

    story.append(Paragraph("REÇU DE PAIEMENT", title_style))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", color=BORDER_COLOR, thickness=1))
    story.append(Spacer(1, 12))

    # ---- Receipt number + date ----
    meta_table_data = [
        [
            Paragraph(f"<b>N° Reçu :</b> {payment_data['receipt_number']}", value_style),
            Paragraph(f"<b>Date :</b> {payment_data['date_paiement']}", receipt_no_style),
        ]
    ]
    meta_table = Table(meta_table_data, colWidths=[None, None])
    meta_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 14))

    # ---- Student information box ----
    student_info = [
        [Paragraph("<b>Informations Élève</b>", styles["Heading4"]), ""],
        [Paragraph("Matricule", label_style), Paragraph(str(student_data.get("matricule", "")), value_style)],
        [Paragraph("Nom & Prénom", label_style),
         Paragraph(f"{student_data.get('eleve_prenom', '')} {student_data.get('eleve_nom', '')}", value_style)],
        [Paragraph("Classe", label_style), Paragraph(str(student_data.get("classe", "")), value_style)],
        [Paragraph("Année scolaire", label_style), Paragraph(str(payment_data.get("annee_scolaire", "")), value_style)],
    ]
    student_table = Table(student_info, colWidths=[50 * mm, None])
    student_table.setStyle(TableStyle([
        ("SPAN", (0, 0), (1, 0)),
        ("BACKGROUND", (0, 0), (1, 0), colors.HexColor("#EFF6FF")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("BOX", (0, 0), (-1, -1), 0.75, BORDER_COLOR),
    ]))
    story.append(student_table)
    story.append(Spacer(1, 14))

    # ---- Payment details box ----
    mois_display = payment_data.get("mois") or "—"
    payment_info = [
        [Paragraph("<b>Détails du Paiement</b>", styles["Heading4"]), ""],
        [Paragraph("Type de paiement", label_style), Paragraph(str(payment_data.get("payment_type", "")), value_style)],
        [Paragraph("Mois concerné", label_style), Paragraph(mois_display, value_style)],
        [Paragraph("Montant payé", label_style),
         Paragraph(f"<b>{payment_data.get('montant', 0):,.2f} DH</b>".replace(",", " "), value_style)],
    ]

    remaining = payment_data.get("remaining")
    if remaining is not None and remaining > 0:
        payment_info.append([
            Paragraph("Montant restant", label_style),
            Paragraph(f"{remaining:,.2f} DH".replace(",", " "), value_style)
        ])

    payment_table = Table(payment_info, colWidths=[50 * mm, None])
    payment_table.setStyle(TableStyle([
        ("SPAN", (0, 0), (1, 0)),
        ("BACKGROUND", (0, 0), (1, 0), colors.HexColor("#F0FDF4")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("BOX", (0, 0), (-1, -1), 0.75, BORDER_COLOR),
    ]))
    story.append(payment_table)
    story.append(Spacer(1, 14))

    # ---- Notes ----
    notes = payment_data.get("notes") or ""
    if notes.strip():
        story.append(Paragraph("<b>Remarques :</b>", label_style))
        story.append(Paragraph(notes, value_style))
        story.append(Spacer(1, 14))

    story.append(Spacer(1, 30))

    # ---- Signature area ----
    signature_table = Table(
        [
            ["", ""],
            [Paragraph("Signature du Parent / Tuteur", label_style),
             Paragraph("Signature & Cachet de l'Établissement", label_style)],
        ],
        colWidths=[None, None], rowHeights=[25 * mm, None]
    )
    signature_table.setStyle(TableStyle([
        ("LINEABOVE", (0, 1), (0, 1), 0.75, MUTED_COLOR),
        ("LINEABOVE", (1, 1), (1, 1), 0.75, MUTED_COLOR),
        ("ALIGN", (0, 1), (0, 1), "CENTER"),
        ("ALIGN", (1, 1), (1, 1), "CENTER"),
        ("TOPPADDING", (0, 1), (-1, 1), 4),
    ]))
    story.append(signature_table)

    story.append(Spacer(1, 20))
    footer_style = ParagraphStyle(
        "Footer", parent=styles["Normal"], fontSize=8,
        textColor=MUTED_COLOR, alignment=TA_CENTER,
    )
    story.append(Paragraph(
        f"Document généré automatiquement le {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        footer_style
    ))

    doc.build(story)
    return output_path
