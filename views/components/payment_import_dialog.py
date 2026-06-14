"""
==================================================================
 PAYMENT IMPORT DIALOG
==================================================================
Modal dialog allowing the user to pick the payment Excel file,
run the import, and view a summary of created/updated students
and the monthly status grid update.
==================================================================
"""

import customtkinter as ctk
from tkinter import filedialog
from controllers.payment_excel_controller import PaymentExcelController
from utils.theme import COLORS, FONTS, BUTTON_CORNER_RADIUS


class PaymentImportDialog(ctk.CTkToplevel):
    """Modal dialog for importing payment history from Excel."""

    def __init__(self, master, default_annee_scolaire: str, on_complete=None):
        super().__init__(master)
        self.default_annee_scolaire = default_annee_scolaire
        self.on_complete = on_complete
        self.selected_file = None

        self.title("Importer Historique de Paiements")
        self.geometry("600x500")
        self.resizable(False, False)
        self.grab_set()
        self.transient(master)

        self._build_ui()

    # ------------------------------------------------------------
    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color=COLORS["primary"], corner_radius=0, height=70)
        header.pack(fill="x")
        ctk.CTkLabel(
            header, text="📥 Importation Paiements Excel",
            font=FONTS["h2"], text_color="white"
        ).pack(side="left", padx=20, pady=15)

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=25, pady=20)

        ctk.CTkLabel(
            content,
            text=f"Année scolaire par défaut (si colonne 'Year' vide) : {self.default_annee_scolaire}",
            font=FONTS["body_bold"]
        ).pack(anchor="w", pady=(0, 15))

        # File picker
        file_frame = ctk.CTkFrame(content, fg_color="transparent")
        file_frame.pack(fill="x", pady=5)

        self.file_label = ctk.CTkLabel(
            file_frame, text="Aucun fichier sélectionné",
            font=FONTS["body"], text_color=COLORS["muted_light"], anchor="w"
        )
        self.file_label.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            file_frame, text="📂 Choisir un fichier", width=160,
            fg_color=COLORS["secondary"], hover_color=COLORS["primary_hover"],
            corner_radius=BUTTON_CORNER_RADIUS, command=self._browse_file
        ).pack(side="right")

        # Info box
        info_box = ctk.CTkFrame(content, fg_color=("#EFF6FF", "#1E3A5F"), corner_radius=10)
        info_box.pack(fill="x", pady=15)
        ctk.CTkLabel(
            info_box,
            text=("ℹ️ Colonnes attendues :\nMatricule, Nom, Prénom, Classe, Inscription, "
                  "Transport, Mensualité, Total a payé, Note/Date, Year,\n"
                  "Septembre, Octobre, Novembre, Décembre, Janvier, Février, "
                  "Mars, Avril, Mai, Juin\n\n"
                  "Valeurs mensuelles acceptées : 'Payé' (payé), vide (impayé), "
                  "'NAN' (non inscrit)."),
            font=FONTS["small"], justify="left", wraplength=520
        ).pack(padx=15, pady=12, anchor="w")

        # Results
        self.result_box = ctk.CTkTextbox(content, height=140, font=FONTS["small"])
        self.result_box.pack(fill="both", expand=True, pady=(0, 10))
        self.result_box.insert("1.0", "En attente d'un fichier...")
        self.result_box.configure(state="disabled")

        # Buttons
        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(fill="x")

        self.import_btn = ctk.CTkButton(
            btn_frame, text="📥 Importer", fg_color=COLORS["success"],
            hover_color=COLORS["success_hover"], corner_radius=BUTTON_CORNER_RADIUS,
            command=self._run_import, state="disabled"
        )
        self.import_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        ctk.CTkButton(
            btn_frame, text="Fermer", fg_color=COLORS["muted_light"],
            hover_color=COLORS["muted_dark"], corner_radius=BUTTON_CORNER_RADIUS,
            command=self.destroy
        ).pack(side="left", fill="x", expand=True, padx=(5, 0))

    # ------------------------------------------------------------
    def _browse_file(self):
        path = filedialog.askopenfilename(
            title="Sélectionner le fichier de paiements",
            filetypes=[("Fichiers Excel", "*.xlsx *.xls")]
        )
        if path:
            self.selected_file = path
            filename = path.split("/")[-1].split("\\")[-1]
            self.file_label.configure(text=f"📄 {filename}", text_color=COLORS["text_light"])
            self.import_btn.configure(state="normal")

    def _set_result_text(self, text: str):
        self.result_box.configure(state="normal")
        self.result_box.delete("1.0", "end")
        self.result_box.insert("1.0", text)
        self.result_box.configure(state="disabled")

    def _run_import(self):
        if not self.selected_file:
            return

        self._set_result_text("⏳ Importation en cours...")
        self.update()

        result = PaymentExcelController.import_excel(self.selected_file, self.default_annee_scolaire)

        summary = (
            f"✅ Importation terminée\n\n"
            f"Lignes totales       : {result['total_rows']}\n"
            f"Élèves créés         : {result['students_created']}\n"
            f"Élèves mis à jour    : {result['students_updated']}\n"
            f"Lignes ignorées      : {result['skipped']}\n"
        )

        if result["errors"]:
            summary += "\n--- Erreurs ---\n"
            for err in result["errors"][:20]:
                summary += f"Ligne {err['row']}: {err['message']}\n"
            if len(result["errors"]) > 20:
                summary += f"... et {len(result['errors']) - 20} autres erreurs.\n"

        self._set_result_text(summary)

        if self.on_complete:
            self.on_complete()
