"""
==================================================================
 STUDENT SEARCH DIALOG
==================================================================
Modal dialog allowing the user to search for a student by
matricule, nom, prénom or classe, and select one to proceed
to the payment form.
==================================================================
"""

import customtkinter as ctk
from tkinter import ttk
from models.student import Student
from controllers.student_controller import StudentController
from utils.theme import COLORS, FONTS, BUTTON_CORNER_RADIUS


class StudentSearchDialog(ctk.CTkToplevel):
    """Modal dialog for searching and selecting a student."""

    def __init__(self, master, on_select, annee_scolaire: str = None):
        super().__init__(master)
        self.on_select = on_select
        self.annee_scolaire = annee_scolaire or StudentController.get_current_year()

        self.title("Rechercher un Élève")
        self.geometry("720x520")
        self.minsize(640, 460)
        self.grab_set()
        self.transient(master)

        self._build_ui()
        self._reload_table()

    # ------------------------------------------------------------
    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color=COLORS["primary"], corner_radius=0, height=70)
        header.pack(fill="x")
        ctk.CTkLabel(
            header, text="🔍 Rechercher un Élève", font=FONTS["h2"], text_color="white"
        ).pack(side="left", padx=20, pady=15)

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=15)

        # Search bar
        search_frame = ctk.CTkFrame(content, fg_color="transparent")
        search_frame.pack(fill="x", pady=(0, 10))

        self.search_entry = ctk.CTkEntry(
            search_frame, placeholder_text="Matricule, Nom, Prénom ou Classe...",
            width=400
        )
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.bind("<KeyRelease>", self._on_search)
        self.search_entry.focus()

        # Table
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Search.Treeview", rowheight=32, font=("Segoe UI", 11))
        style.configure("Search.Treeview.Heading",
                        background=COLORS["primary"], foreground="white",
                        font=("Segoe UI", 11, "bold"), relief="flat")
        style.map("Search.Treeview",
                  background=[("selected", COLORS["secondary"])],
                  foreground=[("selected", "white")])

        table_frame = ctk.CTkFrame(content, corner_radius=12,
                                    fg_color=("white", COLORS["card_dark"]))
        table_frame.pack(fill="both", expand=True)

        columns = ("matricule", "nom", "prenom", "classe", "annee")
        self.tree = ttk.Treeview(
            table_frame, columns=columns, show="headings",
            style="Search.Treeview", selectmode="browse"
        )
        headers = {
            "matricule": ("Matricule", 100),
            "nom": ("Nom", 150),
            "prenom": ("Prénom", 150),
            "classe": ("Classe", 100),
            "annee": ("Année", 100),
        }
        for col, (label, width) in headers.items():
            self.tree.heading(col, text=label)
            self.tree.column(col, width=width, anchor="center")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        vsb.pack(side="right", fill="y", pady=10, padx=(0, 10))

        self.tree.bind("<Double-1>", self._on_double_click)

        # Footer buttons
        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(10, 0))

        ctk.CTkButton(
            btn_frame, text="✅ Sélectionner", fg_color=COLORS["success"],
            hover_color=COLORS["success_hover"], corner_radius=BUTTON_CORNER_RADIUS,
            command=self._confirm_selection
        ).pack(side="left", fill="x", expand=True, padx=(0, 5))

        ctk.CTkButton(
            btn_frame, text="Annuler", fg_color=COLORS["muted_light"],
            hover_color=COLORS["muted_dark"], corner_radius=BUTTON_CORNER_RADIUS,
            command=self.destroy
        ).pack(side="left", fill="x", expand=True, padx=(5, 0))

    # ------------------------------------------------------------
    def _on_search(self, _event=None):
        self._reload_table()

    def _reload_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        search_term = self.search_entry.get().strip()

        students = Student.get_all(
            annee_scolaire=self.annee_scolaire,
            search=search_term,
            order_by="eleve_nom",
            limit=100,
        )

        for s in students:
            self.tree.insert("", "end", iid=str(s["id"]), values=(
                s.get("matricule", ""), s.get("eleve_nom", ""),
                s.get("eleve_prenom", ""), s.get("classe", ""),
                s.get("annee_scolaire", ""),
            ))

    # ------------------------------------------------------------
    def _on_double_click(self, _event=None):
        self._confirm_selection()

    def _confirm_selection(self):
        selection = self.tree.selection()
        if not selection:
            return
        student_id = int(selection[0])
        self.on_select(student_id)
        self.destroy()
