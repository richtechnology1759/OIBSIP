# SkyCast Weather

An advanced desktop weather application created for the Oasis Infobyte Python Programming Internship.

## Internship Task

- Track: Python Programming
- Task: Task 4 — Basic Weather App
- Tier: Advanced

## Features

- Tkinter graphical interface
- Search by city name or ZIP code
- Current temperature in Celsius or Fahrenheit
- Humidity, weather description, wind, pressure, visibility, sunrise, and sunset
- OpenWeather condition icons
- Next-six-hours panel using three-hour forecast points
- Five-day forecast
- Celsius/Fahrenheit toggle
- Automatic city detection from the public IP address
- Last five searches
- Input validation
- GUI error messages
- Timeout, invalid-key, city-not-found, rate-limit, and server-error handling
- Background requests so the interface remains responsive
- Local API-key storage excluded from GitHub

## Installation

```bash
python3 -m pip install -r requirements.txt
```

## API Key

1. Create a free OpenWeather account.
2. Copy your API key.
3. Run the app.
4. Paste the key into the API field.
5. Click **Save Key**.

The key is saved locally in `config.json`. This file is ignored by Git.

A new OpenWeather key may require some time before it becomes active.

## Run

```bash
python3 weather_app.py
```

## Files

```text
Python-Task4-WeatherApp
├── weather_app.py
├── README.md
├── requirements.txt
├── .gitignore
└── config.example.json
```

The application creates these local files:

- `config.json`
- `search_history.json`

Both are excluded from GitHub.

## Privacy

- Searches are sent to OpenWeather.
- Automatic location uses ipinfo.io and the public IP address.
- The API key and search history remain in local files.
- No precise GPS location, passwords, or personal accounts are collected.

## Author

John Eseneh Obhiebo
