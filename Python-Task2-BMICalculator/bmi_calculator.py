import csv
import sqlite3
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


DATABASE_FILE = Path(__file__).with_name("bmi_records.db")

# Colour palette
BG = "#0B1220"
CARD = "#142033"
CARD_ALT = "#1D2B40"
BORDER = "#2D405A"
PRIMARY = "#4F7CFF"
PRIMARY_HOVER = "#3D67E8"
TEXT = "#F8FAFC"
MUTED = "#AFC0D4"
INPUT_BG = "#F8FAFC"
INPUT_TEXT = "#111827"
GREEN = "#34D399"
BLUE = "#60A5FA"
ORANGE = "#FB923C"
RED = "#F87171"
YELLOW = "#FACC15"


class BMITrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BMI Health Tracker")
        self.root.geometry("1180x880")
        self.root.minsize(920, 700)
        self.root.configure(bg=BG)

        self.connection = None
        self.selected_record_id = None

        self.user_name = tk.StringVar()
        self.unit_system = tk.StringVar(value="Metric")
        self.weight_value = tk.StringVar()
        self.height_value = tk.StringVar()
        self.search_user = tk.StringVar()

        self.bmi_value = tk.StringVar(value="--")
        self.category_value = tk.StringVar(value="No result yet")
        self.result_note = tk.StringVar(
            value='Fill in your details and click "Calculate BMI" to see your result.'
        )
        self.summary_text = tk.StringVar(value="No saved records yet.")
        self.status_text = tk.StringVar(value="Ready")

        self.total_records_text = tk.StringVar(value="0")
        self.average_bmi_text = tk.StringVar(value="--")
        self.healthy_records_text = tk.StringVar(value="0")
        self.highest_bmi_text = tk.StringVar(value="--")

        self.setup_styles()
        self.setup_database()
        self.build_scroll_area()
        self.build_interface()
        self.load_users()
        self.refresh_history()
        self.root.protocol("WM_DELETE_WINDOW", self.close_app)

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Treeview",
            background=CARD_ALT,
            fieldbackground=CARD_ALT,
            foreground=TEXT,
            rowheight=32,
            borderwidth=0,
            font=("Helvetica", 10),
        )
        style.configure(
            "Treeview.Heading",
            background=CARD,
            foreground=TEXT,
            font=("Helvetica", 10, "bold"),
            relief="flat",
        )
        style.map(
            "Treeview",
            background=[("selected", PRIMARY)],
            foreground=[("selected", TEXT)],
        )
        style.configure(
            "TCombobox",
            fieldbackground=INPUT_BG,
            background=INPUT_BG,
            foreground=INPUT_TEXT,
            padding=7,
        )

    def setup_database(self):
        try:
            self.connection = sqlite3.connect(DATABASE_FILE)
            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS bmi_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_name TEXT NOT NULL,
                    weight_kg REAL NOT NULL,
                    height_m REAL NOT NULL,
                    bmi REAL NOT NULL,
                    category TEXT NOT NULL,
                    recorded_at TEXT NOT NULL
                )
                """
            )
            self.connection.commit()
        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Your BMI records could not be opened.\n\n{error}",
            )
            self.root.destroy()

    def build_scroll_area(self):
        container = tk.Frame(self.root, bg=BG)
        container.pack(fill="both", expand=True)

        self.page_canvas = tk.Canvas(
            container,
            bg=BG,
            highlightthickness=0,
            borderwidth=0,
        )
        self.page_canvas.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(
            container,
            orient="vertical",
            command=self.page_canvas.yview,
        )
        scrollbar.pack(side="right", fill="y")
        self.page_canvas.configure(yscrollcommand=scrollbar.set)

        self.page = tk.Frame(self.page_canvas, bg=BG, padx=34, pady=26)
        self.page_window = self.page_canvas.create_window(
            (0, 0),
            window=self.page,
            anchor="nw",
        )

        self.page.bind(
            "<Configure>",
            lambda event: self.page_canvas.configure(
                scrollregion=self.page_canvas.bbox("all")
            ),
        )
        self.page_canvas.bind(
            "<Configure>",
            lambda event: self.page_canvas.itemconfigure(
                self.page_window,
                width=event.width,
            ),
        )

        self.root.bind_all("<MouseWheel>", self.scroll_page)
        self.root.bind_all("<Button-4>", lambda event: self.page_canvas.yview_scroll(-1, "units"))
        self.root.bind_all("<Button-5>", lambda event: self.page_canvas.yview_scroll(1, "units"))

    def scroll_page(self, event):
        if event.delta == 0:
            return "break"
        direction = -1 if event.delta > 0 else 1
        self.page_canvas.yview_scroll(direction, "units")
        return "break"

    def build_interface(self):
        self.build_header()
        self.build_input_card()
        self.build_result_card()
        self.build_stats_row()
        self.build_history_card()
        self.build_chart_card()
        self.build_footer()

    def build_header(self):
        header = tk.Frame(self.page, bg=BG)
        header.pack(fill="x", pady=(0, 20))

        tk.Label(
            header,
            text="BMI Health Tracker",
            font=("Helvetica", 30, "bold"),
            bg=BG,
            fg=TEXT,
        ).pack()

        tk.Label(
            header,
            text="Calculate your BMI, save your results, and follow your progress over time.",
            font=("Helvetica", 12),
            bg=BG,
            fg=MUTED,
        ).pack(pady=(7, 0))

    def create_card(self):
        border = tk.Frame(self.page, bg=BORDER, padx=1, pady=1)
        card = tk.Frame(border, bg=CARD, padx=24, pady=22)
        card.pack(fill="both", expand=True)
        return border, card

    def add_heading(self, parent, title, description):
        tk.Label(
            parent,
            text=title,
            font=("Helvetica", 17, "bold"),
            bg=CARD,
            fg=TEXT,
            anchor="w",
        ).pack(fill="x")

        tk.Label(
            parent,
            text=description,
            font=("Helvetica", 10),
            bg=CARD,
            fg=MUTED,
            anchor="w",
        ).pack(fill="x", pady=(4, 16))

    def add_form_label(self, parent, text, row, column):
        tk.Label(
            parent,
            text=text,
            font=("Helvetica", 10, "bold"),
            bg=CARD,
            fg=TEXT,
            anchor="w",
        ).grid(
            row=row,
            column=column,
            sticky="w",
            padx=(0 if column == 0 else 10, 0),
            pady=(0 if row == 0 else 18, 7),
        )

    def make_button(self, parent, text, command, color=PRIMARY, hover=PRIMARY_HOVER):
        button = tk.Label(
            parent,
            text=text,
            font=("Helvetica", 10, "bold"),
            bg=color,
            fg=TEXT,
            padx=16,
            pady=10,
            cursor="hand2",
        )
        button.bind("<Button-1>", lambda event: command())
        button.bind("<Enter>", lambda event: button.config(bg=hover))
        button.bind("<Leave>", lambda event: button.config(bg=color))
        return button

    def build_input_card(self):
        border, card = self.create_card()
        border.pack(fill="x", pady=(0, 18))

        self.add_heading(
            card,
            "Your Information",
            "Enter your details below to calculate your BMI.",
        )

        form = tk.Frame(card, bg=CARD)
        form.pack(fill="x")

        for column in range(3):
            form.grid_columnconfigure(column, weight=1)

        self.add_form_label(form, "Name", 0, 0)
        self.user_box = ttk.Combobox(
            form,
            textvariable=self.user_name,
            font=("Helvetica", 11),
        )
        self.user_box.grid(row=1, column=0, sticky="ew", padx=(0, 10), ipady=3)
        self.user_box.bind("<<ComboboxSelected>>", self.on_user_selected)

        self.add_form_label(form, "Units", 0, 1)
        unit_box = ttk.Combobox(
            form,
            textvariable=self.unit_system,
            values=["Metric", "Imperial"],
            state="readonly",
            font=("Helvetica", 11),
        )
        unit_box.grid(row=1, column=1, sticky="ew", padx=10, ipady=3)
        unit_box.bind("<<ComboboxSelected>>", self.update_unit_labels)

        self.add_form_label(form, "Weight", 0, 2)
        tk.Entry(
            form,
            textvariable=self.weight_value,
            font=("Helvetica", 12),
            bg=INPUT_BG,
            fg=INPUT_TEXT,
            relief="flat",
        ).grid(row=1, column=2, sticky="ew", padx=(10, 0), ipady=10)

        self.weight_unit_label = tk.Label(
            form,
            text="Kilograms (kg)",
            font=("Helvetica", 9),
            bg=CARD,
            fg=MUTED,
        )
        self.weight_unit_label.grid(
            row=2,
            column=2,
            sticky="w",
            padx=(10, 0),
            pady=(4, 0),
        )

        self.add_form_label(form, "Height", 3, 0)
        tk.Entry(
            form,
            textvariable=self.height_value,
            font=("Helvetica", 12),
            bg=INPUT_BG,
            fg=INPUT_TEXT,
            relief="flat",
        ).grid(row=4, column=0, sticky="ew", padx=(0, 10), ipady=10)

        self.height_unit_label = tk.Label(
            form,
            text="Metres (m)",
            font=("Helvetica", 9),
            bg=CARD,
            fg=MUTED,
        )
        self.height_unit_label.grid(
            row=5,
            column=0,
            sticky="w",
            pady=(4, 0),
        )

        buttons = tk.Frame(form, bg=CARD)
        buttons.grid(row=4, column=1, columnspan=2, sticky="e", padx=(10, 0))

        self.make_button(
            buttons,
            "Calculate BMI",
            self.calculate_and_save,
        ).pack(side="left", padx=(0, 8))

        self.make_button(
            buttons,
            "Clear",
            self.clear_form,
            CARD_ALT,
            BORDER,
        ).pack(side="left")

        self.root.bind("<Return>", lambda event: self.calculate_and_save())

    def build_result_card(self):
        border, card = self.create_card()
        border.pack(fill="x", pady=(0, 18))

        self.add_heading(
            card,
            "Your BMI Result",
            "Your result and a simple health summary will appear here.",
        )

        row = tk.Frame(card, bg=CARD)
        row.pack(fill="x")

        result_panel = tk.Frame(
            row,
            bg=CARD_ALT,
            padx=24,
            pady=20,
        )
        result_panel.pack(side="left", fill="both", expand=True)

        tk.Label(
            result_panel,
            text="YOUR BMI",
            font=("Helvetica", 10, "bold"),
            bg=CARD_ALT,
            fg=MUTED,
        ).pack(anchor="w")

        self.bmi_label = tk.Label(
            result_panel,
            textvariable=self.bmi_value,
            font=("Helvetica", 48, "bold"),
            bg=CARD_ALT,
            fg=TEXT,
        )
        self.bmi_label.pack(anchor="w", pady=(3, 0))

        self.category_label = tk.Label(
            result_panel,
            textvariable=self.category_value,
            font=("Helvetica", 17, "bold"),
            bg=CARD_ALT,
            fg=MUTED,
        )
        self.category_label.pack(anchor="w", pady=(0, 8))

        tk.Label(
            result_panel,
            text="Healthy BMI range: 18.5 to 24.9",
            font=("Helvetica", 10),
            bg=CARD_ALT,
            fg=MUTED,
        ).pack(anchor="w")

        summary_panel = tk.Frame(
            row,
            bg=CARD_ALT,
            padx=24,
            pady=20,
        )
        summary_panel.pack(
            side="right",
            fill="both",
            expand=True,
            padx=(18, 0),
        )

        tk.Label(
            summary_panel,
            text="Health Summary",
            font=("Helvetica", 12, "bold"),
            bg=CARD_ALT,
            fg=TEXT,
        ).pack(anchor="w")

        tk.Label(
            summary_panel,
            textvariable=self.result_note,
            font=("Helvetica", 11),
            bg=CARD_ALT,
            fg=MUTED,
            wraplength=470,
            justify="left",
        ).pack(anchor="w", pady=(10, 0))

    def build_stats_row(self):
        wrapper = tk.Frame(self.page, bg=BG)
        wrapper.pack(fill="x", pady=(0, 18))

        stats = [
            ("Total Records", self.total_records_text),
            ("Average BMI", self.average_bmi_text),
            ("Healthy Records", self.healthy_records_text),
            ("Highest BMI", self.highest_bmi_text),
        ]

        for index, (title, variable) in enumerate(stats):
            card = tk.Frame(
                wrapper,
                bg=CARD,
                highlightbackground=BORDER,
                highlightthickness=1,
                padx=18,
                pady=15,
            )
            card.pack(
                side="left",
                fill="both",
                expand=True,
                padx=(0 if index == 0 else 6, 0 if index == len(stats) - 1 else 6),
            )

            tk.Label(
                card,
                text=title,
                font=("Helvetica", 9, "bold"),
                bg=CARD,
                fg=MUTED,
            ).pack(anchor="w")

            tk.Label(
                card,
                textvariable=variable,
                font=("Helvetica", 22, "bold"),
                bg=CARD,
                fg=TEXT,
            ).pack(anchor="w", pady=(4, 0))

    def build_history_card(self):
        border, card = self.create_card()
        border.pack(fill="x", pady=(0, 18))

        self.add_heading(
            card,
            "BMI History",
            "Review your saved results or select a record to remove it.",
        )

        controls = tk.Frame(card, bg=CARD)
        controls.pack(fill="x", pady=(0, 12))

        tk.Label(
            controls,
            text="Find a user",
            font=("Helvetica", 10, "bold"),
            bg=CARD,
            fg=TEXT,
        ).pack(side="left")

        search_entry = tk.Entry(
            controls,
            textvariable=self.search_user,
            font=("Helvetica", 11),
            bg=INPUT_BG,
            fg=INPUT_TEXT,
            relief="flat",
            width=24,
        )
        search_entry.pack(side="left", padx=(10, 12), ipady=7)
        self.search_user.trace_add("write", lambda *args: self.refresh_history())

        tk.Label(
            controls,
            textvariable=self.summary_text,
            font=("Helvetica", 10),
            bg=CARD,
            fg=MUTED,
        ).pack(side="left")

        self.make_button(
            controls,
            "Export CSV",
            self.export_records,
            CARD_ALT,
            BORDER,
        ).pack(side="right", padx=(8, 0))

        self.make_button(
            controls,
            "Delete Selected",
            self.delete_selected_record,
            CARD_ALT,
            RED,
        ).pack(side="right")

        table_frame = tk.Frame(card, bg=CARD)
        table_frame.pack(fill="both", expand=True)

        columns = ("date", "user", "weight", "height", "bmi", "category")
        self.history_table = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=9,
        )

        headings = [
            "Date and Time",
            "User",
            "Weight (kg)",
            "Height (m)",
            "BMI",
            "Category",
        ]
        widths = [175, 150, 100, 100, 80, 120]

        for column, heading, width in zip(columns, headings, widths):
            self.history_table.heading(column, text=heading)
            self.history_table.column(column, width=width, anchor="center")

        table_scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.history_table.yview,
        )
        self.history_table.configure(yscrollcommand=table_scrollbar.set)

        self.history_table.pack(side="left", fill="both", expand=True)
        table_scrollbar.pack(side="right", fill="y")
        self.history_table.bind("<<TreeviewSelect>>", self.select_history_record)

    def build_chart_card(self):
        border, card = self.create_card()
        border.pack(fill="x", pady=(0, 18))

        self.add_heading(
            card,
            "Your Progress",
            "Choose a user to see how their BMI has changed over time.",
        )

        self.figure = Figure(figsize=(8, 3.6), dpi=100, facecolor=CARD)
        self.chart = self.figure.add_subplot(111)
        self.chart_canvas = FigureCanvasTkAgg(self.figure, master=card)
        self.chart_canvas.get_tk_widget().pack(fill="both", expand=True)

        self.draw_empty_chart("Choose a user with saved results.")

    def build_footer(self):
        footer = tk.Frame(self.page, bg=BG)
        footer.pack(fill="x", pady=(0, 15))

        tk.Label(
            footer,
            text="BMI is a general health guide and does not replace professional medical advice.",
            font=("Helvetica", 9),
            bg=BG,
            fg=MUTED,
        ).pack(side="left")

        tk.Label(
            footer,
            textvariable=self.status_text,
            font=("Helvetica", 9, "bold"),
            bg=BG,
            fg=MUTED,
        ).pack(side="right")

    def update_unit_labels(self, event=None):
        if self.unit_system.get() == "Metric":
            self.weight_unit_label.config(text="Kilograms (kg)")
            self.height_unit_label.config(text="Metres (m)")
        else:
            self.weight_unit_label.config(text="Pounds (lb)")
            self.height_unit_label.config(text="Inches (in)")

    def validate_inputs(self):
        name = self.user_name.get().strip()
        if not name:
            raise ValueError("Enter your name.")

        try:
            weight = float(self.weight_value.get())
            height = float(self.height_value.get())
        except ValueError as error:
            raise ValueError("Weight and height must be numbers.") from error

        if weight <= 0 or height <= 0:
            raise ValueError("Weight and height must be greater than zero.")

        if self.unit_system.get() == "Imperial":
            weight_kg = weight * 0.45359237
            height_m = height * 0.0254
        else:
            weight_kg = weight
            height_m = height

        if weight_kg > 500:
            raise ValueError("Please check the weight you entered.")
        if height_m < 0.5 or height_m > 3:
            raise ValueError("Please check the height you entered.")

        return name, weight_kg, height_m

    @staticmethod
    def get_category(bmi):
        if bmi < 18.5:
            return "Underweight", BLUE
        if bmi < 25:
            return "Healthy Weight", GREEN
        if bmi < 30:
            return "Overweight", ORANGE
        return "Obese", RED

    @staticmethod
    def get_result_message(category):
        messages = {
            "Underweight": (
                "Your BMI is below the usual healthy range. A balanced diet and advice "
                "from a qualified health professional may help."
            ),
            "Healthy Weight": (
                "Your BMI is within the usual healthy range. Keep supporting it with "
                "balanced meals, regular movement, and enough rest."
            ),
            "Overweight": (
                "Your BMI is above the usual healthy range. Small, steady changes to food "
                "choices and activity can make a meaningful difference."
            ),
            "Obese": (
                "Your BMI is well above the usual healthy range. Consider speaking with a "
                "qualified health professional for advice suited to you."
            ),
        }
        return messages[category]

    def calculate_and_save(self):
        try:
            name, weight_kg, height_m = self.validate_inputs()
            bmi = round(weight_kg / (height_m ** 2), 2)
            category, color = self.get_category(bmi)

            self.connection.execute(
                """
                INSERT INTO bmi_records (
                    user_name, weight_kg, height_m, bmi, category, recorded_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    name,
                    weight_kg,
                    height_m,
                    bmi,
                    category,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )
            self.connection.commit()

            self.bmi_value.set(f"{bmi:.2f}")
            self.category_value.set(category)
            self.result_note.set(self.get_result_message(category))
            self.bmi_label.config(fg=color)
            self.category_label.config(fg=color)
            self.status_text.set(f"Result saved for {name}")

            self.load_users()
            self.refresh_history()
            self.refresh_chart()

        except ValueError as error:
            messagebox.showwarning("Check Your Details", str(error))
            self.status_text.set("Please check your details")
        except sqlite3.Error as error:
            messagebox.showerror(
                "Save Error",
                f"Your result could not be saved.\n\n{error}",
            )
            self.status_text.set("Could not save result")

    def clear_form(self):
        self.user_name.set("")
        self.weight_value.set("")
        self.height_value.set("")
        self.unit_system.set("Metric")
        self.update_unit_labels()

        self.bmi_value.set("--")
        self.category_value.set("No result yet")
        self.result_note.set(
            'Fill in your details and click "Calculate BMI" to see your result.'
        )
        self.bmi_label.config(fg=TEXT)
        self.category_label.config(fg=MUTED)
        self.status_text.set("Form cleared")

    def load_users(self):
        try:
            rows = self.connection.execute(
                """
                SELECT DISTINCT user_name
                FROM bmi_records
                ORDER BY user_name COLLATE NOCASE
                """
            ).fetchall()
            self.user_box["values"] = [row[0] for row in rows]
        except sqlite3.Error:
            self.user_box["values"] = []

    def on_user_selected(self, event=None):
        selected = self.user_name.get().strip()
        self.search_user.set(selected)
        self.refresh_history()
        self.refresh_chart()

    def refresh_history(self):
        for item in self.history_table.get_children():
            self.history_table.delete(item)

        search = self.search_user.get().strip()

        try:
            if search:
                rows = self.connection.execute(
                    """
                    SELECT id, recorded_at, user_name, weight_kg, height_m, bmi, category
                    FROM bmi_records
                    WHERE user_name LIKE ?
                    ORDER BY recorded_at DESC
                    """,
                    (f"%{search}%",),
                ).fetchall()
            else:
                rows = self.connection.execute(
                    """
                    SELECT id, recorded_at, user_name, weight_kg, height_m, bmi, category
                    FROM bmi_records
                    ORDER BY recorded_at DESC
                    """
                ).fetchall()

            for row in rows:
                record_id, recorded_at, user, weight, height, bmi, category = row
                self.history_table.insert(
                    "",
                    "end",
                    iid=str(record_id),
                    values=(
                        recorded_at,
                        user,
                        f"{weight:.2f}",
                        f"{height:.3f}",
                        f"{bmi:.2f}",
                        category,
                    ),
                )

            if rows:
                average = sum(row[5] for row in rows) / len(rows)
                self.summary_text.set(
                    f"{len(rows)} record(s) • Average BMI: {average:.2f}"
                )
            else:
                self.summary_text.set("No matching records.")

            self.update_statistics()
        except sqlite3.Error as error:
            messagebox.showerror(
                "History Error",
                f"Your BMI history could not be loaded.\n\n{error}",
            )

    def update_statistics(self):
        try:
            total, average, healthy, highest = self.connection.execute(
                """
                SELECT
                    COUNT(*),
                    AVG(bmi),
                    SUM(CASE WHEN bmi >= 18.5 AND bmi < 25 THEN 1 ELSE 0 END),
                    MAX(bmi)
                FROM bmi_records
                """
            ).fetchone()

            self.total_records_text.set(str(total or 0))
            self.average_bmi_text.set(f"{average:.2f}" if average is not None else "--")
            self.healthy_records_text.set(str(healthy or 0))
            self.highest_bmi_text.set(f"{highest:.2f}" if highest is not None else "--")
        except sqlite3.Error:
            self.total_records_text.set("--")
            self.average_bmi_text.set("--")
            self.healthy_records_text.set("--")
            self.highest_bmi_text.set("--")

    def select_history_record(self, event=None):
        selection = self.history_table.selection()
        self.selected_record_id = int(selection[0]) if selection else None

    def delete_selected_record(self):
        if self.selected_record_id is None:
            messagebox.showinfo(
                "Select a Record",
                "Choose a BMI record before deleting it.",
            )
            return

        if not messagebox.askyesno(
            "Delete Record",
            "Delete the selected BMI record?",
        ):
            return

        try:
            self.connection.execute(
                "DELETE FROM bmi_records WHERE id = ?",
                (self.selected_record_id,),
            )
            self.connection.commit()
            self.selected_record_id = None
            self.refresh_history()
            self.refresh_chart()
            self.load_users()
            self.status_text.set("Record deleted")
        except sqlite3.Error as error:
            messagebox.showerror(
                "Delete Error",
                f"The selected record could not be deleted.\n\n{error}",
            )

    def export_records(self):
        rows = [
            self.history_table.item(item, "values")
            for item in self.history_table.get_children()
        ]

        if not rows:
            messagebox.showinfo(
                "Nothing to Export",
                "There are no BMI records to export.",
            )
            return

        path = filedialog.asksaveasfilename(
            title="Save BMI Records",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile="bmi_records.csv",
        )
        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(
                    [
                        "Date and Time",
                        "User",
                        "Weight (kg)",
                        "Height (m)",
                        "BMI",
                        "Category",
                    ]
                )
                writer.writerows(rows)

            self.status_text.set("CSV exported")
            messagebox.showinfo(
                "Export Complete",
                "Your BMI records were saved successfully.",
            )
        except OSError as error:
            messagebox.showerror(
                "Export Error",
                f"The CSV file could not be saved.\n\n{error}",
            )

    def refresh_chart(self):
        user = self.user_name.get().strip() or self.search_user.get().strip()

        if not user:
            self.draw_empty_chart("Choose a user with saved results.")
            return

        try:
            rows = self.connection.execute(
                """
                SELECT recorded_at, bmi
                FROM bmi_records
                WHERE lower(user_name) = lower(?)
                ORDER BY recorded_at ASC
                """,
                (user,),
            ).fetchall()
        except sqlite3.Error:
            self.draw_empty_chart("The chart could not be loaded.")
            return

        if not rows:
            self.draw_empty_chart(f"No saved BMI results for {user}.")
            return

        dates = [
            datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
            for row in rows
        ]
        values = [row[1] for row in rows]

        self.chart.clear()
        self.style_chart()
        self.chart.plot(
            dates,
            values,
            marker="o",
            linewidth=2.2,
            markersize=6,
        )
        self.chart.axhspan(18.5, 24.9, alpha=0.12)
        self.chart.set_title(
            f"{user.title()}'s BMI Progress",
            color=TEXT,
            fontsize=12,
            pad=12,
        )
        self.chart.set_ylabel("BMI", color=MUTED)
        self.figure.autofmt_xdate(rotation=25)
        self.figure.tight_layout()
        self.chart_canvas.draw_idle()

    def style_chart(self):
        self.chart.set_facecolor(CARD)
        self.chart.tick_params(colors=MUTED)
        self.chart.grid(alpha=0.18)
        for spine in self.chart.spines.values():
            spine.set_color(BORDER)

    def draw_empty_chart(self, message):
        self.chart.clear()
        self.style_chart()
        self.chart.set_xticks([])
        self.chart.set_yticks([])
        self.chart.text(
            0.5,
            0.5,
            message,
            transform=self.chart.transAxes,
            ha="center",
            va="center",
            color=MUTED,
            fontsize=12,
        )
        self.figure.tight_layout()
        self.chart_canvas.draw_idle()

    def close_app(self):
        if self.connection is not None:
            self.connection.close()
        self.root.destroy()


def start_app():
    root = tk.Tk()
    BMITrackerApp(root)
    root.mainloop()


if __name__ == "__main__":
    start_app()