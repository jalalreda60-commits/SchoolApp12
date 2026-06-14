"""
==================================================================
 GESTION ÉLÈVES VIEW
==================================================================
Professional table view of all students with search, multi
filter (year/class/status), sorting, pagination and row actions
(view, edit, delete, print). Includes Import / Export / Refresh
toolbar.
==================================================================
"""

import customtkinter as ctk
from tkinter import filedialog, ttk
import tkinter as tk
from datetime import datetime

from models.student import Student
from controllers.student_controller import StudentController
from controllers.excel_controller import ExcelController
from utils.theme import COLORS, FONTS, BUTTON_CORNER_RADIUS, STATUT_OPTIONS
from utils.helpers import show_toast, confirm_dialog, format_currency
from views.components.student_profile_dialog import StudentProfileDialog
from views.components.import_dialog import ImportExcelDialog


PAGE_SIZE = 25

TABLE_COLUMNS = [
    ("matricule", "Matricule", 90),
    ("eleve_nom", "Nom", 130),
    ("eleve_prenom", "Prénom", 130),
    ("classe", "Classe", 80),
    ("pere_telephone", "Tél. Père", 110),
    ("mere_telephone", "Tél. Mère", 110),
    ("transport_yn", "Transport", 80),
    ("mensualite", "Mensualité", 100),
    ("statut", "Statut", 80),
]


class GestionElevesView(ctk.CTkFrame):
    """Students management page."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.current_year = StudentController.get_current_year()
        self.search_term = ""
        self.filter_classe = "Toutes"
        self.filter_statut = "Tous"
        self.sort_column = "eleve_nom"
        self.sort_dir = "ASC"
        self.current_page = 1

        self._build_ui()
        self.refresh()

    # ------------------------------------------------------------
    def _build_ui(self):
        # ---- Header ----
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(20, 10))

        ctk.CTkLabel(
            header, text="🎓 Gestion des Élèves", font=FONTS["h1"], anchor="w"
        ).pack(side="left")

        # Toolbar buttons
        toolbar = ctk.CTkFrame(header, fg_color="transparent")
        toolbar.pack(side="right")

        ctk.CTkButton(
            toolbar, text="🔄 Actualiser", fg_color=COLORS["muted_light"],
            hover_color=COLORS["muted_dark"], width=110,
            corner_radius=BUTTON_CORNER_RADIUS, command=self.refresh
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            toolbar, text="📤 Exporter Excel", fg_color=COLORS["secondary"],
            hover_color=COLORS["primary_hover"], width=140,
            corner_radius=BUTTON_CORNER_RADIUS, command=self._export_excel
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            toolbar, text="📥 Importer Excel", fg_color=COLORS["success"],
            hover_color=COLORS["success_hover"], width=140,
            corner_radius=BUTTON_CORNER_RADIUS, command=self._open_import
        ).pack(side="left", padx=4)

        # ---- Filters row ----
        filters = ctk.CTkFrame(self, fg_color="transparent")
        filters.pack(fill="x", padx=25, pady=(0, 10))

        self.search_entry = ctk.CTkEntry(
            filters, placeholder_text="🔍 Rechercher (matricule, nom, prénom, classe)...",
            width=320
        )
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", self._on_search)

        ctk.CTkLabel(filters, text="Année:", font=FONTS["body"]).pack(side="left", padx=(10, 5))
        years = Student.get_distinct_years()
        if self.current_year not in years:
            years.append(self.current_year)
        years = sorted(set(years), reverse=True)
        self.year_var = ctk.StringVar(value=self.current_year)
        ctk.CTkOptionMenu(
            filters, values=years, variable=self.year_var, width=110,
            fg_color=COLORS["primary"], button_color=COLORS["primary_hover"],
            command=self._on_filter_change
        ).pack(side="left", padx=(0, 10))

        ctk.CTkLabel(filters, text="Classe:", font=FONTS["body"]).pack(side="left", padx=(10, 5))
        self.classe_var = ctk.StringVar(value="Toutes")
        self.classe_menu = ctk.CTkOptionMenu(
            filters, values=["Toutes"], variable=self.classe_var, width=110,
            fg_color=COLORS["primary"], button_color=COLORS["primary_hover"],
            command=self._on_filter_change
        )
        self.classe_menu.pack(side="left", padx=(0, 10))

        ctk.CTkLabel(filters, text="Statut:", font=FONTS["body"]).pack(side="left", padx=(10, 5))
        self.statut_var = ctk.StringVar(value="Tous")
        ctk.CTkOptionMenu(
            filters, values=["Tous"] + STATUT_OPTIONS, variable=self.statut_var, width=110,
            fg_color=COLORS["primary"], button_color=COLORS["primary_hover"],
            command=self._on_filter_change
        ).pack(side="left")

        self.count_label = ctk.CTkLabel(filters, text="", font=FONTS["small"],
                                         text_color=COLORS["muted_light"])
        self.count_label.pack(side="right", padx=10)

        # ---- Table (using ttk.Treeview for sortable columns) ----
        table_frame = ctk.CTkFrame(self, corner_radius=14,
                                    fg_color=("white", COLORS["card_dark"]))
        table_frame.pack(fill="both", expand=True, padx=25, pady=(0, 10))

        # Style for the Treeview to match the modern theme
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Modern.Treeview",
                        background="white",
                        foreground=COLORS["text_light"],
                        fieldbackground="white",
                        rowheight=34,
                        font=("Segoe UI", 11))
        style.configure("Modern.Treeview.Heading",
                        background=COLORS["primary"],
                        foreground="white",
                        font=("Segoe UI", 11, "bold"),
                        relief="flat")
        style.map("Modern.Treeview.Heading",
                  background=[("active", COLORS["primary_hover"])])
        style.map("Modern.Treeview",
                  background=[("selected", COLORS["secondary"])],
                  foreground=[("selected", "white")])

        columns = [c[0] for c in TABLE_COLUMNS]
        self.tree = ttk.Treeview(
            table_frame, columns=columns, show="headings",
            style="Modern.Treeview", selectmode="browse"
        )
        for col_id, col_label, col_width in TABLE_COLUMNS:
            self.tree.heading(col_id, text=col_label,
                               command=lambda c=col_id: self._sort_by(c))
            self.tree.column(col_id, width=col_width, anchor="center")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        vsb.pack(side="right", fill="y", pady=10, padx=(0, 10))

        self.tree.bind("<Double-1>", self._on_row_double_click)

        # ---- Pagination + actions ----
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", padx=25, pady=(0, 15))

        action_frame = ctk.CTkFrame(bottom, fg_color="transparent")
        action_frame.pack(side="left")

        ctk.CTkButton(
            action_frame, text="👁️ Voir", width=90, fg_color=COLORS["secondary"],
            hover_color=COLORS["primary_hover"], corner_radius=BUTTON_CORNER_RADIUS,
            command=self._view_selected
        ).pack(side="left", padx=3)

        ctk.CTkButton(
            action_frame, text="✏️ Modifier", width=90, fg_color=COLORS["warning"],
            hover_color=COLORS["warning_hover"], corner_radius=BUTTON_CORNER_RADIUS,
            command=self._view_selected
        ).pack(side="left", padx=3)

        ctk.CTkButton(
            action_frame, text="🗑️ Supprimer", width=100, fg_color=COLORS["danger"],
            hover_color=COLORS["danger_hover"], corner_radius=BUTTON_CORNER_RADIUS,
            command=self._delete_selected
        ).pack(side="left", padx=3)

        ctk.CTkButton(
            action_frame, text="🖨️ Carte", width=90, fg_color=COLORS["muted_light"],
            hover_color=COLORS["muted_dark"], corner_radius=BUTTON_CORNER_RADIUS,
            command=self._print_selected
        ).pack(side="left", padx=3)

        # Pagination
        pagination = ctk.CTkFrame(bottom, fg_color="transparent")
        pagination.pack(side="right")

        self.prev_btn = ctk.CTkButton(
            pagination, text="◀ Précédent", width=110, fg_color=COLORS["muted_light"],
            hover_color=COLORS["muted_dark"], corner_radius=BUTTON_CORNER_RADIUS,
            command=self._prev_page
        )
        self.prev_btn.pack(side="left", padx=5)

        self.page_label = ctk.CTkLabel(pagination, text="Page 1 / 1", font=FONTS["body"])
        self.page_label.pack(side="left", padx=10)

        self.next_btn = ctk.CTkButton(
            pagination, text="Suivant ▶", width=110, fg_color=COLORS["muted_light"],
            hover_color=COLORS["muted_dark"], corner_radius=BUTTON_CORNER_RADIUS,
            command=self._next_page
        )
        self.next_btn.pack(side="left", padx=5)

    # ------------------------------------------------------------
    def _on_search(self, _event=None):
        self.search_term = self.search_entry.get().strip()
        self.current_page = 1
        self._reload_table()

    def _on_filter_change(self, _value=None):
        self.current_year = self.year_var.get()
        self.filter_classe = self.classe_var.get()
        self.filter_statut = self.statut_var.get()
        self.current_page = 1
        self._reload_table()

    def _sort_by(self, column):
        if self.sort_column == column:
            self.sort_dir = "DESC" if self.sort_dir == "ASC" else "ASC"
        else:
            self.sort_column = column
            self.sort_dir = "ASC"
        self._reload_table()

    # ------------------------------------------------------------
    def refresh(self):
        """Full refresh: reload year/class options and table data."""
        self.current_year = StudentController.get_current_year()

        years = Student.get_distinct_years()
        if self.current_year not in years:
            years.append(self.current_year)
        years = sorted(set(years), reverse=True)

        classes = Student.get_distinct_classes(self.year_var.get() if hasattr(self, "year_var") else self.current_year)
        self.classe_menu.configure(values=["Toutes"] + classes)

        self._reload_table()

    def _reload_table(self):
        # Clear existing rows
        for item in self.tree.get_children():
            self.tree.delete(item)

        total = Student.count_all(
            annee_scolaire=self.current_year,
            classe=self.filter_classe,
            search=self.search_term,
            statut=self.filter_statut,
        )

        total_pages = max((total + PAGE_SIZE - 1) // PAGE_SIZE, 1)
        if self.current_page > total_pages:
            self.current_page = total_pages
        offset = (self.current_page - 1) * PAGE_SIZE

        students = Student.get_all(
            annee_scolaire=self.current_year,
            classe=self.filter_classe,
            search=self.search_term,
            statut=self.filter_statut,
            order_by=self.sort_column,
            order_dir=self.sort_dir,
            limit=PAGE_SIZE,
            offset=offset,
        )

        for s in students:
            values = []
            for col_id, _, _ in TABLE_COLUMNS:
                val = s.get(col_id, "")
                if col_id == "mensualite":
                    val = format_currency(val)
                if val is None:
                    val = ""
                values.append(val)
            self.tree.insert("", "end", iid=str(s["id"]), values=values)

        self.count_label.configure(text=f"{total} élève(s) trouvé(s)")
        self.page_label.configure(text=f"Page {self.current_page} / {total_pages}")

        self.prev_btn.configure(state="normal" if self.current_page > 1 else "disabled")
        self.next_btn.configure(state="normal" if self.current_page < total_pages else "disabled")

    # ------------------------------------------------------------
    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._reload_table()

    def _next_page(self):
        self.current_page += 1
        self._reload_table()

    # ------------------------------------------------------------
    def _get_selected_id(self):
        selection = self.tree.selection()
        if not selection:
            show_toast(self, "⚠️ Veuillez sélectionner un élève.", kind="warning")
            return None
        return int(selection[0])

    def _on_row_double_click(self, _event=None):
        self._view_selected()

    def _view_selected(self):
        student_id = self._get_selected_id()
        if student_id is None:
            return
        StudentProfileDialog(self, student_id, on_change=self._reload_table)

    def _delete_selected(self):
        student_id = self._get_selected_id()
        if student_id is None:
            return

        student = Student.get_by_id(student_id)
        if confirm_dialog(
            self, "Confirmer la suppression",
            f"Voulez-vous vraiment supprimer l'élève "
            f"{student.get('eleve_prenom')} {student.get('eleve_nom')} ?"
        ):
            StudentController.delete_student(student_id)
            show_toast(self, "🗑️ Élève supprimé avec succès.", kind="success")
            self._reload_table()

    def _print_selected(self):
        student_id = self._get_selected_id()
        if student_id is None:
            return
        dialog = StudentProfileDialog(self, student_id, on_change=self._reload_table)
        dialog._print_card()
        dialog.after(200, dialog.destroy)

    # ------------------------------------------------------------
    def _open_import(self):
        ImportExcelDialog(self, self.current_year, on_complete=self.refresh)

    def _export_excel(self):
        students = Student.get_all(
            annee_scolaire=self.current_year,
            classe=self.filter_classe,
            search=self.search_term,
            statut=self.filter_statut,
            order_by=self.sort_column,
            order_dir=self.sort_dir,
        )

        if not students:
            show_toast(self, "⚠️ Aucun élève à exporter.", kind="warning")
            return

        path = filedialog.asksaveasfilename(
            title="Exporter vers Excel",
            defaultextension=".xlsx",
            initialfile=f"eleves_{self.current_year.replace('/', '-')}.xlsx",
            filetypes=[("Fichier Excel", "*.xlsx")]
        )
        if not path:
            return

        ExcelController.export_excel(path, students)
        show_toast(self, f"✅ {len(students)} élève(s) exporté(s) avec succès.", kind="success")
