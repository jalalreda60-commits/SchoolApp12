"""
==================================================================
 KPI CARD COMPONENT
==================================================================
Reusable rounded card used on the dashboard to display a single
KPI value with icon, label and accent color.
==================================================================
"""

import customtkinter as ctk
from utils.theme import COLORS, FONTS, CARD_CORNER_RADIUS


class KPICard(ctk.CTkFrame):
    """A single KPI card: icon + big value + label."""

    def __init__(self, master, icon: str, value: str, label: str,
                 accent_color: str = None, **kwargs):
        accent_color = accent_color or COLORS["primary"]

        super().__init__(
            master, corner_radius=CARD_CORNER_RADIUS,
            fg_color=("white", COLORS["card_dark"]),
            border_width=1, border_color=("#E2E8F0", COLORS["border_dark"]),
            **kwargs
        )

        self.grid_columnconfigure(1, weight=1)

        # Icon circle
        icon_frame = ctk.CTkFrame(
            self, width=52, height=52, corner_radius=26,
            fg_color=accent_color
        )
        icon_frame.grid(row=0, column=0, rowspan=2, padx=(18, 12), pady=18, sticky="n")
        icon_frame.grid_propagate(False)

        icon_label = ctk.CTkLabel(
            icon_frame, text=icon, font=("Segoe UI", 22), text_color="white"
        )
        icon_label.place(relx=0.5, rely=0.5, anchor="center")

        # Value
        self.value_label = ctk.CTkLabel(
            self, text=value, font=FONTS["kpi_value"],
            anchor="w"
        )
        self.value_label.grid(row=0, column=1, sticky="sw", padx=(0, 18), pady=(18, 0))

        # Label
        self.text_label = ctk.CTkLabel(
            self, text=label, font=FONTS["kpi_label"],
            text_color=COLORS["muted_light"], anchor="w"
        )
        self.text_label.grid(row=1, column=1, sticky="nw", padx=(0, 18), pady=(0, 18))

        # Hover effect
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        for child in self.winfo_children():
            child.bind("<Enter>", self._on_enter)
            child.bind("<Leave>", self._on_leave)

    def _on_enter(self, event=None):
        self.configure(border_color=COLORS["primary"])

    def _on_leave(self, event=None):
        self.configure(border_color=("#E2E8F0", COLORS["border_dark"]))

    def update_value(self, value: str):
        self.value_label.configure(text=value)
