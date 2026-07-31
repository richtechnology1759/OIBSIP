import secrets
import string
import tkinter as tk
from datetime import datetime
from tkinter import messagebox

import pyperclip


MAX_HISTORY = 5

# App colours
NAVY = "#0F172A"
CARD_NAVY = "#1E293B"
LIGHT_NAVY = "#334155"
BLUE = "#2563EB"
DARK_BLUE = "#1D4ED8"
WHITE = "#F8FAFC"
LIGHT_TEXT = "#CBD5E1"
INPUT_BG = "#F8FAFC"
INPUT_TEXT = "#0F172A"
GREEN = "#22C55E"
ORANGE = "#F59E0B"
RED = "#EF4444"
BORDER = "#475569"


class PasswordGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("Secure Password Generator")
        self.root.geometry("1000x850")
        self.root.minsize(800, 650)
        self.root.configure(bg=NAVY)
        self.root.resizable(True, True)

        self.saved_passwords = []

        self.password_length = tk.IntVar(value=12)
        self.use_uppercase = tk.BooleanVar(value=True)
        self.use_lowercase = tk.BooleanVar(value=True)
        self.use_numbers = tk.BooleanVar(value=True)
        self.use_symbols = tk.BooleanVar(value=True)
        self.remove_confusing_chars = tk.BooleanVar(value=False)

        self.generated_password = tk.StringVar()
        self.password_strength = tk.StringVar(value="Not generated")
        self.password_info = tk.StringVar(
            value="Password length: 0 characters"
        )

        self.setup_scroll_area()
        self.build_app()

        self.root.bind(
            "<Return>",
            lambda event: self.generate_password(),
        )

    def setup_scroll_area(self):
        self.page_canvas = tk.Canvas(
            self.root,
            bg=NAVY,
            highlightthickness=0,
        )
        self.page_canvas.pack(
            side="left",
            fill="both",
            expand=True,
        )

        self.page_scrollbar = tk.Scrollbar(
            self.root,
            orient="vertical",
            command=self.page_canvas.yview,
        )
        self.page_scrollbar.pack(
            side="right",
            fill="y",
        )

        self.page_canvas.configure(
            yscrollcommand=self.page_scrollbar.set
        )

        self.page = tk.Frame(
            self.page_canvas,
            bg=NAVY,
            padx=45,
            pady=30,
        )

        self.page_window = self.page_canvas.create_window(
            (0, 0),
            window=self.page,
            anchor="nw",
        )

        self.page.bind(
            "<Configure>",
            self.update_scroll_area,
        )

        self.page_canvas.bind(
            "<Configure>",
            self.resize_page,
        )

        self.root.bind_all(
            "<MouseWheel>",
            self.scroll_page,
        )

        self.root.bind_all(
            "<Button-4>",
            self.scroll_up,
        )

        self.root.bind_all(
            "<Button-5>",
            self.scroll_down,
        )

    def update_scroll_area(self, event=None):
        self.page_canvas.configure(
            scrollregion=self.page_canvas.bbox("all")
        )

    def resize_page(self, event):
        self.page_canvas.itemconfigure(
            self.page_window,
            width=event.width,
        )

    def scroll_page(self, event):
        self.page_canvas.yview_scroll(
            int(-1 * (event.delta / 120)),
            "units",
        )

    def scroll_up(self, event):
        self.page_canvas.yview_scroll(
            -1,
            "units",
        )

    def scroll_down(self, event):
        self.page_canvas.yview_scroll(
            1,
            "units",
        )

    def build_app(self):
        self.build_header()
        self.build_settings_section()
        self.build_main_buttons()
        self.build_password_section()
        self.build_history_section()
        self.build_footer()

    def build_header(self):
        header = tk.Frame(
            self.page,
            bg=NAVY,
        )
        header.pack(
            fill="x",
            pady=(0, 25),
        )

        lock_icon = tk.Label(
            header,
            text="🔐",
            font=("Helvetica", 34),
            bg=NAVY,
            fg=WHITE,
        )
        lock_icon.pack()

        title = tk.Label(
            header,
            text="Secure Password Generator",
            font=("Helvetica", 27, "bold"),
            bg=NAVY,
            fg=WHITE,
        )
        title.pack(pady=(8, 5))

        description = tk.Label(
            header,
            text="Create secure passwords based on the settings you choose.",
            font=("Helvetica", 12),
            bg=NAVY,
            fg=LIGHT_TEXT,
            wraplength=720,
            justify="center",
        )
        description.pack()

    def create_card(self, parent):
        card_border = tk.Frame(
            parent,
            bg=BORDER,
            padx=1,
            pady=1,
        )

        card = tk.Frame(
            card_border,
            bg=CARD_NAVY,
            padx=25,
            pady=22,
        )
        card.pack(
            fill="both",
            expand=True,
        )

        return card_border, card

    def add_section_heading(self, parent, heading, description):
        heading_label = tk.Label(
            parent,
            text=heading,
            font=("Helvetica", 16, "bold"),
            bg=CARD_NAVY,
            fg=WHITE,
            anchor="w",
        )
        heading_label.pack(
            fill="x",
            pady=(0, 4),
        )

        description_label = tk.Label(
            parent,
            text=description,
            font=("Helvetica", 10),
            bg=CARD_NAVY,
            fg=LIGHT_TEXT,
            anchor="w",
            justify="left",
        )
        description_label.pack(
            fill="x",
            pady=(0, 18),
        )

    def build_settings_section(self):
        border, settings_card = self.create_card(self.page)

        border.pack(
            fill="x",
            pady=(0, 20),
        )

        self.add_section_heading(
            settings_card,
            "Password Settings",
            "Choose the password length and character types.",
        )

        length_row = tk.Frame(
            settings_card,
            bg=CARD_NAVY,
        )
        length_row.pack(
            fill="x",
            pady=(0, 15),
        )

        length_label = tk.Label(
            length_row,
            text="Password length",
            font=("Helvetica", 12, "bold"),
            bg=CARD_NAVY,
            fg=WHITE,
        )
        length_label.pack(side="left")

        self.length_box = tk.Spinbox(
            length_row,
            from_=8,
            to=64,
            textvariable=self.password_length,
            width=8,
            font=("Helvetica", 13, "bold"),
            bg=INPUT_BG,
            fg=INPUT_TEXT,
            buttonbackground=LIGHT_NAVY,
            relief="flat",
            justify="center",
        )
        self.length_box.pack(
            side="right",
            ipady=5,
        )

        line = tk.Frame(
            settings_card,
            bg=BORDER,
            height=1,
        )
        line.pack(
            fill="x",
            pady=(0, 15),
        )

        checkbox_area = tk.Frame(
            settings_card,
            bg=CARD_NAVY,
        )
        checkbox_area.pack(fill="x")

        self.add_checkbox(
            checkbox_area,
            "Include uppercase letters",
            self.use_uppercase,
        )

        self.add_checkbox(
            checkbox_area,
            "Include lowercase letters",
            self.use_lowercase,
        )

        self.add_checkbox(
            checkbox_area,
            "Include numbers",
            self.use_numbers,
        )

        self.add_checkbox(
            checkbox_area,
            "Include symbols",
            self.use_symbols,
        )

        self.add_checkbox(
            checkbox_area,
            "Remove confusing characters: 0, O, 1, l, I",
            self.remove_confusing_chars,
        )

    def add_checkbox(self, parent, text, variable):
        checkbox = tk.Checkbutton(
            parent,
            text=text,
            variable=variable,
            font=("Helvetica", 11),
            bg=CARD_NAVY,
            fg=WHITE,
            activebackground=CARD_NAVY,
            activeforeground=WHITE,
            selectcolor=LIGHT_NAVY,
            highlightthickness=0,
            anchor="w",
            cursor="hand2",
        )
        checkbox.pack(
            fill="x",
            pady=6,
        )

    def build_main_buttons(self):
        button_area = tk.Frame(
            self.page,
            bg=NAVY,
        )
        button_area.pack(
            pady=(0, 20),
        )

        generate_button = self.make_button(
            button_area,
            text="Generate Password",
            command=self.generate_password,
            normal_color=BLUE,
            hover_color=DARK_BLUE,
            button_width=220,
            bold=True,
        )
        generate_button.grid(
            row=0,
            column=0,
            padx=8,
        )

        reset_button = self.make_button(
            button_area,
            text="Reset Settings",
            command=self.reset_app,
            normal_color=LIGHT_NAVY,
            hover_color=BORDER,
            button_width=170,
        )
        reset_button.grid(
            row=0,
            column=1,
            padx=8,
        )

        about_button = self.make_button(
            button_area,
            text="About",
            command=self.show_about,
            normal_color=LIGHT_NAVY,
            hover_color=BORDER,
            button_width=120,
        )
        about_button.grid(
            row=0,
            column=2,
            padx=8,
        )

    def draw_rounded_box(
        self,
        canvas,
        x1,
        y1,
        x2,
        y2,
        radius,
        color,
        tag,
    ):
        canvas.create_arc(
            x1,
            y1,
            x1 + radius * 2,
            y1 + radius * 2,
            start=90,
            extent=90,
            fill=color,
            outline=color,
            tags=tag,
        )

        canvas.create_arc(
            x2 - radius * 2,
            y1,
            x2,
            y1 + radius * 2,
            start=0,
            extent=90,
            fill=color,
            outline=color,
            tags=tag,
        )

        canvas.create_arc(
            x1,
            y2 - radius * 2,
            x1 + radius * 2,
            y2,
            start=180,
            extent=90,
            fill=color,
            outline=color,
            tags=tag,
        )

        canvas.create_arc(
            x2 - radius * 2,
            y2 - radius * 2,
            x2,
            y2,
            start=270,
            extent=90,
            fill=color,
            outline=color,
            tags=tag,
        )

        canvas.create_rectangle(
            x1 + radius,
            y1,
            x2 - radius,
            y2,
            fill=color,
            outline=color,
            tags=tag,
        )

        canvas.create_rectangle(
            x1,
            y1 + radius,
            x2,
            y2 - radius,
            fill=color,
            outline=color,
            tags=tag,
        )

    def make_button(
        self,
        parent,
        text,
        command,
        normal_color,
        hover_color,
        button_width,
        bold=False,
    ):
        button_height = 48
        corner_radius = 14

        button_canvas = tk.Canvas(
            parent,
            width=button_width,
            height=button_height,
            bg=parent.cget("bg"),
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )

        self.draw_rounded_box(
            button_canvas,
            2,
            2,
            button_width - 2,
            button_height - 2,
            corner_radius,
            normal_color,
            "button_background",
        )

        font_weight = "bold" if bold else "normal"

        button_canvas.create_text(
            button_width / 2,
            button_height / 2,
            text=text,
            fill=WHITE,
            font=("Helvetica", 11, font_weight),
            tags="button_text",
        )

        def show_hover_color(event=None):
            button_canvas.itemconfig(
                "button_background",
                fill=hover_color,
                outline=hover_color,
            )

        def show_normal_color(event=None):
            button_canvas.itemconfig(
                "button_background",
                fill=normal_color,
                outline=normal_color,
            )

        def run_command(event=None):
            command()

        button_canvas.bind(
            "<Enter>",
            show_hover_color,
        )

        button_canvas.bind(
            "<Leave>",
            show_normal_color,
        )

        button_canvas.bind(
            "<Button-1>",
            run_command,
        )

        return button_canvas

    def build_password_section(self):
        border, password_card = self.create_card(self.page)

        border.pack(
            fill="x",
            pady=(0, 20),
        )

        self.add_section_heading(
            password_card,
            "Generated Password",
            "Your new password will appear below.",
        )

        self.password_box = tk.Entry(
            password_card,
            textvariable=self.generated_password,
            font=("Courier", 16, "bold"),
            justify="center",
            bg=INPUT_BG,
            fg=INPUT_TEXT,
            insertbackground=INPUT_TEXT,
            relief="flat",
            bd=0,
        )
        self.password_box.pack(
            fill="x",
            ipady=13,
            pady=(0, 12),
        )

        self.password_box.bind(
            "<Key>",
            lambda event: "break",
        )

        password_details = tk.Frame(
            password_card,
            bg=CARD_NAVY,
        )
        password_details.pack(
            fill="x",
            pady=(0, 10),
        )

        length_text = tk.Label(
            password_details,
            textvariable=self.password_info,
            font=("Helvetica", 10),
            bg=CARD_NAVY,
            fg=LIGHT_TEXT,
        )
        length_text.pack(side="left")

        self.strength_text = tk.Label(
            password_details,
            textvariable=self.password_strength,
            font=("Helvetica", 11, "bold"),
            bg=CARD_NAVY,
            fg=LIGHT_TEXT,
        )
        self.strength_text.pack(side="right")

        self.strength_bar_area = tk.Canvas(
            password_card,
            height=12,
            bg=LIGHT_NAVY,
            highlightthickness=0,
        )
        self.strength_bar_area.pack(
            fill="x",
            pady=(0, 15),
        )

        self.strength_bar = self.strength_bar_area.create_rectangle(
            0,
            0,
            0,
            12,
            fill=LIGHT_TEXT,
            outline="",
        )

        copy_button = self.make_button(
            password_card,
            text="Copy Password",
            command=self.copy_password,
            normal_color=BLUE,
            hover_color=DARK_BLUE,
            button_width=180,
            bold=True,
        )
        copy_button.pack()

    def build_history_section(self):
        border, history_card = self.create_card(self.page)

        border.pack(
            fill="x",
            pady=(0, 20),
        )

        self.add_section_heading(
            history_card,
            "Last 5 Generated Passwords",
            "The newest passwords are shown with the date and time.",
        )

        self.history_box = tk.Listbox(
            history_card,
            font=("Courier", 11),
            height=8,
            bg=LIGHT_NAVY,
            fg=WHITE,
            selectbackground=BLUE,
            selectforeground=WHITE,
            relief="flat",
            bd=0,
            highlightthickness=0,
        )
        self.history_box.pack(
            fill="x",
            ipady=8,
            pady=(0, 12),
        )

        clear_button = self.make_button(
            history_card,
            text="Clear History",
            command=self.clear_history,
            normal_color=LIGHT_NAVY,
            hover_color=RED,
            button_width=150,
        )
        clear_button.pack()

    def build_footer(self):
        footer = tk.Label(
            self.page,
            text=(
                "Built with Python, Tkinter, Secrets and Pyperclip\n"
                "Press Enter to generate a password"
            ),
            font=("Helvetica", 9),
            bg=NAVY,
            fg=LIGHT_TEXT,
            justify="center",
        )
        footer.pack(pady=(0, 20))

    def generate_password(self):
        try:
            length = int(self.password_length.get())

        except (ValueError, tk.TclError):
            messagebox.showerror(
                "Invalid Length",
                "Please enter a valid whole number.",
            )
            return

        if length < 8:
            messagebox.showerror(
                "Invalid Length",
                "The password must contain at least 8 characters.",
            )
            return

        if length > 64:
            messagebox.showerror(
                "Invalid Length",
                "The password cannot contain more than 64 characters.",
            )
            return

        character_groups = []

        uppercase_letters = string.ascii_uppercase
        lowercase_letters = string.ascii_lowercase
        numbers = string.digits
        symbols = string.punctuation

        if self.remove_confusing_chars.get():
            confusing_chars = "0O1lI"

            uppercase_letters = self.remove_characters(
                uppercase_letters,
                confusing_chars,
            )

            lowercase_letters = self.remove_characters(
                lowercase_letters,
                confusing_chars,
            )

            numbers = self.remove_characters(
                numbers,
                confusing_chars,
            )

        if self.use_uppercase.get():
            character_groups.append(uppercase_letters)

        if self.use_lowercase.get():
            character_groups.append(lowercase_letters)

        if self.use_numbers.get():
            character_groups.append(numbers)

        if self.use_symbols.get():
            character_groups.append(symbols)

        if len(character_groups) < 2:
            messagebox.showerror(
                "Character Types Required",
                "Please select at least two character types.",
            )
            return

        password_chars = []

        for group in character_groups:
            password_chars.append(
                secrets.choice(group)
            )

        all_characters = "".join(character_groups)
        spaces_left = length - len(password_chars)

        for _ in range(spaces_left):
            password_chars.append(
                secrets.choice(all_characters)
            )

        secrets.SystemRandom().shuffle(password_chars)

        new_password = "".join(password_chars)

        self.generated_password.set(new_password)

        self.password_info.set(
            f"Password length: {len(new_password)} characters"
        )

        self.show_password_strength(
            new_password,
            len(character_groups),
        )

        self.save_password(new_password)

    def remove_characters(
        self,
        characters,
        characters_to_remove,
    ):
        cleaned_characters = ""

        for character in characters:
            if character not in characters_to_remove:
                cleaned_characters += character

        return cleaned_characters

    def show_password_strength(
        self,
        password,
        selected_group_count,
    ):
        length = len(password)

        if length >= 16 and selected_group_count == 4:
            strength = "Strong"
            strength_color = GREEN
            bar_size = 1.0

        elif length >= 12 and selected_group_count >= 3:
            strength = "Medium"
            strength_color = ORANGE
            bar_size = 0.65

        else:
            strength = "Weak"
            strength_color = RED
            bar_size = 0.35

        self.password_strength.set(
            f"Strength: {strength}"
        )

        self.strength_text.config(
            fg=strength_color
        )

        self.root.update_idletasks()

        full_width = self.strength_bar_area.winfo_width()
        current_width = full_width * bar_size

        self.strength_bar_area.coords(
            self.strength_bar,
            0,
            0,
            current_width,
            12,
        )

        self.strength_bar_area.itemconfig(
            self.strength_bar,
            fill=strength_color,
        )

    def copy_password(self):
        password = self.generated_password.get()

        if password == "":
            messagebox.showwarning(
                "No Password",
                "Generate a password before copying.",
            )
            return

        try:
            pyperclip.copy(password)

            messagebox.showinfo(
                "Copied",
                "The password has been copied.",
            )

        except pyperclip.PyperclipException:
            messagebox.showerror(
                "Clipboard Error",
                "The password could not be copied.",
            )

    def save_password(self, password):
        date_created = datetime.now().strftime(
            "%d %b %Y, %I:%M:%S %p"
        )

        password_record = {
            "password": password,
            "date": date_created,
        }

        self.saved_passwords.insert(
            0,
            password_record,
        )

        if len(self.saved_passwords) > MAX_HISTORY:
            self.saved_passwords.pop()

        self.update_history_box()

    def update_history_box(self):
        self.history_box.delete(
            0,
            tk.END,
        )

        for number, password_record in enumerate(
            self.saved_passwords,
            start=1,
        ):
            password = password_record["password"]
            date_created = password_record["date"]

            history_text = (
                f"{number}. {password}    |    {date_created}"
            )

            self.history_box.insert(
                tk.END,
                history_text,
            )

    def clear_history(self):
        if len(self.saved_passwords) == 0:
            messagebox.showinfo(
                "History Empty",
                "There are no saved passwords to clear.",
            )
            return

        should_clear = messagebox.askyesno(
            "Clear History",
            "Are you sure you want to clear the password history?",
        )

        if should_clear:
            self.saved_passwords.clear()
            self.update_history_box()

    def reset_app(self):
        self.password_length.set(12)
        self.use_uppercase.set(True)
        self.use_lowercase.set(True)
        self.use_numbers.set(True)
        self.use_symbols.set(True)
        self.remove_confusing_chars.set(False)

        self.generated_password.set("")
        self.password_strength.set("Not generated")
        self.password_info.set(
            "Password length: 0 characters"
        )

        self.strength_text.config(
            fg=LIGHT_TEXT
        )

        self.strength_bar_area.coords(
            self.strength_bar,
            0,
            0,
            0,
            12,
        )

    def show_about(self):
        messagebox.showinfo(
            "About",
            (
                "Secure Password Generator\n\n"
                "Created by John Eseneh Obhiebo\n"
                "Python Programming Internship Project\n"
                "Oasis Infobyte\n\n"
                "Built with Python, Tkinter, Secrets "
                "and Pyperclip."
            ),
        )


def start_app():
    root = tk.Tk()
    PasswordGenerator(root)
    root.mainloop()


if __name__ == "__main__":
    start_app()