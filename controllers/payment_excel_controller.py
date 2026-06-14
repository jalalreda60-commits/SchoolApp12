"""
==================================================================
 PAYMENT EXCEL CONTROLLER
==================================================================
Handles import of the "Gestion des Paiements" Excel file.

Expected columns:
  Matricule | Nom | Prénom | Classe | Inscription | Transport |
  Mensualité | Total a payé | Note/Date | Year |
  Septembre | Octobre | Novembre | Décembre | Janvier | Février |
  Mars | Avril | Mai | Juin

Monthly cell values:
  "Payé"  -> student paid for that month            -> STATUS_PAID
  empty   -> student enrolled, not yet paid         -> STATUS_UNPAID
  "NAN"   -> student not enrolled during that month -> STATUS_NAN

Students are created automatically if they do not exist (matched
by matricule + Year), or updated if they already exist. Historical
payments are NOT re-created on every import (to avoid duplicates);
only the monthly status grid and student totals are (re)written.
==================================================================
"""

import math
import pandas as pd
from datetime import datetime

from models.student import Student
from models.payment import Payment
from utils.theme import MONTHS_ORDER, STATUS_PAID, STATUS_UNPAID, STATUS_NAN


REQUIRED_FIELDS = ["matricule", "eleve_nom"]


class PaymentExcelController:
    """Static helper class for importing the payment Excel file."""

    @staticmethod
    def import_excel(file_path: str, default_annee_scolaire: str = None):
        """
        Import students + payment status grid from the payment Excel file.

        Returns a result dict:
        {
            "total_rows": int,
            "students_created": int,
            "students_updated": int,
            "skipped": int,
            "errors": [ {"row": int, "message": str}, ... ]
        }
        """
        result = {
            "total_rows": 0,
            "students_created": 0,
            "students_updated": 0,
            "skipped": 0,
            "errors": [],
        }

        try:
            df = pd.read_excel(file_path)
        except Exception as e:
            result["errors"].append({"row": 0, "message": f"Impossible de lire le fichier: {e}"})
            return result

        df.columns = [str(c).strip() for c in df.columns]
        result["total_rows"] = len(df)

        for idx, row in df.iterrows():
            row_num = idx + 2
            try:
                matricule = PaymentExcelController._clean_matricule(row.get("Matricule"))
                nom = PaymentExcelController._clean_str(row.get("Nom"))
                prenom = PaymentExcelController._clean_str(row.get("Prénom"))
                classe = PaymentExcelController._clean_str(row.get("Classe"))

                if not matricule or not nom:
                    result["errors"].append({
                        "row": row_num,
                        "message": "Matricule et Nom sont obligatoires."
                    })
                    result["skipped"] += 1
                    continue

                annee_scolaire = PaymentExcelController._clean_str(row.get("Year")) or default_annee_scolaire
                if not annee_scolaire:
                    result["errors"].append({
                        "row": row_num,
                        "message": "Année scolaire (Year) manquante et aucune année par défaut fournie."
                    })
                    result["skipped"] += 1
                    continue

                inscription = PaymentExcelController._clean_number(row.get("Inscription"))
                transport = PaymentExcelController._clean_number(row.get("Transport"))
                mensualite = PaymentExcelController._clean_number(row.get("Mensualité"))
                note_date = PaymentExcelController._clean_str(row.get("Note/Date"))

                total_a_payer = inscription + transport

                student_data = {
                    "matricule": matricule,
                    "eleve_nom": nom,
                    "eleve_prenom": prenom,
                    "classe": classe,
                    "inscription": inscription,
                    "transport": transport,
                    "transport_yn": "Yes" if transport > 0 else "No",
                    "mensualite": mensualite,
                    "note_date": note_date,
                    "annee_scolaire": annee_scolaire,
                    "total_a_payer": total_a_payer,
                }

                existing = Student.get_by_matricule_year(matricule, annee_scolaire)
                if existing:
                    Student.update(existing["id"], student_data)
                    student_id = existing["id"]
                    result["students_updated"] += 1
                else:
                    student_data["date_creation"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    student_id = Student.create(student_data)
                    result["students_created"] += 1

                # ---- Monthly status grid ----
                status_map = {}
                for month in MONTHS_ORDER:
                    raw_value = row.get(month)
                    status_map[month] = PaymentExcelController._interpret_month_value(raw_value)

                Payment.set_status_bulk(student_id, annee_scolaire, status_map)

            except Exception as e:
                result["errors"].append({"row": row_num, "message": str(e)})
                result["skipped"] += 1

        return result

    # ------------------------------------------------------------
    # VALUE INTERPRETATION HELPERS
    # ------------------------------------------------------------
    @staticmethod
    def _interpret_month_value(value) -> str:
        """
        Interpret a single monthly cell value:
          - "Payé" (any case/accents tolerated)  -> STATUS_PAID
          - "NAN" (string) or NaN/empty           -> depends:
                * literal string "NAN" / "nan"    -> STATUS_NAN
                * empty / NaN / None               -> STATUS_UNPAID
        """
        if value is None:
            return STATUS_UNPAID

        # pandas NaN (float)
        if isinstance(value, float) and math.isnan(value):
            return STATUS_UNPAID

        text = str(value).strip()
        if text == "":
            return STATUS_UNPAID

        lowered = text.lower()
        if lowered in ("nan",):
            return STATUS_NAN
        if "pay" in lowered:  # matches "Payé", "paye", "PAYÉ", etc.
            return STATUS_PAID

        # Unknown value: treat as unpaid but enrolled
        return STATUS_UNPAID

    @staticmethod
    def _clean_str(value) -> str:
        if value is None:
            return ""
        if isinstance(value, float) and math.isnan(value):
            return ""
        return str(value).strip()

    @staticmethod
    def _clean_matricule(value) -> str:
        if value is None:
            return ""
        if isinstance(value, float):
            if math.isnan(value):
                return ""
            if value == int(value):
                return str(int(value))
        return str(value).strip()

    @staticmethod
    def _clean_number(value) -> float:
        if value is None:
            return 0.0
        if isinstance(value, str):
            value = value.replace(",", ".").strip()
            if value == "":
                return 0.0
        try:
            v = float(value)
            if math.isnan(v):
                return 0.0
            return v
        except (ValueError, TypeError):
            return 0.0
