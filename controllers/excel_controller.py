"""
==================================================================
 EXCEL CONTROLLER
==================================================================
Handles import / export of student data via Excel files using
pandas + openpyxl. Performs validation, duplicate detection and
update-existing logic.
==================================================================
"""

import pandas as pd
from datetime import datetime
from models.student import Student

# Mapping between Excel column headers and database field names
EXCEL_TO_DB = {
    "Matricule": "matricule",
    "Eleve Nom": "eleve_nom",
    "Eleve Prénom": "eleve_prenom",
    "Eleve Prenom": "eleve_prenom",  # tolerate missing accent
    "Mere": "mere",
    "Père": "pere",
    "Pere": "pere",
    "Date of birth": "date_of_birth",
    "City of birth": "city_of_birth",
    "Adress": "adresse",
    "Adresse": "adresse",
    "Père telephone": "pere_telephone",
    "Pere telephone": "pere_telephone",
    "Mere telephone": "mere_telephone",
    "Classe": "classe",
    "Inscription": "inscription",
    "Transport (Y/N)": "transport_yn",
    "Transport": "transport",
    "Mensualité": "mensualite",
    "Mensualite": "mensualite",
    "Note/Date": "note_date",
}

DB_TO_EXCEL = {
    "matricule": "Matricule",
    "eleve_nom": "Eleve Nom",
    "eleve_prenom": "Eleve Prénom",
    "mere": "Mere",
    "pere": "Père",
    "date_of_birth": "Date of birth",
    "city_of_birth": "City of birth",
    "adresse": "Adress",
    "pere_telephone": "Père telephone",
    "mere_telephone": "Mere telephone",
    "classe": "Classe",
    "inscription": "Inscription",
    "transport_yn": "Transport (Y/N)",
    "transport": "Transport",
    "mensualite": "Mensualité",
    "note_date": "Note/Date",
}

REQUIRED_FIELDS = ["matricule", "eleve_nom", "eleve_prenom"]


class ExcelController:
    """Static helper class for Excel import / export operations."""

    # ------------------------------------------------------------
    # IMPORT
    # ------------------------------------------------------------
    @staticmethod
    def import_excel(file_path: str, annee_scolaire: str):
        """
        Read an Excel file and import students into the database.

        Returns a result dict with statistics and any row-level errors:
        {
            "total_rows": int,
            "created": int,
            "updated": int,
            "skipped": int,
            "errors": [ {"row": int, "message": str}, ... ]
        }
        """
        result = {
            "total_rows": 0,
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "errors": [],
        }

        try:
            df = pd.read_excel(file_path)
        except Exception as e:
            result["errors"].append({"row": 0, "message": f"Impossible de lire le fichier: {e}"})
            return result

        # Normalize column names (strip whitespace)
        df.columns = [str(c).strip() for c in df.columns]

        result["total_rows"] = len(df)

        for idx, row in df.iterrows():
            row_num = idx + 2  # +1 for 0-index, +1 for header row
            try:
                data = ExcelController._row_to_db_dict(row)

                # Validation: required fields
                missing = [f for f in REQUIRED_FIELDS if not data.get(f)]
                if missing:
                    result["errors"].append({
                        "row": row_num,
                        "message": f"Champs requis manquants: {', '.join(missing)}"
                    })
                    result["skipped"] += 1
                    continue

                data["annee_scolaire"] = annee_scolaire

                # Duplicate detection (matricule + annee_scolaire)
                existing = Student.get_by_matricule_year(data["matricule"], annee_scolaire)

                if existing:
                    Student.update(existing["id"], data)
                    result["updated"] += 1
                else:
                    Student.create(data)
                    result["created"] += 1

            except Exception as e:
                result["errors"].append({"row": row_num, "message": str(e)})
                result["skipped"] += 1

        return result

    @staticmethod
    def _row_to_db_dict(row) -> dict:
        """Convert a pandas Series (Excel row) into a DB-ready dict."""
        data = {}
        for excel_col, db_field in EXCEL_TO_DB.items():
            if excel_col in row.index:
                value = row[excel_col]

                # Handle NaN
                if pd.isna(value):
                    value = None

                # Special handling per field
                if db_field == "matricule" and value is not None:
                    # Keep as string but strip trailing .0 from floats
                    if isinstance(value, float) and value == int(value):
                        value = str(int(value))
                    else:
                        value = str(value).strip()

                elif db_field in ("inscription", "transport", "mensualite"):
                    try:
                        value = float(value) if value is not None else 0.0
                    except (ValueError, TypeError):
                        value = 0.0

                elif db_field == "transport_yn":
                    if value is None:
                        value = "No"
                    else:
                        v = str(value).strip().lower()
                        value = "Yes" if v in ("yes", "y", "oui", "1", "true") else "No"

                elif db_field in ("date_of_birth", "note_date"):
                    if value is not None:
                        if isinstance(value, (pd.Timestamp, datetime)):
                            value = value.strftime("%Y-%m-%d")
                        else:
                            value = str(value).strip()

                elif value is not None and isinstance(value, str):
                    value = value.strip()

                # Only set if not None to avoid overwriting field
                if db_field not in data or value is not None:
                    data[db_field] = value

        return data

    # ------------------------------------------------------------
    # EXPORT
    # ------------------------------------------------------------
    @staticmethod
    def export_excel(file_path: str, students: list):
        """Export a list of student dicts to an Excel file."""
        rows = []
        for s in students:
            row = {}
            for db_field, excel_col in DB_TO_EXCEL.items():
                row[excel_col] = s.get(db_field, "")
            rows.append(row)

        df = pd.DataFrame(rows, columns=list(DB_TO_EXCEL.values()))
        df.to_excel(file_path, index=False, sheet_name="Élèves")
        return file_path

    # ------------------------------------------------------------
    # SAMPLE TEMPLATE GENERATION
    # ------------------------------------------------------------
    @staticmethod
    def generate_template(file_path: str):
        """Create an empty Excel template with the correct columns."""
        columns = list(EXCEL_TO_DB.keys())
        # Remove duplicate alias columns (keep first occurrence per db field)
        seen_db_fields = set()
        clean_columns = []
        for col in columns:
            db_field = EXCEL_TO_DB[col]
            if db_field not in seen_db_fields:
                clean_columns.append(col)
                seen_db_fields.add(db_field)

        df = pd.DataFrame(columns=clean_columns)
        df.to_excel(file_path, index=False, sheet_name="Élèves")
        return file_path
