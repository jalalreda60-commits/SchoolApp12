"""
==================================================================
 RE-INSCRIPTION VIEW
==================================================================
Allows selecting students from the current year and generating
their registration records for the next academic year while
preserving all information.
==================================================================
"""

import customtkinter as ctk
from tkinter import ttk
from models.student import Student
from controllers.student_controller import StudentController
from utils.theme import COLORS, FONTS, BUTTON_CORNER_RADIUS
from utils.helpers import show_toast, confirm_dialog


TABLE_COLUMNS = [
    ("matricule", "Matricule", 90),
    ("eleve_nom", "Nom", 140),
    ("eleve_prenom", "Prénom", 140),
    ("classe", "Classe", 90),
    ("mensualite", "Mensualité", 100),
    ("statut_reinscription", "Statut Réinscription", 160),
]


class ReinscriptionView(ctk.CTkFrame):
    """Re-inscription preparation page."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.current_year = StudentController.get_current_year()
        self.next_year = StudentController.get_next_year()
        self.search_term = ""
        self.checked_ids = set()

        self._build_ui()
        self.refresh()

    # ------------------------------------------------------------
    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(20, 10))

        ctk.CTkLabel(
            header, text="🔁 Réinscription", font=FONTS["h1"], anchor="w"
        ).pack(side="left")

        self.year_info_label = ctk.CTkLabel(
            header, text="", font=FONTS["body_bold"], text_color=COLORS["primary"]
        )
        self.year_info_label.pack(side="right")

        # ---- Stats cards ----
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.pack(fill="x", padx=25, pady=(0, 10))
        for i in range(3):
            stats_frame.grid_columnconfigure(i, weight=1, uniform="stat")

        self.stat_total = self._make_stat_card(stats_frame, "👥 Total éligibles", "0", COLORS["primary"])
        self.stat_total.grid(row=0, column=0, padx=8, sticky="ew")

        self.stat_selected = self._make_stat_card(stats_frame, "✅ Sélectionnés", "0", COLORS["secondary"])
        self.stat_selected.grid(row=0, column=1, padx=8, sticky="ew")

        self.stat_reinscribed = self._make_stat_card(stats_frame, "🔁 Déjà réinscrits", "0", COLORS["success"])
        self.stat_reinscribed.grid(row=0, column=2, padx=8, sticky="ew")

        # ---- Search + actions ----
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", padx=25, pady=(0, 10))

        self.search_entry = ctk.CTkEntry(
            actions, placeholder_text="🔍 Rechercher un élève...", width=300
        )
        self.search_entry.pack(side="left")
        self.search_entry.bind("<KeyRelease>", self._on_search)

        ctk.CTkButton(
            actions, text="☑️ Tout sélectionner", width=160,
            fg_color=COLORS["secondary"], hover_color=COLORS["primary_hover"],
            corner_radius=BUTTON_CORNER_RADIUS, command=self._select_all
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            actions, text="⬜ Tout désélectionner", width=170,
            fg_color=COLORS["muted_light"], hover_color=COLORS["muted_dark"],
            corner_radius=BUTTON_CORNER_RADIUS, command=self._deselect_all
        ).pack(side="left")

        ctk.CTkButton(
            actions, text="🚀 Générer la Réinscription", width=240,
            fg_color=COLORS["success"], hover_color=COLORS["success_hover"],
            corner_radius=BUTTON_CORNER_RADIUS, font=FONTS["body_bold"],
            command=self._generate_reinscription
        ).pack(side="right")

        # ---- Table ----
        table_frame = ctk.CTkFrame(self, corner_radius=14,
                                    fg_color=("white", COLORS["card_dark"]))
        table_frame.pack(fill="both", expand=True, padx=25, pady=(0, 20))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Reins.Treeview",
                        background="white", foreground=COLORS["text_light"],
                        fieldbackground="white", rowheight=34,
                        font=("Segoe UI", 11))
        style.configure("Reins.Treeview.Heading",
                        background=COLORS["primary"], foreground="white",
                        font=("Segoe UI", 11, "bold"), relief="flat")
        style.map("Reins.Treeview",
                  background=[("selected", COLORS["secondary"])],
                  foreground=[("selected", "white")])

        columns = ["check"] + [c[0] for c in TABLE_COLUMNS]
        self.tree = ttk.Treeview(
            table_frame, columns=columns, show="headings",
            style="Reins.Treeview", selectmode="none"
        )
        self.tree.heading("check", text="☐")
        self.tree.column("check", width=50, anchor="center")
        for col_id, col_label, col_width in TABLE_COLUMNS:
            self.tree.heading(col_id, text=col_label)
            self.tree.column(col_id, width=col_width, anchor="center")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        vsb.pack(side="right", fill="y", pady=10, padx=(0, 10))

        self.tree.bind("<Button-1>", self._on_tree_click)

    # ------------------------------------------------------------
    def _make_stat_card(self, parent, label, value, color):
        card = ctk.CTkFrame(parent, corner_radius=14,
                            fg_color=("white", COLORS["card_dark"]),
                            border_width=1, border_color=("#E2E8F0", COLORS["border_dark"]))
        value_label = ctk.CTkLabel(card, text=value, font=FONTS["kpi_value"], text_color=color)
        value_label.pack(pady=(15, 0))
        ctk.CTkLabel(card, text=label, font=FONTS["kpi_label"],
                     text_color=COLORS["muted_light"]).pack(pady=(0, 15))
        card.value_label = value_label
        return card

    # ------------------------------------------------------------
    def _on_search(self, _event=None):
        self.search_term = self.search_entry.get().strip()
        self._reload_table()

    def refresh(self):
        self.current_year = StudentController.get_current_year()
        self.next_year = StudentController.get_next_year()
        self.year_info_label.configure(
            text=f"{self.current_year}  →  {self.next_year}"
        )
        self.checked_ids = set()
        self._reload_table()
        self._update_stats()

    def _reload_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        students = Student.get_all(
            annee_scolaire=self.current_year,
            statut="Actif",
            search=self.search_term,
            order_by="eleve_nom",
        )

        for s in students:
            already = Student.get_by_matricule_year(s["matricule"], self.next_year)
            statut_text = "✅ Déjà réinscrit" if already else "⏳ En attente"

            check_symbol = "☑" if s["id"] in self.checked_ids else "☐"

            values = [check_symbol]
            for col_id, _, _ in TABLE_COLUMNS:
                if col_id == "statut_reinscription":
                    values.append(statut_text)
                elif col_id == "mensualite":
                    values.append(f"{s.get(col_id, 0):,.2f} DH".replace(",", " "))
                else:
                    values.append(s.get(col_id, ""))

            self.tree.insert("", "end", iid=str(s["id"]), values=values)

        self._update_stats()

    # ------------------------------------------------------------
    def _on_tree_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            return
        col = self.tree.identify_column(event.x)
        row = self.tree.identify_row(event.y)
        if not row:
            return

        if col == "#1":  # checkbox column
            student_id = int(row)
            if student_id in self.checked_ids:
                self.checked_ids.discard(student_id)
                self.tree.set(row, "check", "☐")
            else:
                self.checked_ids.add(student_id)
                self.tree.set(row, "check", "☑")
            self._update_stats()

    def _select_all(self):
        for item in self.tree.get_children():
            self.checked_ids.add(int(item))
            self.tree.set(item, "check", "☑")
        self._update_stats()

    def _deselect_all(self):
        self.checked_ids.clear()
        for item in self.tree.get_children():
            self.tree.set(item, "check", "☐")
        self._update_stats()

    # ------------------------------------------------------------
    def _update_stats(self):
        stats = StudentController.get_reinscription_stats(self.current_year, self.next_year)
        self.stat_total.value_label.configure(text=str(stats["total_eligible"]))
        self.stat_selected.value_label.configure(text=str(len(self.checked_ids)))
        self.stat_reinscribed.value_label.configure(text=str(stats["already_reinscribed"]))

    # ------------------------------------------------------------
    def _generate_reinscription(self):
        if not self.checked_ids:
            show_toast(self, "⚠️ Veuillez sélectionner au moins un élève.", kind="warning")
            return

        if not confirm_dialog(
            self, "Confirmer la réinscription",
            f"Générer la réinscription pour {len(self.checked_ids)} élève(s) "
            f"vers l'année {self.next_year} ?"
        ):
            return

        result = StudentController.generate_reinscriptions(
            list(self.checked_ids), self.current_year, self.next_year
        )

        show_toast(
            self,
            f"✅ Réinscription terminée : {result['created']} créé(s), "
            f"{result['updated']} mis à jour, {result['skipped']} ignoré(s).",
            kind="success", duration=4000
        )

        self.checked_ids.clear()
        self._reload_table()
