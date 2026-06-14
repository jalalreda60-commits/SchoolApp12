"""
==================================================================
 PAYMENT CONTROLLER
==================================================================
Business logic layer for the payment module:
  - Validates and saves new payments
  - Updates monthly status grid (marks month as Paye)
  - Generates unique receipt numbers
  - Triggers PDF receipt generation
==================================================================
"""

from datetime import datetime
from models.payment import Payment
from models.student import Student
from utils.theme import STATUS_PAID, STATUS_UNPAID, PAYMENT_TYPES


class PaymentController:

    # ------------------------------------------------------------
    # VALIDATION
    # ------------------------------------------------------------
    @staticmethod
    def validate_payment_data(data: dict) -> list:
        errors = []

        if not data.get("student_id"):
            errors.append("Veuillez sélectionner un élève.")

        if not data.get("payment_type") or data.get("payment_type") not in PAYMENT_TYPES:
            errors.append("Veuillez sélectionner un type de paiement valide.")

        try:
            montant = float(data.get("montant", 0))
            if montant <= 0:
                errors.append("Le montant doit être supérieur à 0.")
        except (ValueError, TypeError):
            errors.append("Le montant doit être un nombre valide.")

        if not data.get("date_paiement"):
            errors.append("La date de paiement est obligatoire.")
        else:
            try:
                datetime.strptime(data["date_paiement"], "%Y-%m-%d")
            except ValueError:
                errors.append("La date de paiement doit être au format AAAA-MM-JJ.")

        # Month required for Mensualité / Transport payments
        if data.get("payment_type") in ("Mensualité", "Transport") and not data.get("mois"):
            errors.append("Veuillez sélectionner le mois concerné par ce paiement.")

        return errors

    # ------------------------------------------------------------
    # SAVE PAYMENT (main entry point)
    # ------------------------------------------------------------
    @staticmethod
    def save_payment(data: dict):
        """
        Save a new payment, update the monthly status grid (if applicable),
        and return (payment_id, receipt_number, errors).
        """
        errors = PaymentController.validate_payment_data(data)
        if errors:
            return None, None, errors

        receipt_number = Payment.generate_receipt_number()
        data["receipt_number"] = receipt_number

        payment_id = Payment.create_payment(data)

        # If this payment concerns a specific month (Mensualité/Transport),
        # mark that month as "Paye" in the status grid.
        if data.get("mois"):
            Payment.set_status(
                data["student_id"], data["annee_scolaire"],
                data["mois"], STATUS_PAID
            )

        return payment_id, receipt_number, []

    # ------------------------------------------------------------
    # NEXT UNPAID MONTH
    # ------------------------------------------------------------
    @staticmethod
    def get_next_unpaid_month(student_id: int, annee_scolaire: str):
        return Payment.get_next_unpaid_month(student_id, annee_scolaire)

    # ------------------------------------------------------------
    # STUDENT PAYMENT SUMMARY
    # ------------------------------------------------------------
    @staticmethod
    def get_student_summary(student_id: int, annee_scolaire: str) -> dict:
        """Aggregate all payment info needed by the payment page for a student."""
        student = Student.get_by_id(student_id)
        if not student:
            return None

        status_map = Payment.get_status_map(student_id, annee_scolaire)
        total_paid = Payment.get_total_paid(student_id, annee_scolaire)
        next_month = Payment.get_next_unpaid_month(student_id, annee_scolaire)
        history = Payment.get_payments_for_student(student_id, annee_scolaire)

        total_a_payer = student.get("total_a_payer") or (
            (student.get("inscription") or 0) + (student.get("transport") or 0)
        )

        return {
            "student": student,
            "status_map": status_map,
            "total_paid": total_paid,
            "total_a_payer": total_a_payer,
            "remaining": max(total_a_payer - total_paid, 0),
            "next_unpaid_month": next_month,
            "history": history,
        }
