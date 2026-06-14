"""
==================================================================
 CHART COMPONENTS
==================================================================
Wrappers around matplotlib figures embedded into CustomTkinter
frames via FigureCanvasTkAgg. Provides bar, line, donut and pie
chart helpers used on the dashboard.
==================================================================
"""

import customtkinter as ctk
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from utils.theme import COLORS, CARD_CORNER_RADIUS

# Consistent color cycle for charts
CHART_COLORS = [
    COLORS["primary"], COLORS["success"], COLORS["warning"],
    COLORS["secondary"], "#A855F7", "#EC4899", "#14B8A6", "#F97316",
]


class ChartCard(ctk.CTkFrame):
    """
    A card containing a title and a matplotlib chart.
    Call `update_chart()` to redraw with new data.
    """

    def __init__(self, master, title: str, chart_type: str = "bar", **kwargs):
        super().__init__(
            master, corner_radius=CARD_CORNER_RADIUS,
            fg_color=("white", COLORS["card_dark"]),
            border_width=1, border_color=("#E2E8F0", COLORS["border_dark"]),
            **kwargs
        )

        self.chart_type = chart_type
        self.title_text = title

        self.title_label = ctk.CTkLabel(
            self, text=title, font=("Segoe UI", 14, "bold"), anchor="w"
        )
        self.title_label.pack(fill="x", padx=18, pady=(15, 5))

        self.canvas_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.canvas_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.figure = None
        self.canvas = None

    # ------------------------------------------------------------
    def _clear_canvas(self):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            plt.close(self.figure)
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()

    def _render_chart(self, fig):
        self._clear_canvas()
        self.figure = fig
        self.canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    # ------------------------------------------------------------
    def update_bar_chart(self, labels: list, values: list, ylabel: str = "Élèves"):
        fig, ax = plt.subplots(figsize=(4.2, 2.8), dpi=90)
        fig.patch.set_facecolor("#FFFFFF")
        ax.set_facecolor("#FFFFFF")

        if not labels:
            labels, values = ["Aucune donnée"], [0]

        bars = ax.bar(labels, values, color=COLORS["primary"], width=0.55,
                       edgecolor="none")
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, height + 0.05,
                    f"{int(height)}", ha="center", va="bottom", fontsize=8)

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#E2E8F0")
        ax.spines["bottom"].set_color("#E2E8F0")
        ax.tick_params(axis="x", labelsize=8, rotation=0)
        ax.tick_params(axis="y", labelsize=8)
        ax.set_ylabel(ylabel, fontsize=9)
        fig.tight_layout()

        self._render_chart(fig)

    def update_line_chart(self, labels: list, values: list, ylabel: str = "Élèves",
                           color: str = None):
        color = color or COLORS["primary"]
        fig, ax = plt.subplots(figsize=(4.2, 2.8), dpi=90)
        fig.patch.set_facecolor("#FFFFFF")
        ax.set_facecolor("#FFFFFF")

        if not labels:
            labels, values = ["Aucune donnée"], [0]

        ax.plot(labels, values, color=color, marker="o", linewidth=2.2,
                markersize=5)
        ax.fill_between(range(len(labels)), values, color=color, alpha=0.08)

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#E2E8F0")
        ax.spines["bottom"].set_color("#E2E8F0")
        ax.tick_params(axis="x", labelsize=7, rotation=30)
        ax.tick_params(axis="y", labelsize=8)
        ax.set_ylabel(ylabel, fontsize=9)
        fig.tight_layout()

        self._render_chart(fig)

    def update_donut_chart(self, labels: list, values: list):
        fig, ax = plt.subplots(figsize=(4.2, 2.8), dpi=90)
        fig.patch.set_facecolor("#FFFFFF")

        total = sum(values)

        if total == 0:
            plot_values = [1]
            plot_labels = labels if labels else ["Aucune donnée"]
            colors = ["#E2E8F0"]
        else:
            plot_values = values
            plot_labels = labels
            colors = CHART_COLORS[:len(values)]

        wedges, _ = ax.pie(
            plot_values, colors=colors, startangle=90,
            wedgeprops=dict(width=0.40, edgecolor="white")
        )

        ax.text(0, 0, f"{total}", ha="center", va="center",
                fontsize=18, fontweight="bold")
        labels = plot_labels

        ax.legend(
            wedges, labels, loc="center left",
            bbox_to_anchor=(0.95, 0.5), fontsize=8, frameon=False
        )
        fig.subplots_adjust(left=0.05, right=0.72)

        self._render_chart(fig)

    def update_stacked_bar_chart(self, labels: list, series: dict, ylabel: str = "Montant (DH)"):
        """
        series: dict {series_name: [values...]} - each list aligned with labels.
        Renders a stacked bar chart with a legend.
        """
        fig, ax = plt.subplots(figsize=(4.2, 2.8), dpi=90)
        fig.patch.set_facecolor("#FFFFFF")
        ax.set_facecolor("#FFFFFF")

        if not labels or not series or all(sum(v) == 0 for v in series.values()):
            labels = ["Aucune donnée"]
            series = {"Aucune donnée": [0]}

        bottom = [0] * len(labels)
        colors_cycle = CHART_COLORS

        for i, (name, values) in enumerate(series.items()):
            ax.bar(labels, values, bottom=bottom, label=name,
                   color=colors_cycle[i % len(colors_cycle)], width=0.55,
                   edgecolor="none")
            bottom = [b + v for b, v in zip(bottom, values)]

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#E2E8F0")
        ax.spines["bottom"].set_color("#E2E8F0")
        ax.tick_params(axis="x", labelsize=7, rotation=30)
        ax.tick_params(axis="y", labelsize=8)
        ax.set_ylabel(ylabel, fontsize=9)
        ax.legend(fontsize=7, frameon=False, loc="upper left")
        fig.tight_layout()

        self._render_chart(fig)

    def update_pie_chart(self, labels: list, values: list):
        fig, ax = plt.subplots(figsize=(4.2, 2.8), dpi=90)
        fig.patch.set_facecolor("#FFFFFF")

        if sum(values) == 0 or not values:
            values = [1]
            labels = ["Aucune donnée"]
            colors = ["#E2E8F0"]
        else:
            colors = CHART_COLORS[:len(values)]

        ax.pie(
            values, labels=labels, colors=colors, autopct="%1.0f%%",
            startangle=90, textprops={"fontsize": 8},
            wedgeprops=dict(edgecolor="white")
        )
        ax.set_aspect("equal")
        fig.tight_layout()

        self._render_chart(fig)
