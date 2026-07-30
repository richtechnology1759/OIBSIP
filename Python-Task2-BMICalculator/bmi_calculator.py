import csv
import sqlite3
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

DATABASE_FILE = Path(__file__).with_name("bmi_records.db")

NAVY = "#0F172A"
CARD = "#1E293B"
CARD_LIGHT = "#334155"
BLUE = "#2563EB"
BLUE_HOVER = "#1D4ED8"
WHITE = "#F8FAFC"
MUTED = "#CBD5E1"
INPUT_BG = "#F8FAFC"
INPUT_TEXT = "#0F172A"
GREEN = "#22C55E"
YELLOW = "#EAB308"
ORANGE = "#F97316"
RED = "#EF4444"
BORDER = "#475569"


class BMITrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BMI Health Tracker")
        self.root.geometry("1120x860")
        self.root.minsize(900, 680)
        self.root.configure(bg=NAVY)

        self.connection = None
        self.selected_record_id = None

        self.user_name = tk.StringVar()
        self.unit_system = tk.StringVar(value="Metric")
        self.weight_value = tk.StringVar()
        self.height_value = tk.StringVar()
        self.bmi_value = tk.StringVar(value="--")
        self.category_value = tk.StringVar(value="No result yet")
        self.result_note = tk.StringVar(value="Enter your details and calculate your BMI.")
        self.summary_text = tk.StringVar(value="No saved records yet.")
        self.status_text = tk.StringVar(value="Ready")

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
        style.configure("Treeview", background=CARD_LIGHT, fieldbackground=CARD_LIGHT,
                        foreground=WHITE, rowheight=30, borderwidth=0,
                        font=("Helvetica", 10))
        style.configure("Treeview.Heading", background=CARD, foreground=WHITE,
                        font=("Helvetica", 10, "bold"), relief="flat")
        style.map("Treeview", background=[("selected", BLUE)],
                  foreground=[("selected", WHITE)])
        style.configure("TCombobox", fieldbackground=INPUT_BG, background=INPUT_BG,
                        foreground=INPUT_TEXT, padding=7)

    def setup_database(self):
        try:
            self.connection = sqlite3.connect(DATABASE_FILE)
            self.connection.execute("""
                CREATE TABLE IF NOT EXISTS bmi_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_name TEXT NOT NULL,
                    weight_kg REAL NOT NULL,
                    height_m REAL NOT NULL,
                    bmi REAL NOT NULL,
                    category TEXT NOT NULL,
                    recorded_at TEXT NOT NULL
                )
            """)
            self.connection.commit()
        except sqlite3.Error as error:
            messagebox.showerror("Database Error", f"The database could not be opened.\n\n{error}")
            self.root.destroy()

    def build_scroll_area(self):
        self.page_canvas = tk.Canvas(self.root, bg=NAVY, highlightthickness=0)
        self.page_canvas.pack(side="left", fill="both", expand=True)
        scrollbar = tk.Scrollbar(self.root, orient="vertical", command=self.page_canvas.yview)
        scrollbar.pack(side="right", fill="y")
        self.page_canvas.configure(yscrollcommand=scrollbar.set)

        self.page = tk.Frame(self.page_canvas, bg=NAVY, padx=36, pady=28)
        self.page_window = self.page_canvas.create_window((0, 0), window=self.page, anchor="nw")
        self.page.bind("<Configure>", lambda event: self.page_canvas.configure(
            scrollregion=self.page_canvas.bbox("all")))
        self.page_canvas.bind("<Configure>", lambda event: self.page_canvas.itemconfigure(
            self.page_window, width=event.width))
        self.root.bind_all("<MouseWheel>", self.scroll_page)

    def scroll_page(self, event):
        self.page_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def build_interface(self):
        self.build_header()
        self.build_input_card()
        self.build_result_card()
        self.build_history_card()
        self.build_chart_card()
        self.build_footer()

    def build_header(self):
        header = tk.Frame(self.page, bg=NAVY)
        header.pack(fill="x", pady=(0, 22))
        tk.Label(header, text="BMI Health Tracker", font=("Helvetica", 28, "bold"),
                 bg=NAVY, fg=WHITE).pack()
        tk.Label(header, text="Calculate BMI, save records for different users, and view trends over time.",
                 font=("Helvetica", 12), bg=NAVY, fg=MUTED).pack(pady=(7, 0))

    def create_card(self):
        border = tk.Frame(self.page, bg=BORDER, padx=1, pady=1)
        card = tk.Frame(border, bg=CARD, padx=24, pady=22)
        card.pack(fill="both", expand=True)
        return border, card

    def add_heading(self, parent, title, description):
        tk.Label(parent, text=title, font=("Helvetica", 16, "bold"), bg=CARD,
                 fg=WHITE, anchor="w").pack(fill="x")
        tk.Label(parent, text=description, font=("Helvetica", 10), bg=CARD,
                 fg=MUTED, anchor="w").pack(fill="x", pady=(4, 16))

    def build_input_card(self):
        border, card = self.create_card()
        border.pack(fill="x", pady=(0, 18))
        self.add_heading(card, "BMI Details", "Enter a user name, unit system, weight and height.")

        form = tk.Frame(card, bg=CARD)
        form.pack(fill="x")
        for column in range(3):
            form.grid_columnconfigure(column, weight=1)

        self.add_label(form, "User name", 0, 0)
        self.user_box = ttk.Combobox(form, textvariable=self.user_name, font=("Helvetica", 11))
        self.user_box.grid(row=1, column=0, sticky="ew", padx=(0, 10), ipady=3)
        self.user_box.bind("<<ComboboxSelected>>", self.on_user_selected)

        self.add_label(form, "Unit system", 0, 1)
        unit_box = ttk.Combobox(form, textvariable=self.unit_system,
                               values=["Metric", "Imperial"], state="readonly",
                               font=("Helvetica", 11))
        unit_box.grid(row=1, column=1, sticky="ew", padx=10, ipady=3)
        unit_box.bind("<<ComboboxSelected>>", self.update_unit_labels)

        self.add_label(form, "Weight", 0, 2)
        tk.Entry(form, textvariable=self.weight_value, font=("Helvetica", 12),
                 bg=INPUT_BG, fg=INPUT_TEXT, relief="flat").grid(
                     row=1, column=2, sticky="ew", padx=(10, 0), ipady=9)
        self.weight_unit_label = tk.Label(form, text="Kilograms (kg)", font=("Helvetica", 9),
                                          bg=CARD, fg=MUTED)
        self.weight_unit_label.grid(row=2, column=2, sticky="w", padx=(10, 0), pady=(4, 0))

        self.add_label(form, "Height", 3, 0)
        tk.Entry(form, textvariable=self.height_value, font=("Helvetica", 12),
                 bg=INPUT_BG, fg=INPUT_TEXT, relief="flat").grid(
                     row=4, column=0, sticky="ew", padx=(0, 10), ipady=9)
        self.height_unit_label = tk.Label(form, text="Metres (m)", font=("Helvetica", 9),
                                          bg=CARD, fg=MUTED)
        self.height_unit_label.grid(row=5, column=0, sticky="w", pady=(4, 0))

        buttons = tk.Frame(form, bg=CARD)
        buttons.grid(row=4, column=1, columnspan=2, sticky="e", padx=(10, 0))
        self.make_button(buttons, "Calculate and Save", self.calculate_and_save,
                         BLUE, BLUE_HOVER).pack(side="left", padx=(0, 8))
        self.make_button(buttons, "Clear Form", self.clear_form,
                         CARD_LIGHT, BORDER).pack(side="left")
        self.root.bind("<Return>", lambda event: self.calculate_and_save())

    def add_label(self, parent, text, row, column):
        tk.Label(parent, text=text, font=("Helvetica", 11, "bold"), bg=CARD,
                 fg=WHITE, anchor="w").grid(row=row, column=column, sticky="w",
                 padx=(0 if column == 0 else 10, 0), pady=(0 if row == 0 else 18, 7))

    def make_button(self, parent, text, command, normal_color, hover_color):
        button = tk.Label(parent, text=text, font=("Helvetica", 10, "bold"),
                          bg=normal_color, fg=WHITE, padx=16, pady=10, cursor="hand2")
        button.bind("<Button-1>", lambda event: command())
        button.bind("<Enter>", lambda event: button.config(bg=hover_color))
        button.bind("<Leave>", lambda event: button.config(bg=normal_color))
        return button

    def build_result_card(self):
        border, card = self.create_card()
        border.pack(fill="x", pady=(0, 18))
        self.add_heading(card, "Current Result", "BMI category and colour-coded feedback.")
        row = tk.Frame(card, bg=CARD)
        row.pack(fill="x")

        left = tk.Frame(row, bg=CARD)
        left.pack(side="left", fill="both", expand=True)
        tk.Label(left, text="BMI", font=("Helvetica", 11, "bold"), bg=CARD, fg=MUTED).pack(anchor="w")
        self.bmi_label = tk.Label(left, textvariable=self.bmi_value, font=("Helvetica", 42, "bold"),
                                  bg=CARD, fg=WHITE)
        self.bmi_label.pack(anchor="w")
        self.category_label = tk.Label(left, textvariable=self.category_value,
                                       font=("Helvetica", 16, "bold"), bg=CARD, fg=MUTED)
        self.category_label.pack(anchor="w")

        right = tk.Frame(row, bg=CARD_LIGHT, padx=20, pady=18)
        right.pack(side="right", fill="both", expand=True, padx=(24, 0))
        tk.Label(right, text="Result note", font=("Helvetica", 11, "bold"),
                 bg=CARD_LIGHT, fg=WHITE).pack(anchor="w")
        tk.Label(right, textvariable=self.result_note, font=("Helvetica", 11),
                 bg=CARD_LIGHT, fg=MUTED, wraplength=470, justify="left").pack(anchor="w", pady=(7, 0))

    def build_history_card(self):
        border, card = self.create_card()
        border.pack(fill="x", pady=(0, 18))
        self.add_heading(card, "Saved BMI Records", "Choose a user to filter records. Select a row before deleting.")

        top = tk.Frame(card, bg=CARD)
        top.pack(fill="x", pady=(0, 12))
        tk.Label(top, textvariable=self.summary_text, font=("Helvetica", 10),
                 bg=CARD, fg=MUTED).pack(side="left")
        self.make_button(top, "Export CSV", self.export_records, CARD_LIGHT, BORDER).pack(side="right", padx=(8, 0))
        self.make_button(top, "Delete Selected", self.delete_selected_record, CARD_LIGHT, RED).pack(side="right")

        table_frame = tk.Frame(card, bg=CARD)
        table_frame.pack(fill="both", expand=True)
        columns = ("date", "user", "weight", "height", "bmi", "category")
        self.history_table = ttk.Treeview(table_frame, columns=columns, show="headings", height=9)
        headings = ["Date and Time", "User", "Weight (kg)", "Height (m)", "BMI", "Category"]
        widths = [175, 150, 100, 100, 80, 120]
        for column, heading, width in zip(columns, headings, widths):
            self.history_table.heading(column, text=heading)
            self.history_table.column(column, width=width, anchor="center")
        table_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.history_table.yview)
        self.history_table.configure(yscrollcommand=table_scrollbar.set)
        self.history_table.pack(side="left", fill="both", expand=True)
        table_scrollbar.pack(side="right", fill="y")
        self.history_table.bind("<<TreeviewSelect>>", self.select_history_record)

    def build_chart_card(self):
        border, card = self.create_card()
        border.pack(fill="x", pady=(0, 18))
        self.add_heading(card, "BMI Trend", "Line chart showing the selected user's BMI records over time.")
        self.make_button(card, "Refresh Chart", self.refresh_chart, BLUE, BLUE_HOVER).pack(anchor="w", pady=(0, 10))

        self.figure = Figure(figsize=(8, 3.5), dpi=100, facecolor=CARD)
        self.chart = self.figure.add_subplot(111)
        self.chart_canvas = FigureCanvasTkAgg(self.figure, master=card)
        self.chart_canvas.get_tk_widget().pack(fill="both", expand=True)
        self.draw_empty_chart("Select a user with saved records.")

    def build_footer(self):
        footer = tk.Frame(self.page, bg=NAVY)
        footer.pack(fill="x", pady=(0, 15))
        tk.Label(footer, text="BMI is a general screening measure and is not a medical diagnosis.",
                 font=("Helvetica", 9), bg=NAVY, fg=MUTED).pack(side="left")
        tk.Label(footer, textvariable=self.status_text, font=("Helvetica", 9, "bold"),
                 bg=NAVY, fg=MUTED).pack(side="right")

    def update_unit_labels(self, event=None):
        if self.unit_system.get() == "Metric":
            self.weight_unit_label.config(text="Kilograms (kg)")
            self.height_unit_label.config(text="Metres (m)")
        else:
            self.weight_unit_label.config(text="Pounds (lb)")
            self.height_unit_label.config(text="Inches (in)")

    def calculate_and_save(self):
        name = self.user_name.get().strip()
        if not name:
            messagebox.showwarning("Missing User Name", "Please enter a user name before calculating.")
            return
        try:
            weight = float(self.weight_value.get())
            height = float(self.height_value.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Weight and height must be valid numbers.")
            return
        if weight <= 0 or height <= 0:
            messagebox.showerror("Invalid Input", "Weight and height must be greater than zero.")
            return

        if self.unit_system.get() == "Imperial":
            weight_kg = weight * 0.45359237
            height_m = height * 0.0254
        else:
            weight_kg = weight
            height_m = height

        if not 20 <= weight_kg <= 400:
            messagebox.showerror("Weight Out of Range", "Enter a realistic weight between 20 kg and 400 kg.")
            return
        if not 0.8 <= height_m <= 2.5:
            messagebox.showerror("Height Out of Range", "Enter a realistic height between 0.8 m and 2.5 m.")
            return

        bmi = weight_kg / (height_m ** 2)
        category, colour, note = self.classify_bmi(bmi)
        self.bmi_value.set(f"{bmi:.2f}")
        self.category_value.set(category)
        self.result_note.set(note)
        self.bmi_label.config(fg=colour)
        self.category_label.config(fg=colour)
        recorded_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            self.connection.execute("""
                INSERT INTO bmi_records (user_name, weight_kg, height_m, bmi, category, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, round(weight_kg, 2), round(height_m, 3), round(bmi, 2), category, recorded_at))
            self.connection.commit()
        except sqlite3.Error as error:
            messagebox.showerror("Save Error", f"The BMI record could not be saved.\n\n{error}")
            return

        self.status_text.set("BMI calculated and saved")
        self.load_users()
        self.refresh_history()
        self.refresh_chart()

    def classify_bmi(self, bmi):
        if bmi < 18.5:
            return "Underweight", YELLOW, "This BMI falls below the standard normal range."
        if bmi < 25:
            return "Normal", GREEN, "This BMI falls within the standard normal range."
        if bmi < 30:
            return "Overweight", ORANGE, "This BMI falls above the standard normal range."
        return "Obese", RED, "This BMI falls within the obese category."

    def load_users(self):
        try:
            rows = self.connection.execute("SELECT DISTINCT user_name FROM bmi_records ORDER BY user_name COLLATE NOCASE").fetchall()
            self.user_box["values"] = [row[0] for row in rows]
        except sqlite3.Error as error:
            messagebox.showerror("Database Error", f"User names could not be loaded.\n\n{error}")

    def on_user_selected(self, event=None):
        self.refresh_history()
        self.refresh_chart()

    def get_records(self, oldest_first=False):
        name = self.user_name.get().strip()
        order = "ASC" if oldest_first else "DESC"
        try:
            if name:
                return self.connection.execute(f"""
                    SELECT id, user_name, weight_kg, height_m, bmi, category, recorded_at
                    FROM bmi_records WHERE user_name = ? ORDER BY recorded_at {order}, id {order}
                """, (name,)).fetchall()
            return self.connection.execute(f"""
                SELECT id, user_name, weight_kg, height_m, bmi, category, recorded_at
                FROM bmi_records ORDER BY recorded_at {order}, id {order}
            """).fetchall()
        except sqlite3.Error as error:
            messagebox.showerror("Database Error", f"Records could not be loaded.\n\n{error}")
            return []

    def refresh_history(self):
        for item in self.history_table.get_children():
            self.history_table.delete(item)
        records = self.get_records()
        for record in records:
            record_id, name, weight, height, bmi, category, date = record
            self.history_table.insert("", "end", iid=str(record_id),
                                      values=(date, name, f"{weight:.2f}", f"{height:.3f}",
                                              f"{bmi:.2f}", category))
        if records:
            average_bmi = sum(record[4] for record in records) / len(records)
            self.summary_text.set(f"{len(records)} record(s) • Average BMI: {average_bmi:.2f}")
        else:
            self.summary_text.set("No saved records found.")
        self.selected_record_id = None

    def select_history_record(self, event=None):
        selected = self.history_table.selection()
        if selected:
            self.selected_record_id = int(selected[0])

    def delete_selected_record(self):
        if self.selected_record_id is None:
            messagebox.showwarning("No Record Selected", "Select a record before deleting.")
            return
        if not messagebox.askyesno("Delete Record", "Delete the selected BMI record?"):
            return
        try:
            self.connection.execute("DELETE FROM bmi_records WHERE id = ?", (self.selected_record_id,))
            self.connection.commit()
            self.refresh_history()
            self.refresh_chart()
            self.load_users()
            self.status_text.set("Selected record deleted")
        except sqlite3.Error as error:
            messagebox.showerror("Delete Error", f"The record could not be deleted.\n\n{error}")

    def export_records(self):
        records = self.get_records(oldest_first=True)
        if not records:
            messagebox.showinfo("Nothing to Export", "There are no records to export.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                                 filetypes=[("CSV files", "*.csv")],
                                                 initialfile="bmi_records.csv")
        if not file_path:
            return
        try:
            with open(file_path, "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["User Name", "Weight (kg)", "Height (m)", "BMI", "Category", "Recorded At"])
                for record in records:
                    _, name, weight, height, bmi, category, date = record
                    writer.writerow([name, weight, height, bmi, category, date])
            messagebox.showinfo("Export Complete", "BMI records exported successfully.")
            self.status_text.set("Records exported successfully")
        except OSError as error:
            messagebox.showerror("Export Error", f"The CSV file could not be created.\n\n{error}")

    def refresh_chart(self):
        name = self.user_name.get().strip()
        if not name:
            self.draw_empty_chart("Enter or select a user to view a BMI trend.")
            return
        records = self.get_records(oldest_first=True)
        if not records:
            self.draw_empty_chart(f"No saved records found for {name}.")
            return

        dates = [datetime.strptime(record[6], "%Y-%m-%d %H:%M:%S") for record in records]
        bmi_values = [record[4] for record in records]
        self.chart.clear()
        self.chart.set_facecolor(CARD)
        self.chart.plot(dates, bmi_values, marker="o", linewidth=2)
        self.chart.set_title(f"BMI Trend for {name}", color=WHITE, pad=12)
        self.chart.set_ylabel("BMI", color=MUTED)
        self.chart.set_xlabel("Date", color=MUTED)
        self.chart.tick_params(axis="x", colors=MUTED, rotation=25)
        self.chart.tick_params(axis="y", colors=MUTED)
        self.chart.grid(alpha=0.2)
        self.figure.tight_layout()
        self.chart_canvas.draw()

    def draw_empty_chart(self, message):
        self.chart.clear()
        self.chart.set_facecolor(CARD)
        self.chart.text(0.5, 0.5, message, ha="center", va="center",
                        color=MUTED, fontsize=12, transform=self.chart.transAxes)
        self.chart.set_xticks([])
        self.chart.set_yticks([])
        for spine in self.chart.spines.values():
            spine.set_visible(False)
        self.figure.tight_layout()
        self.chart_canvas.draw()

    def clear_form(self):
        self.user_name.set("")
        self.weight_value.set("")
        self.height_value.set("")
        self.unit_system.set("Metric")
        self.update_unit_labels()
        self.bmi_value.set("--")
        self.category_value.set("No result yet")
        self.result_note.set("Enter your details and calculate your BMI.")
        self.bmi_label.config(fg=WHITE)
        self.category_label.config(fg=MUTED)
        self.refresh_history()
        self.draw_empty_chart("Select a user with saved records.")
        self.status_text.set("Form cleared")

    def close_app(self):
        if self.connection:
            self.connection.close()
        self.root.destroy()


def start_app():
    root = tk.Tk()
    BMITrackerApp(root)
    root.mainloop()


if __name__ == "__main__":
    start_app()
