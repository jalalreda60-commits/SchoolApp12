"""
==================================================================
 DATABASE MANAGER
==================================================================
Handles SQLite connection, schema creation and low level
database operations for the Private School Management System.
==================================================================
"""

import sqlite3
import os
import sys
import shutil
from datetime import datetime

# ------------------------------------------------------------
# Determine the base directory for persistent application data.
#
# - In a normal Python run, this is the project root (one level
#   above /database).
# - In a PyInstaller --onefile build, sys.frozen is True and
#   sys.executable points to the .exe; we store data in a
#   "data" folder next to the executable so it persists across
#   runs (the PyInstaller temp extraction folder is wiped).
# ------------------------------------------------------------
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "data")
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_PATH = os.path.join(BASE_DIR, "database", "school.db")
BACKUP_DIR = os.path.join(BASE_DIR, "backups")


class DatabaseManager:
    """
    Central database manager. Provides a single point of access
    to the SQLite database and creates the schema if it does not
    exist yet.
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        os.makedirs(BACKUP_DIR, exist_ok=True)
        self._create_schema()

    # ------------------------------------------------------------
    # Connection helper
    # ------------------------------------------------------------
    def get_connection(self) -> sqlite3.Connection:
        """Return a new connection with row factory set to dict-like rows."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    # ------------------------------------------------------------
    # Schema creation
    # ------------------------------------------------------------
    def _create_schema(self):
        """Create all required tables if they do not already exist."""
        conn = self.get_connection()
        cur = conn.cursor()

        # Main students table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                matricule TEXT NOT NULL,
                eleve_nom TEXT NOT NULL,
                eleve_prenom TEXT NOT NULL,
                mere TEXT,
                pere TEXT,
                date_of_birth TEXT,
                city_of_birth TEXT,
                adresse TEXT,
                pere_telephone TEXT,
                mere_telephone TEXT,
                classe TEXT,
                inscription REAL DEFAULT 0,
                transport_yn TEXT DEFAULT 'No',
                transport REAL DEFAULT 0,
                mensualite REAL DEFAULT 0,
                note_date TEXT,
                annee_scolaire TEXT,
                date_creation TEXT,
                statut TEXT DEFAULT 'Actif',
                total_a_payer REAL DEFAULT 0,
                UNIQUE(matricule, annee_scolaire)
            )
        """)

        # Migration: add total_a_payer if missing (for databases created
        # before this column existed)
        cur.execute("PRAGMA table_info(students)")
        existing_cols = [row["name"] for row in cur.fetchall()]
        if "total_a_payer" not in existing_cols:
            cur.execute("ALTER TABLE students ADD COLUMN total_a_payer REAL DEFAULT 0")

        # Settings table (key/value store for app preferences)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # ------------------------------------------------------------
        # PAYMENT MODULE TABLES
        # ------------------------------------------------------------

        # Monthly status table: one row per (student, annee_scolaire, month)
        # status is one of: 'Paye', 'Impaye', 'NAN'
        cur.execute("""
            CREATE TABLE IF NOT EXISTS payment_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                annee_scolaire TEXT NOT NULL,
                mois TEXT NOT NULL,
                statut TEXT NOT NULL DEFAULT 'Impaye',
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                UNIQUE(student_id, annee_scolaire, mois)
            )
        """)

        # Payment history table: every actual payment transaction
        cur.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                annee_scolaire TEXT NOT NULL,
                payment_type TEXT NOT NULL,
                mois TEXT,
                montant REAL NOT NULL DEFAULT 0,
                date_paiement TEXT NOT NULL,
                notes TEXT,
                receipt_number TEXT UNIQUE,
                date_creation TEXT,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
            )
        """)

        # Receipts table: generated PDF receipts linked to payments
        cur.execute("""
            CREATE TABLE IF NOT EXISTS receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_id INTEGER NOT NULL,
                receipt_number TEXT NOT NULL UNIQUE,
                file_path TEXT,
                date_creation TEXT,
                FOREIGN KEY (payment_id) REFERENCES payments(id) ON DELETE CASCADE
            )
        """)

        cur.execute("CREATE INDEX IF NOT EXISTS idx_payment_status_student "
                     "ON payment_status(student_id, annee_scolaire)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_payments_student "
                     "ON payments(student_id, annee_scolaire)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_payments_receipt "
                     "ON payments(receipt_number)")

        # Indexes for fast search & filter
        cur.execute("CREATE INDEX IF NOT EXISTS idx_students_classe ON students(classe)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_students_annee ON students(annee_scolaire)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_students_matricule ON students(matricule)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_students_statut ON students(statut)")

        # Default settings
        defaults = {
            "appearance_mode": "Light",
            "current_school_year": "2025/2026",
            "next_school_year": "2026/2027",
            "school_name": "Le Schéma",
            "last_backup": "",
        }
        for k, v in defaults.items():
            cur.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (k, v),
            )

        conn.commit()
        conn.close()

    # ------------------------------------------------------------
    # Settings helpers
    # ------------------------------------------------------------
    def get_setting(self, key: str, default=None):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cur.fetchone()
        conn.close()
        return row["value"] if row else default

    def set_setting(self, key: str, value: str):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, str(value)),
        )
        conn.commit()
        conn.close()

    # ------------------------------------------------------------
    # Backup
    # ------------------------------------------------------------
    def backup_database(self) -> str:
        """Create a timestamped copy of the database file in /backups."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"school_backup_{timestamp}.db"
        backup_path = os.path.join(BACKUP_DIR, backup_name)
        shutil.copy2(self.db_path, backup_path)
        self.set_setting("last_backup", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        return backup_path


# Singleton instance used across the whole application
db_manager = DatabaseManager()
