"""
==================================================================
 SETTINGS VIEW
==================================================================
Application settings: appearance (light/dark), school years
configuration, manual backup, and general info.
==================================================================
"""

import os
import customtkinter as ctk
from PIL import Image
from database.db_manager import db_manager, BASE_DIR
from controllers.student_controller import StudentController
from utils.theme import COLORS, FONTS, BUTTON_CORNER_RADIUS
from utils.helpers import show_toast


class SettingsView(ctk.CTkFrame):
    """Settings page."""

    def __init__(self, master, on_appearance_change=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_appearance_change = on_appearance_change
        self._build_ui()

    # ------------------------------------------------------------
    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(20, 15))
        ctk.CTkLabel(header, text="⚙️ Paramètres", font=FONTS["h1"], anchor="w").pack(side="left")

        # ---- Appearance card ----
        appearance_card = self._make_card("🎨 Apparence")
        appearance_card.pack(fill="x", padx=25, pady=10)

        ctk.CTkLabel(appearance_card, text="Mode d'affichage", font=FONTS["body_bold"]).pack(
            anchor="w", padx=20, pady=(15, 5)
        )

        mode_frame = ctk.CTkFrame(appearance_card, fg_color="transparent")
        mode_frame.pack(fill="x", padx=20, pady=(0, 15))

        current_mode = db_manager.get_setting("appearance_mode", "Light")
        self.appearance_var = ctk.StringVar(value=current_mode)

        self.appearance_switch = ctk.CTkSegmentedButton(
            mode_frame, values=["Light", "Dark"],
            variable=self.appearance_var, command=self._change_appearance
        )
        self.appearance_switch.pack(anchor="w")

        # ---- School Years card ----
        years_card = self._make_card("📅 Années Scolaires")
        years_card.pack(fill="x", padx=25, pady=10)

        ctk.CTkLabel(years_card, text="Année scolaire courante", font=FONTS["body_bold"]).pack(
            anchor="w", padx=20, pady=(15, 5)
        )
        self.current_year_entry = ctk.CTkEntry(years_card, width=200)
        self.current_year_entry.insert(0, StudentController.get_current_year())
        self.current_year_entry.pack(anchor="w", padx=20, pady=(0, 10))

        ctk.CTkLabel(years_card, text="Année scolaire suivante", font=FONTS["body_bold"]).pack(
            anchor="w", padx=20, pady=(5, 5)
        )
        self.next_year_entry = ctk.CTkEntry(years_card, width=200)
        self.next_year_entry.insert(0, StudentController.get_next_year())
        self.next_year_entry.pack(anchor="w", padx=20, pady=(0, 10))

        ctk.CTkButton(
            years_card, text="💾 Enregistrer les années",
            fg_color=COLORS["success"], hover_color=COLORS["success_hover"],
            corner_radius=BUTTON_CORNER_RADIUS, command=self._save_years
        ).pack(anchor="w", padx=20, pady=(0, 15))

        # ---- School info card ----
        info_card = self._make_card("🏫 Informations de l'établissement")
        info_card.pack(fill="x", padx=25, pady=10)

        # Logo preview
        logo_path = os.path.join(BASE_DIR, "assets", "icons", "school_logo.png")
        if os.path.exists(logo_path):
            try:
                pil_logo = Image.open(logo_path)
                ratio = pil_logo.width / pil_logo.height
                target_h = 90
                target_w = int(target_h * ratio)
                logo_image = ctk.CTkImage(
                    light_image=pil_logo, dark_image=pil_logo,
                    size=(target_w, target_h)
                )
                logo_label = ctk.CTkLabel(info_card, image=logo_image, text="")
                logo_label.pack(anchor="w", padx=20, pady=(15, 5))
            except Exception:
                pass

        ctk.CTkLabel(info_card, text="Nom de l'établissement", font=FONTS["body_bold"]).pack(
            anchor="w", padx=20, pady=(5, 5)
        )
        self.school_name_entry = ctk.CTkEntry(info_card, width=350)
        self.school_name_entry.insert(0, db_manager.get_setting("school_name", ""))
        self.school_name_entry.pack(anchor="w", padx=20, pady=(0, 10))

        ctk.CTkButton(
            info_card, text="💾 Enregistrer",
            fg_color=COLORS["success"], hover_color=COLORS["success_hover"],
            corner_radius=BUTTON_CORNER_RADIUS, command=self._save_school_info
        ).pack(anchor="w", padx=20, pady=(0, 15))

        # ---- Backup card ----
        backup_card = self._make_card("💾 Sauvegarde")
        backup_card.pack(fill="x", padx=25, pady=10)

        self.backup_info_label = ctk.CTkLabel(
            backup_card, text=self._backup_info_text(), font=FONTS["body"],
            text_color=COLORS["muted_light"]
        )
        self.backup_info_label.pack(anchor="w", padx=20, pady=(15, 5))

        ctk.CTkButton(
            backup_card, text="📦 Créer une sauvegarde maintenant",
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            corner_radius=BUTTON_CORNER_RADIUS, command=self._create_backup
        ).pack(anchor="w", padx=20, pady=(0, 15))

        # ---- About card ----
        about_card = self._make_card("ℹ️ À propos")
        about_card.pack(fill="x", padx=25, pady=10)

        ctk.CTkLabel(
            about_card,
            text="Private School Management System v1.0\n"
                 "Développé avec Python, CustomTkinter, SQLite & Pandas.\n"
                 "© 2026 - Tous droits réservés.",
            font=FONTS["body"], text_color=COLORS["muted_light"], justify="left"
        ).pack(anchor="w", padx=20, pady=15)

    # ------------------------------------------------------------
    def _make_card(self, title):
        card = ctk.CTkFrame(self, corner_radius=14,
                             fg_color=("white", COLORS["card_dark"]),
                             border_width=1, border_color=("#E2E8F0", COLORS["border_dark"]))
        ctk.CTkLabel(card, text=title, font=FONTS["h3"]).pack(anchor="w", padx=20, pady=(15, 0))
        return card

    def _backup_info_text(self):
        last = db_manager.get_setting("last_backup", "")
        if last:
            return f"Dernière sauvegarde : {last}"
        return "Aucune sauvegarde effectuée."

    # ------------------------------------------------------------
    def _change_appearance(self, value):
        ctk.set_appearance_mode(value)
        db_manager.set_setting("appearance_mode", value)
        if self.on_appearance_change:
            self.on_appearance_change(value)
        show_toast(self, f"🎨 Mode {value} activé.", kind="success")

    def _save_years(self):
        current = self.current_year_entry.get().strip()
        next_y = self.next_year_entry.get().strip()

        if not current or not next_y:
            show_toast(self, "⚠️ Les deux années doivent être renseignées.", kind="error")
            return

        StudentController.set_current_year(current)
        StudentController.set_next_year(next_y)
        show_toast(self, "✅ Années scolaires mises à jour avec succès.", kind="success")

    def _save_school_info(self):
        name = self.school_name_entry.get().strip()
        db_manager.set_setting("school_name", name)
        show_toast(self, "✅ Informations enregistrées.", kind="success")

    def _create_backup(self):
        path = db_manager.backup_database()
        self.backup_info_label.configure(text=self._backup_info_text())
        show_toast(self, f"📦 Sauvegarde créée avec succès.", kind="success", duration=3000)
