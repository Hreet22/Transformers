# config.py  —  PowerPulse AI  |  Team TRANSFORMERS  v1.0
import os
from dotenv import load_dotenv

load_dotenv()

# ── Project identity ──────────────────────────────────────────────
PROJECT_NAME = "PowerPulse AI"
TEAM_NAME = "TRANSFORMERS"
MEMBER_1_NAME = "Hreet Bansal"  # from Member 1
VERSION = "1.0.0"

# ── Data simulation parameters ────────────────────────────────────
NUM_TRANSFORMERS = 50  # simulated transformer units
SIM_HOURS = 8760  # 1 year of hourly records
SIM_START_DATE = "2024-01-01 00:00:00"
LOAD_MIN_KVA = 50.0  # minimum transformer load
LOAD_MAX_KVA = 500.0  # maximum transformer load
CAPACITY_KVA = 400.0  # rated capacity per unit
FAULT_RATE = 0.02  # 2% probability of fault per row
TEMP_MIN_C = 15.0  # ambient temperature range
TEMP_MAX_C = 42.0

# ── Forecasting (Prophet) ─────────────────────────────────────────
FORECAST_HORIZON_H = 72  # 72-hour look-ahead
FORECAST_FREQ = "h"  # hourly cadence (pandas 2.2+)
PROPHET_SEASONALITY = "multiplicative"
CHANGEPOINT_SCALE = 0.05

# ── Risk scoring thresholds ───────────────────────────────────────
RISK_LOW_PCT = 0.70  # load/capacity < 70%  → LOW
RISK_MED_PCT = 0.85  # 70–85%               → MEDIUM
RISK_HIGH_PCT = 1.00  # > 85%                → HIGH / CRITICAL

# ── PuLP optimisation ─────────────────────────────────────────────
PEAK_HOUR_START = 18  # 18:00
PEAK_HOUR_END = 22  # 22:00
SHIFTABLE_LOADS = ["ev_charging", "industrial_cooling"]
MAX_SHIFT_KVA = 80.0  # max load that can be redistributed
SOLVER_TIMEOUT_S = 30

# ── Weather API (Open-Meteo — no key needed) ──────────────────────
WEATHER_API_BASE = "https://api.open-meteo.com/v1/forecast"
WEATHER_CITY_LAT = 12.9716  # Bengaluru
WEATHER_CITY_LON = 77.5946
WEATHER_CACHE_FILE = "data/weather/weather_cache.json"
WEATHER_HOURLY_VARS = [
    "temperature_2m",
    "relativehumidity_2m",
    "windspeed_10m",
    "precipitation",
]

# ── OpenWeather API (kept for compatibility) ──────────────────────
OW_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
OW_BASE_URL = "https://api.openweathermap.org/data/2.5/forecast"
OW_CITY = "Chennai,IN"
OW_UNITS = "metric"
OW_CACHE_FILE = "data/weather/ow_cache.json"

# ── Streamlit / Dashboard ─────────────────────────────────────────
DASHBOARD_TITLE = "PowerPulse AI — Load Intelligence"
MAP_CENTER_LAT = 12.9716  # Bengaluru
MAP_CENTER_LON = 77.5946
HEATMAP_RADIUS = 15
ALERT_MAX_ROWS = 100  # rows shown in alert log widget
REFRESH_INTERVAL_S = 30

# ── Paths ─────────────────────────────────────────────────────────
DATA_RAW_DIR = "data/raw/"
DATA_PROC_DIR = "data/processed/"
DATA_SIM_DIR = "data/simulated/"
MODEL_PATH = "models/prophet_model.pkl"
MODEL_CONFIG_PATH = "models/model_config.yaml"
