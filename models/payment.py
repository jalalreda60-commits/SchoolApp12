"""
==================================================================
 PAYMENT MODEL
==================================================================
Data access layer for the payment module:
  - payment_status   : monthly status per student (Paye/Impaye/NAN)
  - payments         : actual payment transactions (history)
  - receipts         : generated PDF receipts

Also provides aggregation queries used by the payment dashboard
(KPIs, monthly income evolution, payment status distribution,
income by class).
==================================================================
"""

from datetime import datetime
from database.db_manager import db_manager
from utils.theme import MONTHS_ORDER, STATUS_PAID, STATUS_UNPAID, STATUS_NAN


class Payment:
    """Data model + data access layer for the payment module."""

    # ==============================================================
    # PAYMENT STATUS (monthly grid)
    # ==============================================================
    @staticmethod
    def get_status_map(student_id: int, annee_scolaire: str) -> dict:
        """Return {month: status} for all 10 months for a given student/year.
        Months without a stored row default to 'Impaye'."""
        conn = db_manager.get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT mois, statut FROM payment_status "
            "WHERE student_id = ? AND annee_scolaire = ?",
            (student_id, annee_scolaire),
        )
        rows = {r["mois"]: r["statut"] for r in cur.fetchall()}
        conn.close()

        result = {}
        for month in MONTHS_ORDER:
            result[month] = rows.get(month, STATUS_UNPAID)
        return result

    @staticmethod
    def set_status(student_id: int, annee_scolaire: str, mois: str, statut: str):
        """Insert or update the status for a single month."""
        conn = db_manager.get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO payment_status (student_id, annee_scolaire, mois, statut) "
            "VALUES (?, ?, ?, ?) "
            "ON CONFLICT(student_id, annee_scolaire, mois) "
            "DO UPDATE SET statut = excluded.statut",
            (student_id, annee_scolaire, mois, statut),
        )
        conn.commit()
        conn.close()

    @staticmethod
    def set_status_bulk(student_id: int, annee_scolaire: str, status_map: dict):
        """Insert or update statuses for multiple months at once."""
        conn = db_manager.get_connection()
        cur = conn.cursor()
        for mois, statut in status_map.items():
            cur.execute(
                "INSERT INTO payment_status (student_id, annee_scolaire, mois, statut) "
                "VALUES (?, ?, ?, ?) "
                "ON CONFLICT(student_id, annee_scolaire, mois) "
                "DO UPDATE SET statut = excluded.statut",
                (student_id, annee_scolaire, mois, statut),
            )
        conn.commit()
        conn.close()

    @staticmethod
    def get_next_unpaid_month(student_id: int, annee_scolaire: str):
        """
        Return the first month that is 'Impaye' (ignoring 'Paye' and 'NAN'),
        following MONTHS_ORDER. Returns None if all months are Paye/NAN.
        """
        status_map = Payment.get_status_map(student_id, annee_scolaire)
        for month in MONTHS_ORDER:
            if status_map.get(month) == STATUS_UNPAID:
                return month
        return None

    # ==============================================================
    # PAYMENTS (transaction history)
    # ==============================================================
    @staticmethod
    def create_payment(data: dict) -> int:
        """Insert a new payment record. Returns the new row id."""
        conn = db_manager.get_connection()
        cur = conn.cursor()

        data.setdefault("date_creation", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        cur.execute(
            "INSERT INTO payments "
            "(student_id, annee_scolaire, payment_type, mois, montant, "
            " date_paiement, notes, receipt_number, date_creation) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                data.get("student_id"),
                data.get("annee_scolaire"),
                data.get("payment_type"),
                data.get("mois"),
                data.get("montant", 0),
                data.get("date_paiement"),
                data.get("notes", ""),
                data.get("receipt_number"),
                data.get("date_creation"),
            ),
        )
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        return new_id

    @staticmethod
    def get_payments_for_student(student_id: int, annee_scolaire: str = None):
        conn = db_manager.get_connection()
        cur = conn.cursor()
        if annee_scolaire:
            cur.execute(
                "SELECT * FROM payments WHERE student_id = ? AND annee_scolaire = ? "
                "ORDER BY date_paiement DESC, id DESC",
                (student_id, annee_scolaire),
            )
        else:
            cur.execute(
                "SELECT * FROM payments WHERE student_id = ? "
                "ORDER BY date_paiement DESC, id DESC",
                (student_id,),
            )
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def get_total_paid(student_id: int, annee_scolaire: str) -> float:
        conn = db_manager.get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT COALESCE(SUM(montant), 0) AS total FROM payments "
            "WHERE student_id = ? AND annee_scolaire = ?",
            (student_id, annee_scolaire),
        )
        total = cur.fetchone()["total"]
        conn.close()
        return total

    @staticmethod
    def generate_receipt_number() -> str:
        """Generate a unique receipt number based on date + sequence."""
        conn = db_manager.get_connection()
        cur = conn.cursor()
        today = datetime.now().strftime("%Y%m%d")
        cur.execute(
            "SELECT COUNT(*) AS cnt FROM payments WHERE receipt_number LIKE ?",
            (f"REC-{today}-%",),
        )
        count = cur.fetchone()["cnt"]
        conn.close()
        return f"REC-{today}-{count + 1:04d}"

    # ==============================================================
    # RECEIPTS
    # ==============================================================
    @staticmethod
    def create_receipt(payment_id: int, receipt_number: str, file_path: str) -> int:
        conn = db_manager.get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO receipts (payment_id, receipt_number, file_path, date_creation) "
            "VALUES (?, ?, ?, ?)",
            (payment_id, receipt_number, file_path,
             datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        return new_id

    # ==============================================================
    # DASHBOARD AGGREGATIONS
    # ==============================================================
    @staticmethod
    def get_total_inscription_revenue(annee_scolaire: str, classe: str = None) -> float:
        """Sum of all 'Inscription' payments for the given year (and optional class)."""
        conn = db_manager.get_connection()
        cur = conn.cursor()

        query = (
            "SELECT COALESCE(SUM(p.montant), 0) AS total FROM payments p "
            "JOIN students s ON s.id = p.student_id "
            "WHERE p.annee_scolaire = ? AND p.payment_type = 'Inscription'"
        )
        params = [annee_scolaire]
        if classe and classe != "Toutes":
            query += " AND s.classe = ?"
            params.append(classe)

        cur.execute(query, params)
        total = cur.fetchone()["total"]
        conn.close()
        return total

    @staticmethod
    def get_monthly_income(annee_scolaire: str, month_key: str = None, classe: str = None) -> float:
        """
        Sum of all payments (Mensualité + Transport, excluding Inscription
        which is a one-time fee) made during a given calendar month.

        month_key: 'YYYY-MM' format (based on date_paiement). If None,
        uses the current calendar month.
        """
        conn = db_manager.get_connection()
        cur = conn.cursor()

        if not month_key:
            month_key = datetime.now().strftime("%Y-%m")

        query = (
            "SELECT COALESCE(SUM(p.montant), 0) AS total FROM payments p "
            "JOIN students s ON s.id = p.student_id "
            "WHERE p.annee_scolaire = ? AND p.payment_type != 'Inscription' "
            "AND strftime('%Y-%m', p.date_paiement) = ?"
        )
        params = [annee_scolaire, month_key]
        if classe and classe != "Toutes":
            query += " AND s.classe = ?"
            params.append(classe)

        cur.execute(query, params)
        total = cur.fetchone()["total"]
        conn.close()
        return total

    @staticmethod
    def get_distinct_payment_months(annee_scolaire: str):
        """Return sorted list of distinct 'YYYY-MM' values from date_paiement."""
        conn = db_manager.get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT DISTINCT strftime('%Y-%m', date_paiement) AS m FROM payments "
            "WHERE annee_scolaire = ? AND date_paiement IS NOT NULL ORDER BY m",
            (annee_scolaire,),
        )
        rows = [r["m"] for r in cur.fetchall() if r["m"]]
        conn.close()
        return rows

    @staticmethod
    def get_monthly_income_evolution(annee_scolaire: str, classe: str = None):
        """
        Returns list of tuples:
          (month_key, inscription_total, mensualite_total, transport_total)
        for each distinct calendar month with payments, ordered chronologically.
        """
        conn = db_manager.get_connection()
        cur = conn.cursor()

        query = (
            "SELECT strftime('%Y-%m', p.date_paiement) AS month_key, "
            "p.payment_type, COALESCE(SUM(p.montant), 0) AS total "
            "FROM payments p JOIN students s ON s.id = p.student_id "
            "WHERE p.annee_scolaire = ? AND p.date_paiement IS NOT NULL"
        )
        params = [annee_scolaire]
        if classe and classe != "Toutes":
            query += " AND s.classe = ?"
            params.append(classe)

        query += " GROUP BY month_key, p.payment_type ORDER BY month_key"

        cur.execute(query, params)
        rows = cur.fetchall()
        conn.close()

        data = {}
        for r in rows:
            mk = r["month_key"]
            if mk not in data:
                data[mk] = {"Inscription": 0, "Mensualité": 0, "Transport": 0}
            data[mk][r["payment_type"]] = r["total"]

        result = []
        for mk in sorted(data.keys()):
            result.append((
                mk,
                data[mk].get("Inscription", 0),
                data[mk].get("Mensualité", 0),
                data[mk].get("Transport", 0),
            ))
        return result

    @staticmethod
    def get_payment_status_distribution(annee_scolaire: str, mois: str = None, classe: str = None):
        """
        Returns dict {Paye: n, Impaye: n, NAN: n} counting students per status
        for a given month (or aggregated across all months if mois is None).
        """
        conn = db_manager.get_connection()
        cur = conn.cursor()

        query = (
            "SELECT ps.statut, COUNT(*) AS cnt FROM payment_status ps "
            "JOIN students s ON s.id = ps.student_id "
            "WHERE ps.annee_scolaire = ?"
        )
        params = [annee_scolaire]

        if mois and mois != "Tous":
            query += " AND ps.mois = ?"
            params.append(mois)

        if classe and classe != "Toutes":
            query += " AND s.classe = ?"
            params.append(classe)

        query += " GROUP BY ps.statut"

        cur.execute(query, params)
        rows = {r["statut"]: r["cnt"] for r in cur.fetchall()}
        conn.close()

        return {
            STATUS_PAID: rows.get(STATUS_PAID, 0),
            STATUS_UNPAID: rows.get(STATUS_UNPAID, 0),
            STATUS_NAN: rows.get(STATUS_NAN, 0),
        }

    @staticmethod
    def get_income_by_class(annee_scolaire: str):
        """Returns list of (classe, total_income) for all payment types."""
        conn = db_manager.get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT s.classe AS classe, COALESCE(SUM(p.montant), 0) AS total "
            "FROM payments p JOIN students s ON s.id = p.student_id "
            "WHERE p.annee_scolaire = ? AND s.classe IS NOT NULL AND s.classe != '' "
            "GROUP BY s.classe ORDER BY s.classe",
            (annee_scolaire,),
        )
        rows = [(r["classe"], r["total"]) for r in cur.fetchall()]
        conn.close()
        return rows
