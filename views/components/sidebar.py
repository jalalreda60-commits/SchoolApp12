"""
==================================================================
 SIDEBAR COMPONENT
==================================================================
Collapsible left navigation sidebar with icons, active page
highlighting and smooth expand/collapse animation.
==================================================================
"""

import os
import customtkinter as ctk
from PIL import Image
from utils.theme import COLORS, FONTS, SIDEBAR_WIDTH_EXPANDED, SIDEBAR_WIDTH_COLLAPSED
from database.db_manager import BASE_DIR

EMBLEM_PATH = os.path.join(BASE_DIR, "assets", "icons", "school_emblem.png")


class Sidebar(ctk.CTkFrame):
    """
    Left navigation sidebar.

    Parameters
    ----------
    master : widget
        Parent widget.
    nav_items : list[tuple]
        List of (key, label, icon_char) tuples.
    on_navigate : callable
        Callback invoked with the page key when an item is clicked.
    """

    def __init__(self, master, nav_items, on_navigate, **kwargs):
        super().__init__(master, corner_radius=0, **kwargs)

        self.nav_items = nav_items
        self.on_navigate = on_navigate
        self.expanded = True
        self.current_width = SIDEBAR_WIDTH_EXPANDED
        self.active_key = nav_items[0][0] if nav_items else None

        self.configure(fg_color=COLORS["sidebar_light"], width=SIDEBAR_WIDTH_EXPANDED)
        self.grid_propagate(False)
        self.pack_propagate(False)

        self._build_ui()

    # ------------------------------------------------------------
    def _build_ui(self):
        # ---- Header (Logo + toggle button) ----
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent", height=70)
        self.header_frame.pack(fill="x", pady=(15, 10), padx=10)

        # Load logo emblem if available
        self.logo_image = None
        if os.path.exists(EMBLEM_PATH):
            try:
                pil_img = Image.open(EMBLEM_PATH)
                ratio = pil_img.width / pil_img.height
                target_h = 36
                target_w = int(target_h * ratio)
                self.logo_image = ctk.CTkImage(
                    light_image=pil_img, dark_image=pil_img,
                    size=(target_w, target_h)
                )
            except Exception:
                self.logo_image = None

        if self.logo_image:
            self.logo_label = ctk.CTkLabel(
                self.header_frame, image=self.logo_image, text="  Le Schéma",
                font=FONTS["h3"], text_color="white", anchor="w", compound="left"
            )
        else:
            self.logo_label = ctk.CTkLabel(
                self.header_frame, text="🏫  Le Schéma",
                font=FONTS["h3"], text_color="white", anchor="w"
            )
        self.logo_label.pack(side="left", fill="x", expand=True)

        self.toggle_btn = ctk.CTkButton(
            self.header_frame, text="☰", width=36, height=36,
            fg_color="transparent", hover_color=COLORS["sidebar_dark"],
            font=FONTS["h3"], command=self.toggle
        )
        self.toggle_btn.pack(side="right")

        # ---- Separator ----
        sep = ctk.CTkFrame(self, height=1, fg_color=COLORS["border_dark"])
        sep.pack(fill="x", padx=10, pady=(0, 10))

        # ---- Navigation buttons ----
        self.nav_buttons = {}
        for key, label, icon in self.nav_items:
            btn = ctk.CTkButton(
                self, text=f"{icon}   {label}",
                anchor="w", font=FONTS["sidebar"],
                fg_color="transparent",
                hover_color=COLORS["primary"],
                text_color="white",
                corner_radius=8,
                height=44,
                command=lambda k=key: self._handle_click(k)
            )
            btn.pack(fill="x", padx=12, pady=4)
            self.nav_buttons[key] = (btn, label, icon)

        # ---- Spacer ----
        spacer = ctk.CTkFrame(self, fg_color="transparent")
        spacer.pack(fill="both", expand=True)

        # ---- Footer ----
        self.footer_label = ctk.CTkLabel(
            self, text="v1.0 · SGS School Manager",
            font=FONTS["small"], text_color=COLORS["muted_dark"]
        )
        self.footer_label.pack(pady=10)

        self._update_active_highlight()

    # ------------------------------------------------------------
    def _handle_click(self, key):
        self.set_active(key)
        self.on_navigate(key)

    def set_active(self, key):
        self.active_key = key
        self._update_active_highlight()

    def _update_active_highlight(self):
        for key, (btn, label, icon) in self.nav_buttons.items():
            if key == self.active_key:
                btn.configure(fg_color=COLORS["primary"])
            else:
                btn.configure(fg_color="transparent")

    # ------------------------------------------------------------
    def toggle(self):
        """Expand or collapse the sidebar with a smooth animation."""
        target_width = SIDEBAR_WIDTH_COLLAPSED if self.expanded else SIDEBAR_WIDTH_EXPANDED
        self.expanded = not self.expanded
        self._animate_width(self.current_width, target_width)
        self._update_labels()

    def _animate_width(self, start, end, step=0):
        steps = 8
        diff = (end - start) / steps

        def animate(i=0, current=start):
            if i >= steps:
                self.current_width = end
                self.configure(width=end)
                return
            current += diff
            self.configure(width=int(current))
            self.after(12, lambda: animate(i + 1, current))

        animate()

    def _update_labels(self):
        if self.expanded:
            if self.logo_image:
                self.logo_label.configure(text="  Le Schéma")
            else:
                self.logo_label.configure(text="🏫  Le Schéma")
            for key, (btn, label, icon) in self.nav_buttons.items():
                btn.configure(text=f"{icon}   {label}", anchor="w")
            self.footer_label.configure(text="v1.0 · SGS School Manager")
        else:
            if self.logo_image:
                self.logo_label.configure(text="")
            else:
                self.logo_label.configure(text="🏫")
            for key, (btn, label, icon) in self.nav_buttons.items():
                btn.configure(text=icon, anchor="center")
            self.footer_label.configure(text="")
