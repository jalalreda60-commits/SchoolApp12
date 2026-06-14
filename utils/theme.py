"""
==================================================================
 THEME / DESIGN TOKENS
==================================================================
Centralized color palette, fonts and styling constants used
throughout the application to keep a consistent, modern
ERP-style look (light & dark mode).
==================================================================
"""

# ------------------------------------------------------------
# COLOR PALETTE
# ------------------------------------------------------------
COLORS = {
    "primary": "#2563EB",
    "primary_hover": "#1D4ED8",
    "secondary": "#3B82F6",
    "success": "#22C55E",
    "success_hover": "#16A34A",
    "warning": "#F59E0B",
    "warning_hover": "#D97706",
    "danger": "#EF4444",
    "danger_hover": "#DC2626",
    "background_light": "#F8FAFC",
    "background_dark": "#0F172A",
    "card_light": "#FFFFFF",
    "card_dark": "#1E293B",
    "sidebar_light": "#1E293B",
    "sidebar_dark": "#0B1220",
    "text_light": "#1E293B",
    "text_dark": "#F1F5F9",
    "muted_light": "#64748B",
    "muted_dark": "#94A3B8",
    "border_light": "#E2E8F0",
    "border_dark": "#334155",
}

# ------------------------------------------------------------
# FONTS
# ------------------------------------------------------------
FONT_FAMILY = "Segoe UI"

FONTS = {
    "h1": (FONT_FAMILY, 26, "bold"),
    "h2": (FONT_FAMILY, 20, "bold"),
    "h3": (FONT_FAMILY, 16, "bold"),
    "body": (FONT_FAMILY, 13),
    "body_bold": (FONT_FAMILY, 13, "bold"),
    "small": (FONT_FAMILY, 11),
    "sidebar": (FONT_FAMILY, 14),
    "kpi_value": (FONT_FAMILY, 28, "bold"),
    "kpi_label": (FONT_FAMILY, 12),
}

# ------------------------------------------------------------
# LAYOUT
# ------------------------------------------------------------
SIDEBAR_WIDTH_EXPANDED = 220
SIDEBAR_WIDTH_COLLAPSED = 70
CARD_CORNER_RADIUS = 14
BUTTON_CORNER_RADIUS = 8

# ------------------------------------------------------------
# CLASS LIST (used for dropdowns)
# ------------------------------------------------------------
CLASS_LEVELS = [
    "TPS", "PS", "MS", "GS",
    "CP", "CE1", "CE2", "CM1", "CM2",
    "6eme", "5eme", "4eme", "3eme",
    "2nde", "1ere", "Terminale",
]

STATUT_OPTIONS = ["Actif", "Inactif"]
TRANSPORT_OPTIONS = ["Yes", "No"]

# ------------------------------------------------------------
# PAYMENT MODULE CONSTANTS
# ------------------------------------------------------------
MONTHS_ORDER = [
    "Septembre", "Octobre", "Novembre", "Décembre",
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
]

PAYMENT_TYPES = ["Inscription", "Mensualité", "Transport"]

# Internal payment status values stored in DB
STATUS_PAID = "Paye"
STATUS_UNPAID = "Impaye"
STATUS_NAN = "NAN"

PAYMENT_STATUS_COLORS = {
    STATUS_PAID: COLORS["success"],
    STATUS_UNPAID: COLORS["danger"],
    STATUS_NAN: COLORS["muted_light"],
}

PAYMENT_STATUS_LABELS = {
    STATUS_PAID: "Payé",
    STATUS_UNPAID: "Impayé",
    STATUS_NAN: "Non inscrit",
}
