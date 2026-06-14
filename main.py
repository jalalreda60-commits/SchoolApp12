"""
==================================================================
 MAIN APPLICATION
==================================================================
Entry point of the Private School Management System.
Sets up the main window, sidebar navigation, and routes between
pages (Dashboard, Gestion Élèves, Nouvelle Inscription,
Réinscription, Settings).
==================================================================
"""

import os
import customtkinter as ctk
from database.db_manager import db_manager, BASE_DIR

from views.components.sidebar import Sidebar
from views.dashboard_view import DashboardView
from views.gestion_eleves_view import GestionElevesView
from views.nouvelle_inscription_view import NouvelleInscriptionView
from views.reinscription_view import ReinscriptionView
from views.gestion_paiements_view import GestionPaiementsView
from views.settings_view import SettingsView


# Navigation items: (key, label, icon)
NAV_ITEMS = [
    ("dashboard", "Dashboard", "📊"),
    ("gestion_eleves", "Gestion Élèves", "🎓"),
    ("nouvelle_inscription", "Nouvelle Inscription", "📝"),
    ("reinscription", "Réinscription", "🔁"),
    ("gestion_paiements", "Gestion des Paiements", "💰"),
    ("settings", "Paramètres", "⚙️"),
]


class SchoolManagementApp(ctk.CTk):
    """Main application window."""

    def __init__(self):
        super().__init__()

        # Load saved appearance mode
        saved_mode = db_manager.get_setting("appearance_mode", "Light")
        ctk.set_appearance_mode(saved_mode)
        ctk.set_default_color_theme("blue")

        self.title("Private School Management System - SGS")
        self.geometry("1400x850")
        self.minsize(1100, 700)

        # Set window/taskbar icon (Windows .ico; ignored gracefully on
        # platforms where iconbitmap with .ico is unsupported)
        icon_path = os.path.join(BASE_DIR, "assets", "icons", "app_icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        # Configure grid: sidebar | content
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ---- Sidebar ----
        self.sidebar = Sidebar(self, NAV_ITEMS, on_navigate=self.show_page)
        self.sidebar.grid(row=0, column=0, sticky="nswe")

        # ---- Content container ----
        self.content_frame = ctk.CTkFrame(self, fg_color=("#F8FAFC", "#0F172A"), corner_radius=0)
        self.content_frame.grid(row=0, column=1, sticky="nswe")
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        # Page cache
        self.pages = {}
        self.current_page_key = None

        # Show default page
        self.show_page("dashboard")

    # ------------------------------------------------------------
    def show_page(self, key: str):
        """Switch the visible page in the content area."""
        # Hide current page
        if self.current_page_key and self.current_page_key in self.pages:
            self.pages[self.current_page_key].grid_remove()

        # Create page if not cached
        if key not in self.pages:
            self.pages[key] = self._create_page(key)

        page = self.pages[key]
        page.grid(row=0, column=0, sticky="nswe")

        # Refresh page data if it supports it
        if hasattr(page, "refresh"):
            page.refresh()

        self.current_page_key = key
        self.sidebar.set_active(key)

    def _create_page(self, key: str):
        if key == "dashboard":
            return DashboardView(self.content_frame)
        elif key == "gestion_eleves":
            return GestionElevesView(self.content_frame)
        elif key == "nouvelle_inscription":
            return NouvelleInscriptionView(self.content_frame)
        elif key == "reinscription":
            return ReinscriptionView(self.content_frame)
        elif key == "gestion_paiements":
            return GestionPaiementsView(self.content_frame)
        elif key == "settings":
            return SettingsView(self.content_frame, on_appearance_change=self._on_appearance_change)
        else:
            raise ValueError(f"Unknown page key: {key}")

    def _on_appearance_change(self, mode: str):
        """Called when the user changes appearance mode from settings."""
        # Force refresh of cached pages that contain charts/tables
        for key in ("dashboard",):
            if key in self.pages:
                self.pages[key].refresh()


if __name__ == "__main__":
    app = SchoolManagementApp()
    app.mainloop()
