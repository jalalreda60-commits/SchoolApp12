"""
==================================================================
 STUDENT CONTROLLER
==================================================================
Business logic layer between the views and the Student model.
Handles validation, re-inscription generation and statistics
aggregation for the dashboard.
==================================================================
"""

from datetime import datetime
from models.student import Student
from database.db_manager import db_manager


class StudentController:

    # ------------------------------------------------------------
    # VALIDATION
    # ------------------------------------------------------------
    @staticmethod
    def validate_student_data(data: dict) -> list:
        """Return a list of validation error messages (empty if valid)."""
        errors = []

        if not data.get("matricule"):
            errors.append("Le matricule est obligatoire.")
        if not data.get("eleve_nom"):
            errors.append("Le nom de l'élève est obligatoire.")
        if not data.get("eleve_prenom"):
            errors.append("Le prénom de l'élève est obligatoire.")
        if not data.get("classe"):
            errors.append("La classe est obligatoire.")

        # Numeric fields validation
        for field, label in [
            ("inscription", "Inscription"),
            ("transport", "Transport"),
            ("mensualite", "Mensualité"),
        ]:
            value = data.get(field, 0)
            try:
                fv = float(value) if value not in (None, "") else 0.0
                if fv < 0:
                    errors.append(f"{label} ne peut pas être négatif.")
            except (ValueError, TypeError):
                errors.append(f"{label} doit être un nombre valide.")

        # Transport YN validation
        tyn = data.get("transport_yn", "No")
        if tyn not in ("Yes", "No"):
            errors.append("Transport (Y/N) doit être 'Yes' ou 'No'.")

        return errors

    # ------------------------------------------------------------
    # CREATE / UPDATE / DELETE wrappers
    # ------------------------------------------------------------
    @staticmethod
    def create_student(data: dict, annee_scolaire: str):
        errors = StudentController.validate_student_data(data)
        if errors:
            return None, errors

        # Check duplicate matricule for the year
        existing = Student.get_by_matricule_year(data["matricule"], annee_scolaire)
        if existing:
            return None, ["Un élève avec ce matricule existe déjà pour cette année scolaire."]

        data["annee_scolaire"] = annee_scolaire
        data["date_creation"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_id = Student.create(data)
        return new_id, []

    @staticmethod
    def update_student(student_id: int, data: dict):
        errors = StudentController.validate_student_data(data)
        if errors:
            return False, errors

        success = Student.update(student_id, data)
        if not success:
            return False, ["Erreur lors de la mise à jour de l'élève."]
        return True, []

    @staticmethod
    def delete_student(student_id: int):
        return Student.delete(student_id)

    @staticmethod
    def generate_matricule():
        return Student.generate_next_matricule()

    # ------------------------------------------------------------
    # RE-INSCRIPTION
    # ------------------------------------------------------------
    @staticmethod
    def generate_reinscriptions(student_ids: list, current_year: str, next_year: str):
        """
        For each selected student id (belonging to current_year),
        create (or update) a record for next_year preserving all
        information except matricule/id/year/statut/date_creation
        which are reset appropriately.

        Returns dict: { "created": int, "updated": int, "skipped": int, "errors": [] }
        """
        result = {"created": 0, "updated": 0, "skipped": 0, "errors": []}

        for sid in student_ids:
            student = Student.get_by_id(sid)
            if not student:
                result["skipped"] += 1
                continue
            if student["annee_scolaire"] != current_year:
                result["skipped"] += 1
                continue

            # Build new record for next year
            new_data = {k: v for k, v in student.items() if k not in ("id",)}
            new_data["annee_scolaire"] = next_year
            new_data["date_creation"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_data["statut"] = "Actif"

            existing = Student.get_by_matricule_year(student["matricule"], next_year)
            if existing:
                Student.update(existing["id"], new_data)
                result["updated"] += 1
            else:
                Student.create(new_data)
                result["created"] += 1

        return result

    @staticmethod
    def get_reinscription_stats(current_year: str, next_year: str):
        total_eligible = Student.count_all(annee_scolaire=current_year, statut="Actif")
        already_reinscribed = Student.count_all(annee_scolaire=next_year)
        return {
            "total_eligible": total_eligible,
            "already_reinscribed": already_reinscribed,
        }

    # ------------------------------------------------------------
    # SETTINGS HELPERS
    # ------------------------------------------------------------
    @staticmethod
    def get_current_year():
        return db_manager.get_setting("current_school_year", "2025/2026")

    @staticmethod
    def get_next_year():
        return db_manager.get_setting("next_school_year", "2026/2027")

    @staticmethod
    def set_current_year(value: str):
        db_manager.set_setting("current_school_year", value)

    @staticmethod
    def set_next_year(value: str):
        db_manager.set_setting("next_school_year", value)
