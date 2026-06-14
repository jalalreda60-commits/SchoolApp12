"""
==================================================================
 STUDENT MODEL
==================================================================
Represents a student record and provides all CRUD operations
against the SQLite database, plus helper queries used by the
dashboard (counts, charts data, etc.).
==================================================================
"""

from datetime import datetime
from database.db_manager import db_manager


class Student:
    """Data model + data access layer for the `students` table."""

    # Columns in the exact order they appear in the database
    COLUMNS = [
        "id", "matricule", "eleve_nom", "eleve_prenom", "mere", "pere",
        "date_of_birth", "city_of_birth", "adresse", "pere_telephone",
        "mere_telephone", "classe", "inscription", "transport_yn",
        "transport", "mensualite", "note_date", "annee_scolaire",
        "date_creation", "statut", "total_a_payer",
    ]

    def __init__(self, **kwargs):
        for col in self.COLUMNS:
            setattr(self, col, kwargs.get(col))

    # ------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------
    @staticmethod
    def create(data: dict) -> int:
        """Insert a new student. Returns the new row id."""
        conn = db_manager.get_connection()
        cur = conn.cursor()

        data.setdefault("date_creation", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        data.setdefault("statut", "Actif")
        data.setdefault("transport_yn", "No")
        data.setdefault("transport", 0)
        data.setdefault("inscription", 0)
        data.setdefault("mensualite", 0)

        fields = [c for c in Student.COLUMNS if c != "id" and c in data]
        placeholders = ", ".join(["?"] * len(fields))
        columns_sql = ", ".join(fields)
        values = [data.get(f) for f in fields]

        cur.execute(
            f"INSERT INTO students ({columns_sql}) VALUES ({placeholders})",
            values,
        )
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        return new_id

    # ------------------------------------------------------------
    # READ
    # ------------------------------------------------------------
    @staticmethod
    def get_by_id(student_id: int):
        conn = db_manager.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM students WHERE id = ?", (student_id,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_by_matricule_year(matricule: str, annee_scolaire: str):
        conn = db_manager.get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM students WHERE matricule = ? AND annee_scolaire = ?",
            (matricule, annee_scolaire),
        )
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_all(annee_scolaire: str = None, classe: str = None,
                search: str = None, statut: str = None,
                order_by: str = "eleve_nom", order_dir: str = "ASC",
                limit: int = None, offset: int = None):
        """Flexible query used by the students list page."""
        conn = db_manager.get_connection()
        cur = conn.cursor()

        query = "SELECT * FROM students WHERE 1=1"
        params = []

        if annee_scolaire:
            query += " AND annee_scolaire = ?"
            params.append(annee_scolaire)
        if classe and classe != "Toutes":
            query += " AND classe = ?"
            params.append(classe)
        if statut and statut != "Tous":
            query += " AND statut = ?"
            params.append(statut)
        if search:
            query += (" AND (matricule LIKE ? OR eleve_nom LIKE ? "
                      "OR eleve_prenom LIKE ? OR classe LIKE ?)")
            like = f"%{search}%"
            params.extend([like, like, like, like])

        # Sanitize order_by to prevent SQL injection
        if order_by not in Student.COLUMNS:
            order_by = "eleve_nom"
        order_dir = "DESC" if order_dir.upper() == "DESC" else "ASC"
        query += f" ORDER BY {order_by} {order_dir}"

        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
            if offset is not None:
                query += " OFFSET ?"
                params.append(offset)

        cur.execute(query, params)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def count_all(annee_scolaire: str = None, classe: str = None,
                   search: str = None, statut: str = None) -> int:
        conn = db_manager.get_connection()
        cur = conn.cursor()

        query = "SELECT COUNT(*) AS cnt FROM students WHERE 1=1"
        params = []

        if annee_scolaire:
            query += " AND annee_scolaire = ?"
            params.append(annee_scolaire)
        if classe and classe != "Toutes":
            query += " AND classe = ?"
            params.append(classe)
        if statut and statut != "Tous":
            query += " AND statut = ?"
            params.append(statut)
        if search:
            query += (" AND (matricule LIKE ? OR eleve_nom LIKE ? "
                      "OR eleve_prenom LIKE ? OR classe LIKE ?)")
            like = f"%{search}%"
            params.extend([like, like, like, like])

        cur.execute(query, params)
        cnt = cur.fetchone()["cnt"]
        conn.close()
        return cnt

    @staticmethod
    def get_distinct_classes(annee_scolaire: str = None):
        conn = db_manager.get_connection()
        cur = conn.cursor()
        if annee_scolaire:
            cur.execute(
                "SELECT DISTINCT classe FROM students "
                "WHERE classe IS NOT NULL AND classe != '' AND annee_scolaire = ? "
                "ORDER BY classe",
                (annee_scolaire,),
            )
        else:
            cur.execute(
                "SELECT DISTINCT classe FROM students "
                "WHERE classe IS NOT NULL AND classe != '' ORDER BY classe"
            )
        rows = [r["classe"] for r in cur.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def get_distinct_years():
        conn = db_manager.get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT DISTINCT annee_scolaire FROM students "
            "WHERE annee_scolaire IS NOT NULL AND annee_scolaire != '' "
            "ORDER BY annee_scolaire DESC"
        )
        rows = [r["annee_scolaire"] for r in cur.fetchall()]
        conn.close()
        return rows

    # ------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------
    @staticmethod
    def update(student_id: int, data: dict) -> bool:
        conn = db_manager.get_connection()
        cur = conn.cursor()

        fields = [c for c in Student.COLUMNS if c != "id" and c in data]
        if not fields:
            conn.close()
            return False

        set_clause = ", ".join([f"{f} = ?" for f in fields])
        values = [data.get(f) for f in fields]
        values.append(student_id)

        cur.execute(f"UPDATE students SET {set_clause} WHERE id = ?", values)
        conn.commit()
        success = cur.rowcount > 0
        conn.close()
        return success

    # ------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------
    @staticmethod
    def delete(student_id: int) -> bool:
        conn = db_manager.get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM students WHERE id = ?", (student_id,))
        conn.commit()
        success = cur.rowcount > 0
        conn.close()
        return success

    @staticmethod
    def delete_many(student_ids: list) -> int:
        if not student_ids:
            return 0
        conn = db_manager.get_connection()
        cur = conn.cursor()
        placeholders = ", ".join(["?"] * len(student_ids))
        cur.execute(f"DELETE FROM students WHERE id IN ({placeholders})", student_ids)
        conn.commit()
        count = cur.rowcount
        conn.close()
        return count

    # ------------------------------------------------------------
    # NEXT MATRICULE
    # ------------------------------------------------------------
    @staticmethod
    def generate_next_matricule() -> str:
        """Generate the next sequential matricule (numeric, zero padded)."""
        conn = db_manager.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT matricule FROM students")
        rows = cur.fetchall()
        conn.close()

        max_num = 0
        for r in rows:
            m = str(r["matricule"]).strip()
            if m.isdigit():
                max_num = max(max_num, int(m))
        return str(max_num + 1)

    # ------------------------------------------------------------
    # DASHBOARD STATISTICS
    # ------------------------------------------------------------
    @staticmethod
    def get_kpi_data(current_year: str, next_year: str, month: str = None):
        """Return KPI dictionary for the dashboard cards."""
        conn = db_manager.get_connection()
        cur = conn.cursor()

        # 1) Students enrolled current year (Actif)
        cur.execute(
            "SELECT COUNT(*) AS cnt FROM students "
            "WHERE annee_scolaire = ? AND statut = 'Actif'",
            (current_year,),
        )
        enrolled_current = cur.fetchone()["cnt"]

        # 2) Pre-registered for next year
        cur.execute(
            "SELECT COUNT(*) AS cnt FROM students WHERE annee_scolaire = ?",
            (next_year,),
        )
        pre_registered_next = cur.fetchone()["cnt"]

        # 3) New registrations this month (based on date_creation)
        if month:
            cur.execute(
                "SELECT COUNT(*) AS cnt FROM students "
                "WHERE annee_scolaire = ? AND strftime('%Y-%m', date_creation) = ?",
                (current_year, month),
            )
        else:
            current_month = datetime.now().strftime("%Y-%m")
            cur.execute(
                "SELECT COUNT(*) AS cnt FROM students "
                "WHERE annee_scolaire = ? AND strftime('%Y-%m', date_creation) = ?",
                (current_year, current_month),
            )
        new_this_month = cur.fetchone()["cnt"]

        # 4) Students using transport
        cur.execute(
            "SELECT COUNT(*) AS cnt FROM students "
            "WHERE annee_scolaire = ? AND transport_yn = 'Yes' AND statut = 'Actif'",
            (current_year,),
        )
        transport_users = cur.fetchone()["cnt"]

        conn.close()
        return {
            "enrolled_current": enrolled_current,
            "pre_registered_next": pre_registered_next,
            "new_this_month": new_this_month,
            "transport_users": transport_users,
        }

    @staticmethod
    def get_students_per_class(annee_scolaire: str):
        conn = db_manager.get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT classe, COUNT(*) AS cnt FROM students "
            "WHERE annee_scolaire = ? AND statut = 'Actif' AND classe IS NOT NULL AND classe != '' "
            "GROUP BY classe ORDER BY classe",
            (annee_scolaire,),
        )
        rows = [(r["classe"], r["cnt"]) for r in cur.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def get_monthly_registrations(annee_scolaire: str):
        conn = db_manager.get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT strftime('%Y-%m', date_creation) AS month, COUNT(*) AS cnt "
            "FROM students WHERE annee_scolaire = ? AND date_creation IS NOT NULL "
            "GROUP BY month ORDER BY month",
            (annee_scolaire,),
        )
        rows = [(r["month"], r["cnt"]) for r in cur.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def get_reinscription_progress(current_year: str, next_year: str):
        """Returns (re-inscribed_count, remaining_count) for donut chart."""
        conn = db_manager.get_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT COUNT(*) AS cnt FROM students "
            "WHERE annee_scolaire = ? AND statut = 'Actif'",
            (current_year,),
        )
        total_current = cur.fetchone()["cnt"]

        cur.execute(
            "SELECT COUNT(*) AS cnt FROM students WHERE annee_scolaire = ?",
            (next_year,),
        )
        reinscribed = cur.fetchone()["cnt"]

        conn.close()
        remaining = max(total_current - reinscribed, 0)
        return reinscribed, remaining

    @staticmethod
    def get_departures_by_month(annee_scolaire: str):
        """Students marked Inactif/Parti grouped by month (using date_creation as proxy update date)."""
        conn = db_manager.get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT strftime('%Y-%m', date_creation) AS month, COUNT(*) AS cnt "
            "FROM students WHERE annee_scolaire = ? AND statut = 'Inactif' "
            "GROUP BY month ORDER BY month",
            (annee_scolaire,),
        )
        rows = [(r["month"], r["cnt"]) for r in cur.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def get_transport_by_class(annee_scolaire: str):
        conn = db_manager.get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT classe, COUNT(*) AS cnt FROM students "
            "WHERE annee_scolaire = ? AND transport_yn = 'Yes' AND statut = 'Actif' "
            "AND classe IS NOT NULL AND classe != '' "
            "GROUP BY classe ORDER BY classe",
            (annee_scolaire,),
        )
        rows = [(r["classe"], r["cnt"]) for r in cur.fetchall()]
        conn.close()
        return rows
