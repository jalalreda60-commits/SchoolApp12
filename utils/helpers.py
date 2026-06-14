"""
==================================================================
 HELPER FUNCTIONS
==================================================================
Small reusable utility functions: notifications, validation
helpers, formatting, etc.
==================================================================
"""

import customtkinter as ctk
from utils.theme import COLORS, FONTS


def format_currency(value) -> str:
    """Format a numeric value as a currency string (e.g. 1 200.00 DH)."""
    try:
        v = float(value)
    except (ValueError, TypeError):
        v = 0.0
    return f"{v:,.2f} DH".replace(",", " ")


def safe_str(value) -> str:
    """Return a clean string representation, '' for None/NaN."""
    if value is None:
        return ""
    return str(value)


def show_toast(parent, message: str, kind: str = "success", duration: int = 2500):
    """
    Display a small temporary notification (toast) in the bottom
    right corner of the given parent window.

    kind: "success" | "warning" | "error" | "info"
    """
    color_map = {
        "success": COLORS["success"],
        "warning": COLORS["warning"],
        "error": COLORS["danger"],
        "info": COLORS["primary"],
    }
    bg_color = color_map.get(kind, COLORS["primary"])

    toast = ctk.CTkFrame(
        parent, fg_color=bg_color, corner_radius=10
    )
    label = ctk.CTkLabel(
        toast, text=message, text_color="white",
        font=FONTS["body_bold"], padx=20, pady=12
    )
    label.pack()

    # Position bottom-right
    toast.place(relx=0.99, rely=0.97, anchor="se")
    toast.lift()

    # Auto-destroy after duration
    toast.after(duration, toast.destroy)
    return toast


def confirm_dialog(parent, title: str, message: str) -> bool:
    """
    Show a simple Yes/No confirmation dialog.
    Returns True if the user confirmed, False otherwise.
    """
    result = {"confirmed": False}

    dialog = ctk.CTkToplevel(parent)
    dialog.title(title)
    dialog.geometry("420x180")
    dialog.resizable(False, False)
    dialog.grab_set()
    dialog.transient(parent)

    # Center on parent
    dialog.update_idletasks()
    x = parent.winfo_rootx() + (parent.winfo_width() // 2) - 210
    y = parent.winfo_rooty() + (parent.winfo_height() // 2) - 90
    dialog.geometry(f"+{x}+{y}")

    label = ctk.CTkLabel(
        dialog, text=message, font=FONTS["body"],
        wraplength=380, justify="center"
    )
    label.pack(pady=(30, 20), padx=20)

    btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
    btn_frame.pack(pady=10)

    def on_yes():
        result["confirmed"] = True
        dialog.destroy()

    def on_no():
        result["confirmed"] = False
        dialog.destroy()

    yes_btn = ctk.CTkButton(
        btn_frame, text="Confirmer", fg_color=COLORS["danger"],
        hover_color=COLORS["danger_hover"], width=120,
        command=on_yes
    )
    yes_btn.grid(row=0, column=0, padx=10)

    no_btn = ctk.CTkButton(
        btn_frame, text="Annuler", fg_color=COLORS["muted_light"],
        hover_color=COLORS["muted_dark"], width=120,
        command=on_no
    )
    no_btn.grid(row=0, column=1, padx=10)

    dialog.wait_window()
    return result["confirmed"]


def validate_required(value) -> bool:
    """Return True if value is non-empty (after stripping)."""
    if value is None:
        return False
    return str(value).strip() != ""


def validate_number(value) -> bool:
    """Return True if value can be converted to float."""
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False
