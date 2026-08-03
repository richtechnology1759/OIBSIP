import io
import json
import threading
import tkinter as tk
from datetime import datetime, timezone
from pathlib import Path
from tkinter import messagebox

import requests
from PIL import Image, ImageTk

APP_DIR = Path(__file__).resolve().parent
CONFIG_FILE = APP_DIR / "config.json"
HISTORY_FILE = APP_DIR / "search_history.json"

CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"
ICON_URL = "https://openweathermap.org/img/wn/{code}@2x.png"
IP_URL = "https://ipinfo.io/json"

NAVY = "#0F172A"
CARD = "#1E293B"
LIGHT = "#334155"
BLUE = "#2563EB"
WHITE = "#F8FAFC"
MUTED = "#CBD5E1"
RED = "#F87171"
GREEN = "#4ADE80"
YELLOW = "#FACC15"


class WeatherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SkyCast Weather")
        self.root.geometry("1120x860")
        self.root.minsize(900, 680)
        self.root.configure(bg=NAVY)

        self.api_key = ""
        self.unit = "metric"
        self.icon_images = []
        self.history = []

        self.city = tk.StringVar()
        self.api_key_text = tk.StringVar()
        self.location_text = tk.StringVar(value="Search for a city")
        self.temperature_text = tk.StringVar(value="--°")
        self.condition_text = tk.StringVar(value="Your weather will appear here")
        self.feels_text = tk.StringVar(value="Feels like --")
        self.humidity_text = tk.StringVar(value="--%")
        self.wind_text = tk.StringVar(value="--")
        self.pressure_text = tk.StringVar(value="-- hPa")
        self.visibility_text = tk.StringVar(value="-- km")
        self.sunrise_text = tk.StringVar(value="--")
        self.sunset_text = tk.StringVar(value="--")
        self.error_text = tk.StringVar()
        self.status_text = tk.StringVar(value="Ready")

        self.load_saved_data()
        self.build_scroll_area()
        self.build_ui()
        self.show_history()
        self.root.bind("<Return>", lambda event: self.search_weather())

    def load_saved_data(self):
        try:
            if CONFIG_FILE.exists():
                data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                self.api_key = data.get("api_key", "").strip()
                self.api_key_text.set(self.api_key)
        except (OSError, json.JSONDecodeError):
            pass

        try:
            if HISTORY_FILE.exists():
                data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    self.history = data[:5]
        except (OSError, json.JSONDecodeError):
            pass

    def build_scroll_area(self):
        """Create the scrollable page and enable mouse, trackpad, and keyboard scrolling."""
        container = tk.Frame(self.root, bg=NAVY)
        container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(
            container,
            bg=NAVY,
            highlightthickness=0,
            borderwidth=0,
        )
        self.canvas.pack(side="left", fill="both", expand=True)

        self.scrollbar = tk.Scrollbar(
            container,
            orient="vertical",
            command=self.canvas.yview,
        )
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.page = tk.Frame(self.canvas, bg=NAVY, padx=32, pady=26)
        self.page_window = self.canvas.create_window(
            (0, 0),
            window=self.page,
            anchor="nw",
        )

        self.page.bind("<Configure>", self.update_scroll_region)
        self.canvas.bind("<Configure>", self.resize_scroll_page)

        # Mouse wheel and trackpad support for macOS and Windows.
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)

        # Linux wheel events.
        self.canvas.bind_all("<Button-4>", self.on_linux_scroll_up)
        self.canvas.bind_all("<Button-5>", self.on_linux_scroll_down)

        # Keyboard scrolling.
        self.root.bind("<Up>", lambda event: self.scroll_units(-2))
        self.root.bind("<Down>", lambda event: self.scroll_units(2))
        self.root.bind("<Prior>", lambda event: self.scroll_pages(-1))
        self.root.bind("<Next>", lambda event: self.scroll_pages(1))
        self.root.bind("<Home>", lambda event: self.canvas.yview_moveto(0))
        self.root.bind("<End>", lambda event: self.canvas.yview_moveto(1))

        # Give the canvas focus when the pointer enters it so keyboard scrolling works naturally.
        self.canvas.bind("<Enter>", lambda event: self.canvas.focus_set())

    def update_scroll_region(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def resize_scroll_page(self, event):
        self.canvas.itemconfigure(self.page_window, width=event.width)
        self.update_scroll_region()

    def on_mousewheel(self, event):
        """Handle mouse wheel and trackpad scrolling at a comfortable speed."""
        if event.delta == 0:
            return "break"

        direction = -1 if event.delta > 0 else 1

        # Scroll one small step per wheel/trackpad event.
        # This prevents macOS trackpads from jumping from top to bottom.
        self.canvas.yview_scroll(direction, "units")
        return "break"

    def on_linux_scroll_up(self, event):
        self.canvas.yview_scroll(-2, "units")
        return "break"

    def on_linux_scroll_down(self, event):
        self.canvas.yview_scroll(2, "units")
        return "break"

    def scroll_units(self, amount):
        self.canvas.yview_scroll(amount, "units")
        return "break"

    def scroll_pages(self, amount):
        self.canvas.yview_scroll(amount, "pages")
        return "break"

    def build_ui(self):
        header = tk.Frame(self.page, bg=NAVY)
        header.pack(fill="x")

        title_area = tk.Frame(header, bg=NAVY)
        title_area.pack(expand=True)

        tk.Label(
            title_area,
            text="SkyCast Weather",
            font=("Helvetica", 29, "bold"),
            bg=NAVY,
            fg=WHITE,
        ).pack()

        tk.Label(
            title_area,
            text="Check today's weather and plan the days ahead.",
            font=("Helvetica", 12),
            bg=NAVY,
            fg=MUTED,
        ).pack(pady=(6, 0))

        self.settings_button = self.make_button(
            header,
            "Settings",
            self.toggle_settings,
            LIGHT,
        )
        self.settings_button.place(relx=1.0, rely=0.0, anchor="ne")

        tk.Frame(self.page, bg=NAVY, height=20).pack()

        self.build_api_card()
        self.build_search_card()
        self.build_current_card()
        self.build_forecast_card(
            "Hourly Forecast",
            "Weather expected over the next six hours.",
            "hourly",
        )
        self.build_forecast_card(
            "5-Day Forecast",
            "A simple look at the weather for the next five days.",
            "daily",
        )

        footer = tk.Frame(self.page, bg=NAVY)
        footer.pack(fill="x", pady=(0, 15))

        tk.Label(
            footer,
            text="Weather data: OpenWeather",
            font=("Helvetica", 9),
            bg=NAVY,
            fg=MUTED,
        ).pack(side="left")

        self.status_label = tk.Label(
            footer,
            textvariable=self.status_text,
            font=("Helvetica", 9, "bold"),
            bg=NAVY,
            fg=MUTED,
        )
        self.status_label.pack(side="right")

    def make_card(self, title, description, hidden=False):
        border = tk.Frame(self.page, bg="#475569", padx=1, pady=1)
        if not hidden:
            border.pack(fill="x", pady=(0, 17))

        card = tk.Frame(border, bg=CARD, padx=22, pady=20)
        card.pack(fill="both", expand=True)

        tk.Label(
            card,
            text=title,
            font=("Helvetica", 16, "bold"),
            bg=CARD,
            fg=WHITE,
            anchor="w",
        ).pack(fill="x")

        tk.Label(
            card,
            text=description,
            font=("Helvetica", 10),
            bg=CARD,
            fg=MUTED,
            anchor="w",
        ).pack(fill="x", pady=(4, 15))
        return border, card

    def make_button(self, parent, text, command, color=BLUE):
        button = tk.Label(
            parent,
            text=text,
            font=("Helvetica", 10, "bold"),
            bg=color,
            fg=WHITE,
            padx=14,
            pady=10,
            cursor="hand2",
        )
        button.bind("<Button-1>", lambda event: command())
        return button

    def build_api_card(self):
        self.settings_border, card = self.make_card(
            "App Settings",
            "Add or update the OpenWeather API key used by this app.",
            hidden=True,
        )

        status_row = tk.Frame(card, bg=CARD)
        status_row.pack(fill="x", pady=(0, 12))

        self.api_status_label = tk.Label(
            status_row,
            text="API key saved" if self.api_key else "API key not set",
            font=("Helvetica", 10, "bold"),
            bg=CARD,
            fg=GREEN if self.api_key else YELLOW,
        )
        self.api_status_label.pack(side="left")

        tk.Label(
            status_row,
            text="The key stays on this computer and is excluded from Git.",
            font=("Helvetica", 9),
            bg=CARD,
            fg=MUTED,
        ).pack(side="left", padx=(12, 0))

        row = tk.Frame(card, bg=CARD)
        row.pack(fill="x")

        self.api_entry = tk.Entry(
            row,
            textvariable=self.api_key_text,
            show="•",
            font=("Helvetica", 11),
            bg=WHITE,
            fg=NAVY,
            relief="flat",
        )
        self.api_entry.pack(side="left", fill="x", expand=True, ipady=9)

        self.make_button(row, "Save", self.save_api_key).pack(side="left", padx=(10, 0))

        self.reveal_button = self.make_button(
            row,
            "Reveal",
            self.toggle_key,
            LIGHT,
        )
        self.reveal_button.pack(side="left", padx=(8, 0))

    def build_search_card(self):
        self.search_border, card = self.make_card(
            "Search a City",
            "Enter a city or ZIP code, or use your approximate location.",
        )

        row = tk.Frame(card, bg=CARD)
        row.pack(fill="x")

        self.city_entry = tk.Entry(
            row,
            textvariable=self.city,
            font=("Helvetica", 12),
            bg=WHITE,
            fg=NAVY,
            relief="flat",
        )
        self.city_entry.pack(side="left", fill="x", expand=True, ipady=10)
        self.city_entry.focus_set()

        self.search_button = self.make_button(row, "Get Weather", self.search_weather)
        self.search_button.pack(side="left", padx=(10, 0))
        self.make_button(row, "Use My Location", self.use_location, LIGHT).pack(side="left", padx=(8, 0))

        self.unit_button = self.make_button(row, "Switch to °F", self.toggle_unit, LIGHT)
        self.unit_button.pack(side="left", padx=(8, 0))

        self.history_frame = tk.Frame(card, bg=CARD)
        self.history_frame.pack(fill="x", pady=(14, 0))

        tk.Label(
            self.history_frame,
            text="Recent searches",
            font=("Helvetica", 10, "bold"),
            bg=CARD,
            fg=MUTED,
        ).pack(side="left", padx=(0, 8))

        self.history_buttons = tk.Frame(self.history_frame, bg=CARD)
        self.history_buttons.pack(side="left")

        tk.Label(
            card,
            textvariable=self.error_text,
            font=("Helvetica", 10, "bold"),
            bg=CARD,
            fg=RED,
            anchor="w",
            wraplength=900,
        ).pack(fill="x", pady=(12, 0))

    def build_current_card(self):
        _, card = self.make_card(
            "Today's Weather",
            "Current weather details for the selected location.",
        )

        row = tk.Frame(card, bg=CARD)
        row.pack(fill="x")

        left = tk.Frame(row, bg=CARD)
        left.pack(side="left", fill="both", expand=True)

        tk.Label(
            left,
            textvariable=self.location_text,
            font=("Helvetica", 20, "bold"),
            bg=CARD,
            fg=WHITE,
            anchor="w",
        ).pack(fill="x")

        weather_row = tk.Frame(left, bg=CARD)
        weather_row.pack(fill="x", pady=(10, 0))

        self.main_icon = tk.Label(
            weather_row,
            text="☁",
            font=("Helvetica", 50),
            bg=CARD,
            fg=MUTED,
        )
        self.main_icon.pack(side="left")

        tk.Label(
            weather_row,
            textvariable=self.temperature_text,
            font=("Helvetica", 44, "bold"),
            bg=CARD,
            fg=WHITE,
        ).pack(side="left", padx=18)

        info = tk.Frame(weather_row, bg=CARD)
        info.pack(side="left")

        tk.Label(
            info,
            textvariable=self.condition_text,
            font=("Helvetica", 16, "bold"),
            bg=CARD,
            fg=WHITE,
            anchor="w",
        ).pack(anchor="w")

        tk.Label(
            info,
            textvariable=self.feels_text,
            font=("Helvetica", 11),
            bg=CARD,
            fg=MUTED,
        ).pack(anchor="w", pady=(5, 0))

        details = tk.Frame(row, bg=LIGHT, padx=18, pady=14)
        details.pack(side="right", fill="both", expand=True, padx=(24, 0))

        items = [
            ("Humidity", self.humidity_text),
            ("Wind", self.wind_text),
            ("Pressure", self.pressure_text),
            ("Visibility", self.visibility_text),
            ("Sunrise", self.sunrise_text),
            ("Sunset", self.sunset_text),
        ]

        for index, (name, variable) in enumerate(items):
            box = tk.Frame(details, bg=LIGHT)
            box.grid(row=index // 2, column=index % 2, sticky="ew", padx=8, pady=7)
            details.grid_columnconfigure(index % 2, weight=1)

            tk.Label(box, text=name, font=("Helvetica", 9, "bold"), bg=LIGHT, fg=MUTED).pack(anchor="w")
            tk.Label(box, textvariable=variable, font=("Helvetica", 12, "bold"), bg=LIGHT, fg=WHITE).pack(anchor="w")

    def build_forecast_card(self, title, description, section):
        _, card = self.make_card(title, description)
        frame = tk.Frame(card, bg=CARD)
        frame.pack(fill="x")

        if section == "hourly":
            self.hourly_frame = frame
        else:
            self.daily_frame = frame

        tk.Label(
            frame,
            text="Search for a city to view this forecast.",
            font=("Helvetica", 10),
            bg=CARD,
            fg=MUTED,
            pady=14,
        ).pack()

    def save_api_key(self):
        key = self.api_key_text.get().strip()

        if not key:
            messagebox.showwarning("Missing API Key", "Enter an OpenWeather API key.")
            return

        try:
            CONFIG_FILE.write_text(
                json.dumps({"api_key": key}, indent=4),
                encoding="utf-8",
            )
            self.api_key = key
            self.api_status_label.config(text="API key saved", fg=GREEN)
            self.set_status("API key saved locally.", GREEN)
            messagebox.showinfo(
                "Saved",
                "The API key was saved on this computer.",
            )
            self.hide_settings()
        except OSError as error:
            messagebox.showerror("Save Error", str(error))

    def toggle_key(self):
        hidden = bool(self.api_entry.cget("show"))
        self.api_entry.config(show="" if hidden else "•")
        self.reveal_button.config(text="Hide" if hidden else "Reveal")

    def toggle_settings(self):
        if self.settings_border.winfo_manager():
            self.hide_settings()
        else:
            self.settings_border.pack(
                fill="x",
                pady=(0, 17),
                before=self.search_border,
            )
            self.settings_button.config(text="Close Settings")

    def hide_settings(self):
        self.settings_border.pack_forget()
        self.settings_button.config(text="Settings")
        self.api_entry.config(show="•")
        self.reveal_button.config(text="Reveal")

    def search_weather(self):
        city = self.city.get().strip()
        key = self.api_key_text.get().strip() or self.api_key

        if not city:
            self.show_error("Enter a city name or ZIP code.")
            return

        if not key:
            self.show_error("Enter and save your OpenWeather API key first.")
            return

        self.api_key = key
        self.error_text.set("")
        self.set_loading(True)

        threading.Thread(
            target=self.fetch_weather,
            args=(city, key),
            daemon=True,
        ).start()

    def fetch_weather(self, city, key):
        params = {"q": city, "appid": key, "units": self.unit}

        try:
            current_response = requests.get(CURRENT_URL, params=params, timeout=12)
            forecast_response = requests.get(FORECAST_URL, params=params, timeout=12)

            self.check_response(current_response)
            self.check_response(forecast_response)

            current_data = current_response.json()
            forecast_data = forecast_response.json()

            self.root.after(
                0,
                lambda: self.display_weather(current_data, forecast_data),
            )
        except requests.Timeout:
            self.root.after(0, lambda: self.finish_error("The request timed out. Check your internet connection."))
        except requests.ConnectionError:
            self.root.after(0, lambda: self.finish_error("A network connection could not be made."))
        except requests.RequestException as error:
            message = str(error)
            self.root.after(0, lambda message=message: self.finish_error(message))
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            self.root.after(0, lambda: self.finish_error("The weather service returned unexpected data."))

    def check_response(self, response):
        if response.status_code == 401:
            raise requests.RequestException("The API key is invalid or has not activated yet.")
        if response.status_code == 404:
            raise requests.RequestException("The city or ZIP code was not found.")
        if response.status_code == 429:
            raise requests.RequestException("The API request limit has been reached.")
        if response.status_code >= 500:
            raise requests.RequestException("The weather service is temporarily unavailable.")
        response.raise_for_status()

    def use_location(self):
        key = self.api_key_text.get().strip() or self.api_key

        if not key:
            self.show_error("Enter and save your OpenWeather API key first.")
            return

        self.error_text.set("")
        self.set_loading(True)
        threading.Thread(target=self.detect_location, args=(key,), daemon=True).start()

    def detect_location(self, key):
        try:
            response = requests.get(IP_URL, timeout=10)
            response.raise_for_status()
            city = response.json().get("city", "").strip()

            if not city:
                raise requests.RequestException("Your city could not be detected.")

            self.root.after(0, lambda: self.city.set(city))
            self.fetch_weather(city, key)
        except requests.RequestException as error:
            message = str(error)
            self.root.after(0, lambda message=message: self.finish_error(message))

    def display_weather(self, current, forecast):
        symbol = "°C" if self.unit == "metric" else "°F"
        wind_unit = "m/s" if self.unit == "metric" else "mph"
        city = current["name"]
        country = current.get("sys", {}).get("country", "")
        location = f"{city}, {country}" if country else city

        self.location_text.set(location)
        self.temperature_text.set(f"{round(current['main']['temp'])}{symbol}")
        self.condition_text.set(current["weather"][0]["description"].title())
        self.feels_text.set(f"Feels like {round(current['main']['feels_like'])}{symbol}")
        self.humidity_text.set(f"{current['main']['humidity']}%")
        self.wind_text.set(f"{current.get('wind', {}).get('speed', 0):.1f} {wind_unit}")
        self.pressure_text.set(f"{current['main']['pressure']} hPa")
        self.visibility_text.set(f"{current.get('visibility', 0) / 1000:.1f} km")

        offset = current.get("timezone", 0)
        self.sunrise_text.set(self.local_time(current.get("sys", {}).get("sunrise"), offset))
        self.sunset_text.set(self.local_time(current.get("sys", {}).get("sunset"), offset))

        self.load_main_icon(current["weather"][0].get("icon"))
        self.show_hourly(forecast.get("list", [])[:3])
        self.show_daily(forecast.get("list", []))
        self.add_history(city)

        self.set_loading(False)
        self.set_status(f"Updated for {location}", GREEN)

    def local_time(self, timestamp, offset):
        if not timestamp:
            return "--"

        local_timestamp = timestamp + offset
        return datetime.fromtimestamp(
            local_timestamp,
            tz=timezone.utc,
        ).strftime("%I:%M %p")

    def load_icon_image(self, code, size):
        """
        Download and resize an icon in a worker thread.

        This returns a PIL image only. Tkinter PhotoImage objects must be
        created on the main Tkinter thread to avoid macOS crashes.
        """
        if not code:
            return None

        try:
            response = requests.get(ICON_URL.format(code=code), timeout=8)
            response.raise_for_status()

            with Image.open(io.BytesIO(response.content)) as downloaded:
                image = downloaded.convert("RGBA")
                return image.resize((size, size), Image.Resampling.LANCZOS)

        except (requests.RequestException, OSError):
            return None

    def load_main_icon(self, code):
        def worker():
            pil_image = self.load_icon_image(code, 96)
            if pil_image is not None:
                self.root.after(
                    0,
                    lambda image=pil_image: self.set_main_icon(image),
                )

        threading.Thread(target=worker, daemon=True).start()

    def set_main_icon(self, pil_image):
        photo = ImageTk.PhotoImage(pil_image)
        self.icon_images = [photo]
        self.main_icon.config(image=photo, text="")

    def show_hourly(self, entries):
        self.clear_frame(self.hourly_frame)

        for column, entry in enumerate(entries):
            self.add_forecast_panel(
                self.hourly_frame,
                column,
                datetime.fromtimestamp(entry["dt"]).strftime("%I:%M %p"),
                entry,
            )

    def show_daily(self, entries):
        self.clear_frame(self.daily_frame)
        chosen = []
        used_dates = set()

        for entry in entries:
            day = datetime.fromtimestamp(entry["dt"]).date()
            if day in used_dates:
                continue

            same_day = [
                item for item in entries
                if datetime.fromtimestamp(item["dt"]).date() == day
            ]
            selected = min(
                same_day,
                key=lambda item: abs(datetime.fromtimestamp(item["dt"]).hour - 12),
            )
            chosen.append(selected)
            used_dates.add(day)

            if len(chosen) == 5:
                break

        for column, entry in enumerate(chosen):
            title = datetime.fromtimestamp(entry["dt"]).strftime("%a %d %b")
            self.add_forecast_panel(self.daily_frame, column, title, entry)

    def add_forecast_panel(self, parent, column, title, entry):
        parent.grid_columnconfigure(column, weight=1)

        panel = tk.Frame(parent, bg=LIGHT, padx=14, pady=15)
        panel.grid(row=0, column=column, sticky="nsew", padx=7, pady=3)

        tk.Label(panel, text=title, font=("Helvetica", 10, "bold"), bg=LIGHT, fg=WHITE).pack()

        icon_label = tk.Label(panel, text="☁", font=("Helvetica", 30), bg=LIGHT, fg=MUTED)
        icon_label.pack(pady=4)

        symbol = "°C" if self.unit == "metric" else "°F"
        tk.Label(
            panel,
            text=f"{round(entry['main']['temp'])}{symbol}",
            font=("Helvetica", 17, "bold"),
            bg=LIGHT,
            fg=WHITE,
        ).pack()

        tk.Label(
            panel,
            text=entry["weather"][0]["description"].title(),
            font=("Helvetica", 8),
            bg=LIGHT,
            fg=MUTED,
            wraplength=135,
        ).pack(pady=(4, 0))

        code = entry["weather"][0].get("icon")

        def worker():
            pil_image = self.load_icon_image(code, 60)
            if pil_image is not None:
                self.root.after(
                    0,
                    lambda image=pil_image, target=icon_label: self.set_small_icon(
                        target,
                        image,
                    ),
                )

        threading.Thread(target=worker, daemon=True).start()

    def set_small_icon(self, label, pil_image):
        if not label.winfo_exists():
            return

        photo = ImageTk.PhotoImage(pil_image)
        self.icon_images.append(photo)
        label.config(image=photo, text="")

    def clear_frame(self, frame):
        for widget in frame.winfo_children():
            widget.destroy()

    def toggle_unit(self):
        self.unit = "imperial" if self.unit == "metric" else "metric"
        text = "Switch to °C" if self.unit == "imperial" else "Switch to °F"
        self.unit_button.config(text=text)

        if self.city.get().strip():
            self.search_weather()

    def add_history(self, city):
        self.history = [item for item in self.history if item.lower() != city.lower()]
        self.history.insert(0, city)
        self.history = self.history[:5]

        try:
            HISTORY_FILE.write_text(json.dumps(self.history, indent=4), encoding="utf-8")
        except OSError:
            pass

        self.show_history()

    def show_history(self):
        for widget in self.history_buttons.winfo_children():
            widget.destroy()

        if not self.history:
            tk.Label(
                self.history_buttons,
                text="No searches yet",
                font=("Helvetica", 10),
                bg=CARD,
                fg=MUTED,
            ).pack(side="left")
            return

        for city in self.history:
            self.make_button(
                self.history_buttons,
                city,
                lambda selected=city: self.search_saved_city(selected),
                LIGHT,
            ).pack(side="left", padx=(0, 6))

    def search_saved_city(self, city):
        self.city.set(city)
        self.search_weather()

    def show_error(self, message):
        self.error_text.set(message)
        self.set_status("Unable to load weather.", RED)

    def finish_error(self, message):
        self.set_loading(False)
        self.show_error(message)

    def set_loading(self, loading):
        self.search_button.config(text="Loading..." if loading else "Get Weather")
        if loading:
            self.set_status("Loading weather data...", YELLOW)

    def set_status(self, message, color):
        self.status_text.set(message)
        self.status_label.config(fg=color)


def start_app():
    root = tk.Tk()
    WeatherApp(root)
    root.mainloop()


if __name__ == "__main__":
    start_app()