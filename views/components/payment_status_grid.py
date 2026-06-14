"""
==================================================================
 PAYMENT STATUS GRID COMPONENT
==================================================================
Displays the Septembre→Juin monthly status grid for a student
with colored chips:
  Green = Payé
  Red   = Impayé
  Gray  = NAN (not enrolled)

Clicking a chip can optionally trigger a callback (used to
pre-select the month in the payment form).
==================================================================
"""

import customtkinter as ctk
from utils.theme import (
    COLORS, FONTS, MONTHS_ORDER, PAYMENT_STATUS_COLORS, PAYMENT_STATUS_LABELS,
    STATUS_PAID, STATUS_UNPAID, STATUS_NAN, CARD_CORNER_RADIUS
)


MONTH_SHORT = {
    "Septembre": "Sep", "Octobre": "Oct", "Novembre": "Nov", "Décembre": "Déc",
    "Janvier": "Jan", "Février": "Fév", "Mars": "Mar", "Avril": "Avr",
    "Mai": "Mai", "Juin": "Jun",
}


class PaymentStatusGrid(ctk.CTkFrame):
    """Horizontal row of 10 month chips showing payment status."""

    def __init__(self, master, status_map: dict = None, on_month_click=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_month_click = on_month_click
        self.chips = {}

        for i, month in enumerate(MONTHS_ORDER):
            self.grid_columnconfigure(i, weight=1, uniform="month")

        for i, month in enumerate(MONTHS_ORDER):
            chip = self._make_chip(month)
            chip.grid(row=0, column=i, padx=3, pady=3, sticky="ew")
            self.chips[month] = chip

        if status_map:
            self.update_status(status_map)

    def _make_chip(self, month):
        chip = ctk.CTkFrame(
            self, corner_radius=8, fg_color=PAYMENT_STATUS_COLORS[STATUS_UNPAID],
            height=54
        )
        chip.grid_propagate(False)
        chip.configure(height=54)

        month_label = ctk.CTkLabel(
            chip, text=MONTH_SHORT.get(month, month), font=("Segoe UI", 11, "bold"),
            text_color="white"
        )
        month_label.pack(pady=(8, 0))

        status_label = ctk.CTkLabel(
            chip, text="Impayé", font=("Segoe UI", 9), text_color="white"
        )
        status_label.pack()

        chip.status_label = status_label
        chip.month = month

        if self.on_month_click:
            for widget in (chip, month_label, status_label):
                widget.bind("<Button-1>", lambda e, m=month: self.on_month_click(m))
                widget.configure(cursor="hand2") if hasattr(widget, "configure") else None

        return chip

    def update_status(self, status_map: dict):
        """status_map: {month_name: 'Paye'|'Impaye'|'NAN'}"""
        for month, chip in self.chips.items():
            status = status_map.get(month, STATUS_UNPAID)
            color = PAYMENT_STATUS_COLORS.get(status, PAYMENT_STATUS_COLORS[STATUS_UNPAID])
            label = PAYMENT_STATUS_LABELS.get(status, "Impayé")
            chip.configure(fg_color=color)
            chip.status_label.configure(text=label)
