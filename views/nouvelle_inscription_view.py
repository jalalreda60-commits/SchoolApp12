"""
==================================================================
 NOUVELLE INSCRIPTION VIEW
==================================================================
Modern registration form to create a new student record with
auto matricule generation, field validation and instant save.
==================================================================
"""

import customtkinter as ctk
from controllers.student_controller import StudentController
from utils.theme import COLORS, FONTS, CLASS_LEVELS, TRANSPORT_OPTIONS, BUTTON_CORNER_RADIUS
from utils.helpers import show_toast


FORM_FIELDS = [
    ("matricule", "Matricule", "entry"),
    ("eleve_nom", "Nom de l'élève *", "entry"),
    ("eleve_prenom", "Prénom de l'élève *", "entry"),
    ("mere", "Nom de la mère", "entry"),
    ("pere", "Nom du père", "entry"),
    ("date_of_birth", "Date de naissance (YYYY-MM-DD)", "entry"),
    ("city_of_birth", "Ville de naissance", "entry"),
    ("adresse", "Adresse", "entry"),
    ("pere_telephone", "Téléphone Père", "entry"),
    ("mere_telephone", "Téléphone Mère", "entry"),
    ("classe", "Classe *", "classe"),
    ("inscription", "Frais d'inscription (DH)", "entry"),
    ("transport_yn", "Transport", "transport"),
    ("transport", "Montant Transport (DH)", "entry"),
    ("mensualite", "Mensualité (DH)", "entry"),
    ("note_date", "Note / Remarque", "entry"),
]


class NouvelleInscriptionView(ctk.CTkFrame):
    """New registration page."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.entries = {}
        self._build_ui()

    # ------------------------------------------------------------
    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(20, 10))

        ctk.CTkLabel(
            header, text="📝 Nouvelle Inscription", font=FONTS["h1"], anchor="w"
        ).pack(side="left")

        self.year_label = ctk.CTkLabel(
            header, text=f"Année scolaire : {StudentController.get_current_year()}",
            font=FONTS["body_bold"], text_color=COLORS["primary"]
        )
        self.year_label.pack(side="right")

        # Scrollable form card
        card = ctk.CTkScrollableFrame(
            self, fg_color=("white", COLORS["card_dark"]),
            corner_radius=14
        )
        card.pack(fill="both", expand=True, padx=25, pady=(0, 15))
        card.grid_columnconfigure((0, 1), weight=1, uniform="form")

        for i, (field, label, widget_type) in enumerate(FORM_FIELDS):
            row = i // 2
            col = i % 2

            container = ctk.CTkFrame(card, fg_color="transparent")
            container.grid(row=row, column=col, sticky="ew", padx=15, pady=8)
            container.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(container, text=label, font=FONTS["body_bold"], anchor="w").pack(
                fill="x", pady=(0, 4)
            )

            if widget_type == "classe":
                widget = ctk.CTkOptionMenu(container, values=CLASS_LEVELS)
                widget.set(CLASS_LEVELS[0])
            elif widget_type == "transport":
                widget = ctk.CTkOptionMenu(container, values=TRANSPORT_OPTIONS)
                widget.set("No")
            else:
                widget = ctk.CTkEntry(container, placeholder_text=label)

            widget.pack(fill="x")
            self.entries[field] = widget

        # Auto-generate matricule on load
        self._auto_fill_matricule()

        # Action buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=25, pady=(0, 20))

        ctk.CTkButton(
            btn_frame, text="🔄 Régénérer Matricule", width=180,
            fg_color=COLORS["muted_light"], hover_color=COLORS["muted_dark"],
            corner_radius=BUTTON_CORNER_RADIUS, command=self._auto_fill_matricule
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="🧹 Réinitialiser", width=140,
            fg_color=COLORS["warning"], hover_color=COLORS["warning_hover"],
            corner_radius=BUTTON_CORNER_RADIUS, command=self._reset_form
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="✅ Enregistrer l'inscription", width=240,
            fg_color=COLORS["success"], hover_color=COLORS["success_hover"],
            corner_radius=BUTTON_CORNER_RADIUS, font=FONTS["body_bold"],
            command=self._save_registration
        ).pack(side="right", padx=5)

    # ------------------------------------------------------------
    def _auto_fill_matricule(self):
        matricule = StudentController.generate_matricule()
        widget = self.entries["matricule"]
        widget.delete(0, "end")
        widget.insert(0, matricule)

    def _reset_form(self):
        for field, widget in self.entries.items():
            if isinstance(widget, ctk.CTkOptionMenu):
                if field == "classe":
                    widget.set(CLASS_LEVELS[0])
                elif field == "transport_yn":
                    widget.set("No")
            else:
                widget.delete(0, "end")
        self._auto_fill_matricule()

    # ------------------------------------------------------------
    def _save_registration(self):
        data = {}
        for field, widget in self.entries.items():
            if isinstance(widget, ctk.CTkOptionMenu):
                data[field] = widget.get()
            else:
                data[field] = widget.get().strip()

        # Convert numeric fields
        for field in ("inscription", "transport", "mensualite"):
            try:
                data[field] = float(data.get(field, 0) or 0)
            except ValueError:
                show_toast(self, f"⚠️ Le champ '{field}' doit être un nombre.", kind="error")
                return

        current_year = StudentController.get_current_year()
        new_id, errors = StudentController.create_student(data, current_year)

        if errors:
            show_toast(self, "\n".join(errors), kind="error", duration=3500)
            return

        show_toast(
            self,
            f"✅ Élève {data['eleve_prenom']} {data['eleve_nom']} inscrit avec succès !",
            kind="success", duration=3000
        )

        self._reset_form()

    # ------------------------------------------------------------
    def refresh(self):
        """Called when the page becomes active - refresh year label and matricule."""
        self.year_label.configure(text=f"Année scolaire : {StudentController.get_current_year()}")
