"""
==================================================================
 STUDENT PROFILE DIALOG
==================================================================
Modal window showing the complete profile of a student with
Modify / Save / Print / Delete actions.
==================================================================
"""

import customtkinter as ctk
from controllers.student_controller import StudentController
from models.student import Student
from utils.theme import COLORS, FONTS, CLASS_LEVELS, TRANSPORT_OPTIONS, STATUT_OPTIONS, BUTTON_CORNER_RADIUS
from utils.helpers import show_toast, confirm_dialog


FIELD_LABELS = [
    ("matricule", "Matricule"),
    ("eleve_nom", "Nom de l'élève"),
    ("eleve_prenom", "Prénom de l'élève"),
    ("mere", "Mère"),
    ("pere", "Père"),
    ("date_of_birth", "Date de naissance (YYYY-MM-DD)"),
    ("city_of_birth", "Ville de naissance"),
    ("adresse", "Adresse"),
    ("pere_telephone", "Téléphone Père"),
    ("mere_telephone", "Téléphone Mère"),
    ("classe", "Classe"),
    ("inscription", "Inscription (DH)"),
    ("transport_yn", "Transport (Oui/Non)"),
    ("transport", "Montant Transport (DH)"),
    ("mensualite", "Mensualité (DH)"),
    ("note_date", "Note / Date"),
]


class StudentProfileDialog(ctk.CTkToplevel):
    """Modal dialog displaying a student's full profile."""

    def __init__(self, master, student_id: int, on_change=None):
        super().__init__(master)
        self.student_id = student_id
        self.on_change = on_change  # callback to refresh parent list
        self.edit_mode = False
        self.entries = {}

        self.title("Profil de l'élève")
        self.geometry("640x800")
        self.minsize(580, 650)
        self.grab_set()
        self.transient(master)

        self.student = Student.get_by_id(student_id)
        if not self.student:
            self.destroy()
            return

        self._build_ui()
        self._load_data()

    # ------------------------------------------------------------
    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color=COLORS["primary"], corner_radius=0, height=70)
        header.pack(fill="x")

        self.header_label = ctk.CTkLabel(
            header, text="👤 Profil de l'élève", font=FONTS["h2"], text_color="white"
        )
        self.header_label.pack(side="left", padx=20, pady=15)

        # Scrollable form
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=15)
        self.scroll_frame.grid_columnconfigure(1, weight=1)

        for i, (field, label) in enumerate(FIELD_LABELS):
            lbl = ctk.CTkLabel(self.scroll_frame, text=label, font=FONTS["body_bold"], anchor="w")
            lbl.grid(row=i, column=0, sticky="w", padx=(5, 10), pady=8)

            if field == "classe":
                widget = ctk.CTkOptionMenu(self.scroll_frame, values=CLASS_LEVELS, width=280)
            elif field == "transport_yn":
                widget = ctk.CTkOptionMenu(self.scroll_frame, values=TRANSPORT_OPTIONS, width=280)
            else:
                widget = ctk.CTkEntry(
                    self.scroll_frame, width=280,
                    text_color=("#1E293B", "#F1F5F9"),
                    fg_color=("#F1F5F9", "#0F172A")
                )

            widget.grid(row=i, column=1, sticky="ew", padx=(0, 5), pady=8)
            if isinstance(widget, ctk.CTkEntry):
                widget.bind("<Key>", lambda e: "break")
                widget.configure(fg_color=("#F1F5F9", "#0F172A"))
            else:
                widget.configure(state="disabled")
            self.entries[field] = widget

        # Status row
        status_row = len(FIELD_LABELS)
        lbl = ctk.CTkLabel(self.scroll_frame, text="Statut", font=FONTS["body_bold"], anchor="w")
        lbl.grid(row=status_row, column=0, sticky="w", padx=(5, 10), pady=8)
        self.status_widget = ctk.CTkOptionMenu(self.scroll_frame, values=STATUT_OPTIONS, width=280)
        self.status_widget.grid(row=status_row, column=1, sticky="ew", padx=(0, 5), pady=8)
        self.status_widget.configure(state="disabled")

        year_row = status_row + 1
        lbl = ctk.CTkLabel(self.scroll_frame, text="Année scolaire", font=FONTS["body_bold"], anchor="w")
        lbl.grid(row=year_row, column=0, sticky="w", padx=(5, 10), pady=8)
        self.year_label = ctk.CTkLabel(self.scroll_frame, text="", font=FONTS["body"], anchor="w")
        self.year_label.grid(row=year_row, column=1, sticky="w", padx=(0, 5), pady=8)

        # Action buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))

        self.modify_btn = ctk.CTkButton(
            btn_frame, text="✏️  Modifier", fg_color=COLORS["secondary"],
            hover_color=COLORS["primary_hover"], corner_radius=BUTTON_CORNER_RADIUS,
            command=self._toggle_edit
        )
        self.modify_btn.pack(side="left", padx=5, fill="x", expand=True)

        self.print_btn = ctk.CTkButton(
            btn_frame, text="🖨️  Imprimer", fg_color=COLORS["muted_light"],
            hover_color=COLORS["muted_dark"], corner_radius=BUTTON_CORNER_RADIUS,
            command=self._print_card
        )
        self.print_btn.pack(side="left", padx=5, fill="x", expand=True)

        self.delete_btn = ctk.CTkButton(
            btn_frame, text="🗑️  Supprimer", fg_color=COLORS["danger"],
            hover_color=COLORS["danger_hover"], corner_radius=BUTTON_CORNER_RADIUS,
            command=self._delete_student
        )
        self.delete_btn.pack(side="left", padx=5, fill="x", expand=True)

    # ------------------------------------------------------------
    def _load_data(self):
        for field, widget in self.entries.items():
            value = self.student.get(field)
            if value is None:
                value = ""

            if isinstance(widget, ctk.CTkOptionMenu):
                if field == "transport_yn":
                    widget.set(value if value in TRANSPORT_OPTIONS else "No")
                elif field == "classe":
                    widget.set(value if value in CLASS_LEVELS else (CLASS_LEVELS[0]))
            else:
                widget.delete(0, "end")
                widget.insert(0, str(value))

        self.status_widget.set(self.student.get("statut") or "Actif")
        self.year_label.configure(text=self.student.get("annee_scolaire") or "")

        self.header_label.configure(
            text=f"👤 {self.student.get('eleve_prenom', '')} {self.student.get('eleve_nom', '')}"
        )

    # ------------------------------------------------------------
    def _toggle_edit(self):
        if not self.edit_mode:
            # Enter edit mode
            self.edit_mode = True
            for widget in self.entries.values():
                if isinstance(widget, ctk.CTkEntry):
                    widget.unbind("<Key>")
                    widget.configure(fg_color=("white", COLORS["card_dark"]))
                else:
                    widget.configure(state="normal")
            self.status_widget.configure(state="normal")
            self.modify_btn.configure(text="💾  Enregistrer", fg_color=COLORS["success"],
                                       hover_color=COLORS["success_hover"])
        else:
            self._save_changes()

    def _save_changes(self):
        data = {}
        for field, widget in self.entries.items():
            if isinstance(widget, ctk.CTkOptionMenu):
                data[field] = widget.get()
            else:
                data[field] = widget.get().strip()

        data["statut"] = self.status_widget.get()

        success, errors = StudentController.update_student(self.student_id, data)

        if not success:
            show_toast(self, "\n".join(errors), kind="error", duration=3500)
            return

        show_toast(self, "✅ Modifications enregistrées avec succès.", kind="success")

        # Back to read-only
        self.edit_mode = False
        for widget in self.entries.values():
            if isinstance(widget, ctk.CTkEntry):
                widget.bind("<Key>", lambda e: "break")
                widget.configure(fg_color=("#F1F5F9", "#0F172A"))
            else:
                widget.configure(state="disabled")
        self.status_widget.configure(state="disabled")
        self.modify_btn.configure(text="✏️  Modifier", fg_color=COLORS["secondary"],
                                   hover_color=COLORS["primary_hover"])

        self.student = Student.get_by_id(self.student_id)
        self._load_data()

        if self.on_change:
            self.on_change()

    # ------------------------------------------------------------
    def _delete_student(self):
        if confirm_dialog(
            self, "Confirmer la suppression",
            f"Voulez-vous vraiment supprimer l'élève "
            f"{self.student.get('eleve_prenom')} {self.student.get('eleve_nom')} ?\n"
            f"Cette action est irréversible."
        ):
            StudentController.delete_student(self.student_id)
            show_toast(self.master, "🗑️ Élève supprimé avec succès.", kind="success")
            if self.on_change:
                self.on_change()
            self.destroy()

    # ------------------------------------------------------------
    def _print_card(self):
        """Generate a simple printable text representation (HTML export)."""
        import os
        from datetime import datetime
        from database.db_manager import BASE_DIR, db_manager

        export_dir = os.path.join(BASE_DIR, "exports")
        os.makedirs(export_dir, exist_ok=True)

        filename = f"fiche_{self.student.get('matricule')}_{self.student.get('annee_scolaire', '').replace('/', '-')}.html"
        filepath = os.path.join(export_dir, filename)

        school_name = db_manager.get_setting("school_name", "Le Schéma")
        logo_path = os.path.join(BASE_DIR, "assets", "icons", "school_logo.png")
        logo_html = ""
        if os.path.exists(logo_path):
            logo_uri = "file://" + logo_path.replace("\\", "/")
            logo_html = f'<img src="{logo_uri}" alt="Logo" class="logo">'

        html = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <title>Fiche Élève - {self.student.get('eleve_prenom')} {self.student.get('eleve_nom')}</title>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; padding: 40px; background: #F8FAFC; }}
                .card {{ background: white; border-radius: 14px; padding: 30px; max-width: 600px;
                         margin: auto; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }}
                .logo {{ max-width: 160px; max-height: 120px; display: block; margin: 0 auto 10px; }}
                h1 {{ color: #2563EB; margin-bottom: 5px; }}
                .row {{ display: flex; justify-content: space-between; padding: 8px 0;
                        border-bottom: 1px solid #E2E8F0; }}
                .label {{ color: #64748B; font-weight: 600; }}
                .value {{ font-weight: 500; }}
                .header {{ text-align: center; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="header">
                    {logo_html}
                    <h1>Fiche Élève</h1>
                    <p>{school_name} — {self.student.get('annee_scolaire', '')}</p>
                </div>
        """
        for field, label in FIELD_LABELS:
            value = self.student.get(field, "")
            html += f'<div class="row"><span class="label">{label}</span><span class="value">{value}</span></div>'

        html += f"""
                <div class="row"><span class="label">Statut</span><span class="value">{self.student.get('statut', '')}</span></div>
                <p style="margin-top:20px;color:#94A3B8;font-size:12px;">
                    Généré le {datetime.now().strftime('%Y-%m-%d %H:%M')}
                </p>
            </div>
        </body>
        </html>
        """

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)

        show_toast(self, f"🖨️ Fiche générée: exports/{filename}", kind="info", duration=3500)

        # Try to open in default browser
        try:
            import webbrowser
            webbrowser.open(f"file://{filepath}")
        except Exception:
            pass
