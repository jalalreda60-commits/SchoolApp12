"""
==================================================================
 GESTION DES PAIEMENTS VIEW
==================================================================
Main payment management page:
  - "Ajouter Paiement" button opens student search dialog
  - Displays selected student's info (Matricule, Nom, Prénom,
    Classe, Inscription, Transport, Mensualité, Total à payer, ...)
  - Shows the Septembre→Juin payment status grid with colors
  - Payment form (type, month auto-suggested, amount, date, notes)
  - On save: updates DB, regenerates status, generates PDF receipt
  - Payment history timeline with filters (year, class, month)
  - Import Excel button for historical payment data
==================================================================
"""

import os
import customtkinter as ctk
from tkinter import ttk, filedialog
from datetime import datetime

from models.student import Student
from models.payment import Payment
from controllers.student_controller import StudentController
from controllers.payment_controller import PaymentController
from controllers.payment_excel_controller import PaymentExcelController
from utils.theme import (
    COLORS, FONTS, BUTTON_CORNER_RADIUS, MONTHS_ORDER, PAYMENT_TYPES,
    PAYMENT_STATUS_COLORS, PAYMENT_STATUS_LABELS, STATUS_PAID, STATUS_UNPAID, STATUS_NAN,
)
from utils.helpers import show_toast, format_currency
from utils.receipt_generator import generate_receipt_pdf
from views.components.student_search_dialog import StudentSearchDialog
from views.components.payment_status_grid import PaymentStatusGrid


class GestionPaiementsView(ctk.CTkFrame):
    """Payment management page."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.current_year = StudentController.get_current_year()
        self.selected_student_id = None
        self.summary = None

        self._build_ui()
        self.refresh()

    # ==============================================================
    # UI CONSTRUCTION
    # ==============================================================
    def _build_ui(self):
        # ---- Header ----
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(20, 10))

        ctk.CTkLabel(
            header, text="💰 Gestion des Paiements", font=FONTS["h1"], anchor="w"
        ).pack(side="left")

        toolbar = ctk.CTkFrame(header, fg_color="transparent")
        toolbar.pack(side="right")

        ctk.CTkButton(
            toolbar, text="📥 Importer Excel", fg_color=COLORS["success"],
            hover_color=COLORS["success_hover"], width=150,
            corner_radius=BUTTON_CORNER_RADIUS, command=self._open_import
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            toolbar, text="➕ Ajouter Paiement", fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"], width=160,
            corner_radius=BUTTON_CORNER_RADIUS, font=FONTS["body_bold"],
            command=self._open_student_search
        ).pack(side="left", padx=4)

        # ---- Scrollable content ----
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=25, pady=(0, 15))

        # ---- Empty state placeholder ----
        self.empty_label = ctk.CTkLabel(
            self.scroll,
            text="👈 Cliquez sur \"Ajouter Paiement\" pour rechercher et\n"
                 "sélectionner un élève.",
            font=FONTS["h3"], text_color=COLORS["muted_light"],
            justify="center"
        )
        self.empty_label.pack(pady=80)

        # ---- Student info card (hidden until a student is selected) ----
        self.student_card = ctk.CTkFrame(
            self.scroll, corner_radius=14,
            fg_color=("white", COLORS["card_dark"]),
            border_width=1, border_color=("#E2E8F0", COLORS["border_dark"])
        )

        self.student_header_label = ctk.CTkLabel(
            self.student_card, text="", font=FONTS["h2"], anchor="w"
        )
        self.student_header_label.pack(fill="x", padx=20, pady=(15, 5), anchor="w")

        # Info grid (Matricule, Classe, Inscription, Transport, Mensualité, Total à payer)
        self.info_grid = ctk.CTkFrame(self.student_card, fg_color="transparent")
        self.info_grid.pack(fill="x", padx=20, pady=(5, 10))
        for i in range(4):
            self.info_grid.grid_columnconfigure(i, weight=1, uniform="info")

        self.info_labels = {}
        info_fields = [
            ("matricule", "Matricule"), ("classe", "Classe"),
            ("inscription", "Inscription"), ("transport", "Transport"),
            ("mensualite", "Mensualité"), ("total_a_payer", "Total à payer"),
            ("total_paid", "Total payé"), ("remaining", "Reste à payer"),
        ]
        for i, (key, label) in enumerate(info_fields):
            row, col = i // 4, i % 4
            cell = ctk.CTkFrame(self.info_grid, fg_color=("#F8FAFC", "#0F172A"), corner_radius=10)
            cell.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            ctk.CTkLabel(cell, text=label, font=FONTS["small"],
                         text_color=COLORS["muted_light"]).pack(pady=(8, 0), padx=10, anchor="w")
            value_label = ctk.CTkLabel(cell, text="—", font=FONTS["body_bold"], anchor="w")
            value_label.pack(pady=(0, 8), padx=10, anchor="w")
            self.info_labels[key] = value_label

        # ---- Payment status grid ----
        ctk.CTkLabel(
            self.student_card, text="📅 Historique de paiement mensuel",
            font=FONTS["body_bold"]
        ).pack(anchor="w", padx=20, pady=(10, 5))

        self.status_grid = PaymentStatusGrid(self.student_card)
        self.status_grid.pack(fill="x", padx=20, pady=(0, 5))

        self.next_unpaid_label = ctk.CTkLabel(
            self.student_card, text="", font=FONTS["body_bold"],
            text_color=COLORS["warning"]
        )
        self.next_unpaid_label.pack(anchor="w", padx=20, pady=(0, 15))

        # ---- Payment form ----
        form_title = ctk.CTkLabel(
            self.student_card, text="💳 Nouveau Paiement", font=FONTS["h3"]
        )
        form_title.pack(anchor="w", padx=20, pady=(5, 10))

        form_frame = ctk.CTkFrame(self.student_card, fg_color="transparent")
        form_frame.pack(fill="x", padx=20, pady=(0, 10))
        for i in range(4):
            form_frame.grid_columnconfigure(i, weight=1, uniform="form")

        # Payment type
        ctk.CTkLabel(form_frame, text="Type de paiement", font=FONTS["body_bold"]).grid(
            row=0, column=0, sticky="w", padx=5, pady=(0, 2)
        )
        self.payment_type_var = ctk.StringVar(value=PAYMENT_TYPES[1])
        self.payment_type_menu = ctk.CTkOptionMenu(
            form_frame, values=PAYMENT_TYPES, variable=self.payment_type_var,
            command=self._on_payment_type_change
        )
        self.payment_type_menu.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 10))

        # Month
        ctk.CTkLabel(form_frame, text="Mois concerné", font=FONTS["body_bold"]).grid(
            row=0, column=1, sticky="w", padx=5, pady=(0, 2)
        )
        self.month_var = ctk.StringVar(value="")
        self.month_menu = ctk.CTkOptionMenu(
            form_frame, values=MONTHS_ORDER, variable=self.month_var
        )
        self.month_menu.grid(row=1, column=1, sticky="ew", padx=5, pady=(0, 10))

        # Amount
        ctk.CTkLabel(form_frame, text="Montant (DH)", font=FONTS["body_bold"]).grid(
            row=0, column=2, sticky="w", padx=5, pady=(0, 2)
        )
        self.amount_entry = ctk.CTkEntry(form_frame, placeholder_text="0.00")
        self.amount_entry.grid(row=1, column=2, sticky="ew", padx=5, pady=(0, 10))

        # Date
        ctk.CTkLabel(form_frame, text="Date de paiement", font=FONTS["body_bold"]).grid(
            row=0, column=3, sticky="w", padx=5, pady=(0, 2)
        )
        self.date_entry = ctk.CTkEntry(form_frame, placeholder_text="AAAA-MM-JJ")
        self.date_entry.grid(row=1, column=3, sticky="ew", padx=5, pady=(0, 10))
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        # Notes
        ctk.CTkLabel(form_frame, text="Notes", font=FONTS["body_bold"]).grid(
            row=2, column=0, columnspan=4, sticky="w", padx=5, pady=(0, 2)
        )
        self.notes_entry = ctk.CTkEntry(form_frame, placeholder_text="Remarques (optionnel)")
        self.notes_entry.grid(row=3, column=0, columnspan=4, sticky="ew", padx=5, pady=(0, 10))

        # Save button
        save_btn_frame = ctk.CTkFrame(self.student_card, fg_color="transparent")
        save_btn_frame.pack(fill="x", padx=20, pady=(0, 20))

        self.save_btn = ctk.CTkButton(
            save_btn_frame, text="✅ Enregistrer Paiement", font=FONTS["body_bold"],
            fg_color=COLORS["success"], hover_color=COLORS["success_hover"],
            corner_radius=BUTTON_CORNER_RADIUS, height=42,
            command=self._save_payment
        )
        self.save_btn.pack(side="left", fill="x", expand=True)

        # ---- Payment history section ----
        self.history_card = ctk.CTkFrame(
            self.scroll, corner_radius=14,
            fg_color=("white", COLORS["card_dark"]),
            border_width=1, border_color=("#E2E8F0", COLORS["border_dark"])
        )

        ctk.CTkLabel(
            self.history_card, text="🧾 Historique des Paiements", font=FONTS["h3"]
        ).pack(anchor="w", padx=20, pady=(15, 10))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("History.Treeview", rowheight=32,
                        background="white", fieldbackground="white",
                        font=("Segoe UI", 10))
        style.configure("History.Treeview.Heading",
                        background=COLORS["primary"], foreground="white",
                        font=("Segoe UI", 10, "bold"), relief="flat")

        history_table_frame = ctk.CTkFrame(self.history_card, fg_color="transparent")
        history_table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        columns = ("mois", "type", "montant", "date", "recu")
        self.history_tree = ttk.Treeview(
            history_table_frame, columns=columns, show="headings",
            style="History.Treeview", height=8, selectmode="browse"
        )
        headers = {
            "mois": ("Mois", 100), "type": ("Type", 120),
            "montant": ("Montant", 110), "date": ("Date Paiement", 120),
            "recu": ("N° Reçu", 160),
        }
        for col, (label, width) in headers.items():
            self.history_tree.heading(col, text=label)
            self.history_tree.column(col, width=width, anchor="center")

        vsb = ttk.Scrollbar(history_table_frame, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=vsb.set)
        self.history_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

    # ==============================================================
    # NAVIGATION / SELECTION
    # ==============================================================
    def _open_student_search(self):
        StudentSearchDialog(self, on_select=self._select_student, annee_scolaire=self.current_year)

    def _select_student(self, student_id: int):
        self.selected_student_id = student_id
        self._load_student()

    # ==============================================================
    # LOAD STUDENT DATA
    # ==============================================================
    def _load_student(self):
        if not self.selected_student_id:
            return

        self.summary = PaymentController.get_student_summary(
            self.selected_student_id, self.current_year
        )
        if not self.summary:
            show_toast(self, "⚠️ Élève introuvable pour cette année scolaire.", kind="warning")
            return

        student = self.summary["student"]

        # Show student card, hide empty state
        self.empty_label.pack_forget()
        if not self.student_card.winfo_ismapped():
            self.student_card.pack(fill="x", pady=(0, 15))
        if not self.history_card.winfo_ismapped():
            self.history_card.pack(fill="x", pady=(0, 15))

        self.student_header_label.configure(
            text=f"👤 {student.get('eleve_prenom', '')} {student.get('eleve_nom', '')} "
                 f"— {student.get('classe', '')} ({self.current_year})"
        )

        self.info_labels["matricule"].configure(text=str(student.get("matricule", "")))
        self.info_labels["classe"].configure(text=str(student.get("classe", "")))
        self.info_labels["inscription"].configure(text=format_currency(student.get("inscription", 0)))
        self.info_labels["transport"].configure(text=format_currency(student.get("transport", 0)))
        self.info_labels["mensualite"].configure(text=format_currency(student.get("mensualite", 0)))
        self.info_labels["total_a_payer"].configure(text=format_currency(self.summary["total_a_payer"]))
        self.info_labels["total_paid"].configure(text=format_currency(self.summary["total_paid"]))
        self.info_labels["remaining"].configure(text=format_currency(self.summary["remaining"]))

        # Status grid
        self.status_grid.update_status(self.summary["status_map"])

        # Next unpaid month suggestion
        next_month = self.summary["next_unpaid_month"]
        if next_month:
            self.next_unpaid_label.configure(
                text=f"💡 Prochain mois à payer suggéré : {next_month}"
            )
            self.month_var.set(next_month)
        else:
            self.next_unpaid_label.configure(
                text="✅ Tous les mois sont payés ou non concernés."
            )
            self.month_var.set(MONTHS_ORDER[0])

        # Reset form defaults
        self.payment_type_var.set("Mensualité")
        self._on_payment_type_change("Mensualité")
        self.amount_entry.delete(0, "end")
        self.amount_entry.insert(0, f"{student.get('mensualite', 0):.2f}")
        self.date_entry.delete(0, "end")
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.notes_entry.delete(0, "end")

        self._reload_history()

    def _on_payment_type_change(self, value):
        """Adjust month dropdown and amount suggestion based on payment type."""
        if not self.summary:
            return
        student = self.summary["student"]

        if value == "Inscription":
            self.month_menu.configure(state="disabled")
            self.amount_entry.delete(0, "end")
            self.amount_entry.insert(0, f"{student.get('inscription', 0):.2f}")
        elif value == "Transport":
            self.month_menu.configure(state="normal")
            self.amount_entry.delete(0, "end")
            self.amount_entry.insert(0, f"{student.get('transport', 0):.2f}")
        else:  # Mensualité
            self.month_menu.configure(state="normal")
            self.amount_entry.delete(0, "end")
            self.amount_entry.insert(0, f"{student.get('mensualite', 0):.2f}")

    # ==============================================================
    # PAYMENT HISTORY TABLE
    # ==============================================================
    def _reload_history(self):
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        if not self.selected_student_id:
            return

        history = Payment.get_payments_for_student(self.selected_student_id, self.current_year)
        for p in history:
            self.history_tree.insert("", "end", values=(
                p.get("mois") or "—",
                p.get("payment_type", ""),
                format_currency(p.get("montant", 0)),
                p.get("date_paiement", ""),
                p.get("receipt_number", ""),
            ))

    # ==============================================================
    # SAVE PAYMENT
    # ==============================================================
    def _save_payment(self):
        if not self.selected_student_id:
            show_toast(self, "⚠️ Veuillez sélectionner un élève.", kind="warning")
            return

        payment_type = self.payment_type_var.get()
        mois = self.month_var.get() if payment_type != "Inscription" else None

        data = {
            "student_id": self.selected_student_id,
            "annee_scolaire": self.current_year,
            "payment_type": payment_type,
            "mois": mois,
            "montant": self.amount_entry.get().strip(),
            "date_paiement": self.date_entry.get().strip(),
            "notes": self.notes_entry.get().strip(),
        }

        payment_id, receipt_number, errors = PaymentController.save_payment(data)

        if errors:
            show_toast(self, "\n".join(errors), kind="error", duration=3500)
            return

        # Recompute summary for receipt info
        montant = float(data["montant"])
        updated_summary = PaymentController.get_student_summary(
            self.selected_student_id, self.current_year
        )

        # ---- Generate PDF receipt ----
        try:
            receipt_data = {
                "receipt_number": receipt_number,
                "payment_type": payment_type,
                "mois": mois,
                "montant": montant,
                "date_paiement": data["date_paiement"],
                "notes": data["notes"],
                "annee_scolaire": self.current_year,
                "remaining": updated_summary["remaining"],
            }
            pdf_path = generate_receipt_pdf(receipt_data, updated_summary["student"])
            Payment.create_receipt(payment_id, receipt_number, pdf_path)
        except Exception as e:
            pdf_path = None
            show_toast(self, f"⚠️ Paiement enregistré mais erreur PDF: {e}", kind="warning", duration=4000)

        show_toast(
            self,
            f"✅ Paiement enregistré ! Reçu N° {receipt_number}",
            kind="success", duration=3500
        )

        # Refresh UI
        self._load_student()

        # Try to open the PDF
        if pdf_path and os.path.exists(pdf_path):
            try:
                import webbrowser
                webbrowser.open(f"file://{pdf_path}")
            except Exception:
                pass

    # ==============================================================
    # IMPORT
    # ==============================================================
    def _open_import(self):
        from views.components.payment_import_dialog import PaymentImportDialog
        PaymentImportDialog(self, default_annee_scolaire=self.current_year, on_complete=self._on_import_complete)

    def _on_import_complete(self):
        if self.selected_student_id:
            self._load_student()

    # ==============================================================
    # REFRESH (called on page navigation)
    # ==============================================================
    def refresh(self):
        self.current_year = StudentController.get_current_year()
        if self.selected_student_id:
            self._load_student()
