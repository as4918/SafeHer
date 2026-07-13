"""
config.py
----------
Central place for all app-wide settings.
Keeping config in ONE file makes the project easy to grade/read for hackathon judges
and easy for beginners to customize (change a color, change a DB path, etc.)
"""

import os
from dotenv import load_dotenv

# Load variables from a local .env file (if present) into the environment.
load_dotenv()

# ------------------------------------------------------------------
# GEMINI API CONFIG
# ------------------------------------------------------------------
def get_gemini_api_key():
    return os.getenv("GEMINI_API_KEY")


GEMINI_API_KEY = get_gemini_api_key()
GEMINI_MODEL_NAME = "gemini-1.5-flash"  # fast + cheap, good for a live demo

# ------------------------------------------------------------------
# LOCATION VALIDATION CONFIG (OpenStreetMap Nominatim via geopy)
# ------------------------------------------------------------------
# Nominatim is completely free and needs NO API key -- but its usage policy
# requires every app to identify itself with a descriptive User-Agent string.
# Customize this (ideally with your app name + a contact email) before
# deploying publicly: https://operations.osmfoundation.org/policies/nominatim/
NOMINATIM_USER_AGENT = os.getenv("NOMINATIM_USER_AGENT", "safeher_ai_hackathon_app")

# ------------------------------------------------------------------
# APP CONFIG
# ------------------------------------------------------------------
APP_NAME = "SafeHer AI"
APP_TAGLINE = "Your AI-powered personal safety companion 💜"
APP_ICON = "🛡️"

# ------------------------------------------------------------------
# DATABASE CONFIG
# ------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "safeher.db")

# ------------------------------------------------------------------
# DEMO / FALLBACK MODE
# ------------------------------------------------------------------
# If no Gemini API key is configured, the app still works end-to-end using
# rule-based fallback responses. This is critical for hackathon demos --
# judges' WiFi or a missing key should never crash the app.
DEMO_MODE = GEMINI_API_KEY is None

# STRICT_LOCATION_VALIDATION: when True, if OpenStreetMap/Nominatim can't verify
# a location (network error, no results) the location is REJECTED instead of
# silently scored anyway. Recommended to set STRICT_LOCATION_VALIDATION=true
# in your .env once you've confirmed geocoding works, so gibberish input can't
# get a fake score.
STRICT_LOCATION_VALIDATION = os.getenv("STRICT_LOCATION_VALIDATION", "false").lower() == "true"
