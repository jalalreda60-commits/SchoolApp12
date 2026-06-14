"""
==================================================================
 DASHBOARD VIEW
==================================================================
Main ERP-style dashboard with filters (school year, class, month),
KPI cards and 5 dynamic charts:
  1. Students per class (Bar)
  2. Monthly registrations (Line)
  3. Re-inscription progress (Donut)
  4. Student departures by month (Line)
  5. Transport users by class (Pie)
==================================================================
"""

import customtkinter as ctk
from datetime import datetime
from models.student import Student
from models.payment import Payment
from controllers.student_controller import StudentController
from utils.theme import COLORS, FONTS, STATUS_PAID, STATUS_UNPAID, STATUS_NAN, PAYMENT_STATUS_LABELS
from views.components.kpi_card import KPICard
from views.components.charts import ChartCard


MONTH_NAMES_FR = {
    "01": "Jan", "02": "Fév", "03": "Mar", "04": "Avr",
    "05": "Mai", "06": "Jun", "07": "Jul", "08": "Aoû",
    "09": "Sep", "10": "Oct", "11": "Nov", "12": "Déc",
}


def format_month_label(yyyymm: str) -> str:
    try:
        year, month = yyyymm.split("-")
        return f"{MONTH_NAMES_FR.get(month, month)} {year[2:]}"
    except Exception:
        return yyyymm


class DashboardView(ctk.CTkFrame):
    """Dashboard page."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.current_year = StudentController.get_current_year()
        self.next_year = StudentController.get_next_year()

        self.selected_year = self.current_year
        self.selected_class = "Toutes"
        self.selected_month = "Tous"

        self._build_ui()
        self.refresh()

    # ------------------------------------------------------------
    def _build_ui(self):
        # ---- Header with title and filters ----
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(20, 10))

        title = ctk.CTkLabel(
            header, text="📊 Tableau de Bord", font=FONTS["h1"], anchor="w"
        )
        title.pack(side="left")

        # Filters frame
        filters = ctk.CTkFrame(header, fg_color="transparent")
        filters.pack(side="right")

        # Year filter
        ctk.CTkLabel(filters, text="Année scolaire:", font=FONTS["body"]).pack(side="left", padx=(0, 6))
        years = Student.get_distinct_years()
        if self.current_year not in years:
            years.append(self.current_year)
        if self.next_year not in years:
            years.append(self.next_year)
        years = sorted(set(years), reverse=True)

        self.year_var = ctk.StringVar(value=self.selected_year)
        self.year_menu = ctk.CTkOptionMenu(
            filters, values=years, variable=self.year_var,
            width=120, fg_color=COLORS["primary"],
            button_color=COLORS["primary_hover"],
            command=self._on_filter_change
        )
        self.year_menu.pack(side="left", padx=(0, 12))

        # Class filter
        ctk.CTkLabel(filters, text="Classe:", font=FONTS["body"]).pack(side="left", padx=(0, 6))
        self.class_var = ctk.StringVar(value="Toutes")
        self.class_menu = ctk.CTkOptionMenu(
            filters, values=["Toutes"], variable=self.class_var,
            width=110, fg_color=COLORS["primary"],
            button_color=COLORS["primary_hover"],
            command=self._on_filter_change
        )
        self.class_menu.pack(side="left", padx=(0, 12))

        # Month filter
        ctk.CTkLabel(filters, text="Mois:", font=FONTS["body"]).pack(side="left", padx=(0, 6))
        self.month_var = ctk.StringVar(value="Tous")
        self.month_menu = ctk.CTkOptionMenu(
            filters, values=["Tous"], variable=self.month_var,
            width=100, fg_color=COLORS["primary"],
            button_color=COLORS["primary_hover"],
            command=self._on_filter_change
        )
        self.month_menu.pack(side="left")

        # ---- Scrollable body ----
        self.body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=0, pady=0)

        # ---- KPI Cards row 1 (enrollment) ----
        kpi_frame = ctk.CTkFrame(self.body, fg_color="transparent")
        kpi_frame.pack(fill="x", padx=25, pady=10)
        for i in range(4):
            kpi_frame.grid_columnconfigure(i, weight=1, uniform="kpi")

        self.kpi_enrolled = KPICard(
            kpi_frame, icon="🎓", value="0",
            label=f"Inscrits {self.current_year}",
            accent_color=COLORS["primary"]
        )
        self.kpi_enrolled.grid(row=0, column=0, padx=8, pady=5, sticky="ew")

        self.kpi_pre_registered = KPICard(
            kpi_frame, icon="📝", value="0",
            label=f"Pré-inscrits {self.next_year}",
            accent_color=COLORS["secondary"]
        )
        self.kpi_pre_registered.grid(row=0, column=1, padx=8, pady=5, sticky="ew")

        self.kpi_new_month = KPICard(
            kpi_frame, icon="✨", value="0",
            label="Nouvelles inscriptions (mois)",
            accent_color=COLORS["success"]
        )
        self.kpi_new_month.grid(row=0, column=2, padx=8, pady=5, sticky="ew")

        self.kpi_transport = KPICard(
            kpi_frame, icon="🚌", value="0",
            label="Élèves utilisant le transport",
            accent_color=COLORS["warning"]
        )
        self.kpi_transport.grid(row=0, column=3, padx=8, pady=5, sticky="ew")

        # ---- KPI Cards row 2 (financial) ----
        kpi_frame2 = ctk.CTkFrame(self.body, fg_color="transparent")
        kpi_frame2.pack(fill="x", padx=25, pady=(0, 10))
        for i in range(2):
            kpi_frame2.grid_columnconfigure(i, weight=1, uniform="kpi2")

        self.kpi_inscription_revenue = KPICard(
            kpi_frame2, icon="💼", value="0 DH",
            label=f"Revenus d'Inscription {self.current_year}",
            accent_color=COLORS["success"]
        )
        self.kpi_inscription_revenue.grid(row=0, column=0, padx=8, pady=5, sticky="ew")

        self.kpi_monthly_income = KPICard(
            kpi_frame2, icon="💵", value="0 DH",
            label="Revenus du mois sélectionné",
            accent_color=COLORS["primary"]
        )
        self.kpi_monthly_income.grid(row=0, column=1, padx=8, pady=5, sticky="ew")

        # ---- Charts grid: enrollment (5) ----
        charts_frame = ctk.CTkFrame(self.body, fg_color="transparent")
        charts_frame.pack(fill="x", expand=False, padx=25, pady=(10, 10))
        charts_frame.grid_columnconfigure((0, 1, 2), weight=1, uniform="chart")
        charts_frame.grid_rowconfigure((0, 1), weight=1, uniform="chartrow", minsize=280)

        self.chart_students_per_class = ChartCard(
            charts_frame, title="1. Élèves par classe", chart_type="bar"
        )
        self.chart_students_per_class.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")

        self.chart_monthly_registrations = ChartCard(
            charts_frame, title="2. Inscriptions mensuelles", chart_type="line"
        )
        self.chart_monthly_registrations.grid(row=0, column=1, padx=8, pady=8, sticky="nsew")

        self.chart_reinscription = ChartCard(
            charts_frame, title="3. Progression des réinscriptions", chart_type="donut"
        )
        self.chart_reinscription.grid(row=0, column=2, padx=8, pady=8, sticky="nsew")

        self.chart_departures = ChartCard(
            charts_frame, title="4. Départs par mois", chart_type="line"
        )
        self.chart_departures.grid(row=1, column=0, padx=8, pady=8, sticky="nsew")

        self.chart_transport_class = ChartCard(
            charts_frame, title="5. Transport par classe", chart_type="pie"
        )
        self.chart_transport_class.grid(row=1, column=1, columnspan=2, padx=8, pady=8, sticky="nsew")

        # ---- Charts grid: financial (3) ----
        finance_frame = ctk.CTkFrame(self.body, fg_color="transparent")
        finance_frame.pack(fill="x", expand=False, padx=25, pady=(0, 20))
        finance_frame.grid_columnconfigure((0, 1, 2), weight=1, uniform="financechart")
        finance_frame.grid_rowconfigure(0, weight=1, minsize=280)

        self.chart_income_evolution = ChartCard(
            finance_frame, title="6. Évolution des revenus mensuels", chart_type="bar"
        )
        self.chart_income_evolution.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")

        self.chart_payment_status = ChartCard(
            finance_frame, title="7. Répartition des statuts de paiement", chart_type="donut"
        )
        self.chart_payment_status.grid(row=0, column=1, padx=8, pady=8, sticky="nsew")

        self.chart_income_by_class = ChartCard(
            finance_frame, title="8. Revenus par classe", chart_type="bar"
        )
        self.chart_income_by_class.grid(row=0, column=2, padx=8, pady=8, sticky="nsew")

    # ------------------------------------------------------------
    def _on_filter_change(self, _value=None):
        self.selected_year = self.year_var.get()
        self.selected_class = self.class_var.get()
        self.selected_month = self.month_var.get()
        self.refresh(update_year_settings=False)

    # ------------------------------------------------------------
    def refresh(self, update_year_settings: bool = True):
        """Reload all data from the database and redraw charts/KPIs."""
        if update_year_settings:
            self.current_year = StudentController.get_current_year()
            self.next_year = StudentController.get_next_year()
            self.selected_year = self.year_var.get() if hasattr(self, "year_var") else self.current_year

        # Update class filter options dynamically
        classes = Student.get_distinct_classes(self.selected_year)
        class_options = ["Toutes"] + classes
        current_class_selection = self.class_var.get()
        self.class_menu.configure(values=class_options)
        if current_class_selection not in class_options:
            self.class_var.set("Toutes")
            self.selected_class = "Toutes"

        # Update month filter options dynamically (registration months + payment months)
        reg_months = set(m for m, _ in Student.get_monthly_registrations(self.selected_year))
        pay_months = set(Payment.get_distinct_payment_months(self.selected_year))
        months = sorted(reg_months | pay_months)
        month_options = ["Tous"] + [format_month_label(m) for m in months]
        self._month_map = {format_month_label(m): m for m in months}
        current_month_selection = self.month_var.get()
        self.month_menu.configure(values=month_options)
        if current_month_selection not in month_options:
            self.month_var.set("Tous")
            self.selected_month = "Tous"

        month_filter_value = self._month_map.get(self.selected_month) if self.selected_month != "Tous" else None

        # ---- KPI data ----
        kpi_data = Student.get_kpi_data(self.selected_year, self.next_year, month_filter_value)
        self.kpi_enrolled.update_value(str(kpi_data["enrolled_current"]))
        self.kpi_pre_registered.update_value(str(kpi_data["pre_registered_next"]))
        self.kpi_new_month.update_value(str(kpi_data["new_this_month"]))
        self.kpi_transport.update_value(str(kpi_data["transport_users"]))

        self.kpi_enrolled.text_label.configure(text=f"Inscrits {self.selected_year}")

        # ---- Financial KPIs ----
        inscription_revenue = Payment.get_total_inscription_revenue(
            self.selected_year, self.selected_class
        )
        self.kpi_inscription_revenue.update_value(f"{inscription_revenue:,.0f} DH".replace(",", " "))
        self.kpi_inscription_revenue.text_label.configure(
            text=f"Revenus d'Inscription {self.selected_year}"
        )

        # Use the selected month if set, otherwise the current calendar month
        if month_filter_value:
            income_month_key = month_filter_value
            income_label_suffix = format_month_label(month_filter_value)
        else:
            income_month_key = datetime.now().strftime("%Y-%m")
            income_label_suffix = "ce mois"

        monthly_income = Payment.get_monthly_income(
            self.selected_year, income_month_key, self.selected_class
        )
        self.kpi_monthly_income.update_value(f"{monthly_income:,.0f} DH".replace(",", " "))
        self.kpi_monthly_income.text_label.configure(
            text=f"Revenus encaissés — {income_label_suffix}"
        )

        # ---- Chart 1: Students per class ----
        per_class = Student.get_students_per_class(self.selected_year)
        if self.selected_class != "Toutes":
            per_class = [(c, n) for c, n in per_class if c == self.selected_class]
        labels = [c for c, _ in per_class]
        values = [n for _, n in per_class]
        self.chart_students_per_class.update_bar_chart(labels, values, ylabel="Élèves")

        # ---- Chart 2: Monthly registrations ----
        monthly = Student.get_monthly_registrations(self.selected_year)
        labels = [format_month_label(m) for m, _ in monthly]
        values = [n for _, n in monthly]
        self.chart_monthly_registrations.update_line_chart(labels, values, ylabel="Inscriptions",
                                                             color=COLORS["primary"])

        # ---- Chart 3: Re-inscription progress (donut) ----
        reinscribed, remaining = Student.get_reinscription_progress(self.selected_year, self.next_year)
        self.chart_reinscription.update_donut_chart(
            ["Réinscrits", "En attente"], [reinscribed, remaining]
        )

        # ---- Chart 4: Departures by month ----
        departures = Student.get_departures_by_month(self.selected_year)
        labels = [format_month_label(m) for m, _ in departures]
        values = [n for _, n in departures]
        self.chart_departures.update_line_chart(labels, values, ylabel="Départs",
                                                  color=COLORS["danger"])

        # ---- Chart 5: Transport by class (pie) ----
        transport_class = Student.get_transport_by_class(self.selected_year)
        if self.selected_class != "Toutes":
            transport_class = [(c, n) for c, n in transport_class if c == self.selected_class]
        labels = [c for c, _ in transport_class]
        values = [n for _, n in transport_class]
        self.chart_transport_class.update_pie_chart(labels, values)

        # ---- Chart 6: Monthly income evolution (stacked bar) ----
        income_evolution = Payment.get_monthly_income_evolution(self.selected_year, self.selected_class)
        labels = [format_month_label(mk) for mk, _, _, _ in income_evolution]
        series = {
            "Inscription": [v[1] for v in income_evolution],
            "Mensualité": [v[2] for v in income_evolution],
            "Transport": [v[3] for v in income_evolution],
        }
        self.chart_income_evolution.update_stacked_bar_chart(labels, series, ylabel="Montant (DH)")

        # ---- Chart 7: Payment status distribution (donut) ----
        # Aggregated across all months for the selected year/class.
        distribution = Payment.get_payment_status_distribution(
            self.selected_year, None, self.selected_class
        )
        self.chart_payment_status.update_donut_chart(
            [PAYMENT_STATUS_LABELS[STATUS_PAID], PAYMENT_STATUS_LABELS[STATUS_UNPAID],
             PAYMENT_STATUS_LABELS[STATUS_NAN]],
            [distribution[STATUS_PAID], distribution[STATUS_UNPAID], distribution[STATUS_NAN]]
        )

        # ---- Chart 8: Income by class (bar) ----
        income_by_class = Payment.get_income_by_class(self.selected_year)
        if self.selected_class != "Toutes":
            income_by_class = [(c, n) for c, n in income_by_class if c == self.selected_class]
        labels = [c for c, _ in income_by_class]
        values = [n for _, n in income_by_class]
        self.chart_income_by_class.update_bar_chart(labels, values, ylabel="Revenus (DH)")
