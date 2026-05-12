"""
pipeline/weather_api.py  —  Member 4 | Data & Integration
==========================================================
Fetches 72-hour hourly weather forecasts from Open-Meteo
(https://open-meteo.com/).

WHY Open-Meteo?
  • 100 % free and open-source — no API key needed.
  • Hourly resolution up to 16 days ahead.
  • Variables: temperature, humidity, wind speed, precipitation.
  • GDPR-compliant, no account required.

Public interface
----------------
  fetch_weather()          → pd.DataFrame  (live from API)
  load_cached_weather()    → pd.DataFrame  (from JSON cache)
  get_weather_dataframe()  → pd.DataFrame  (cache-first, then live)
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd
import requests

# ── project config ────────────────────────────────────────────────────────────
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import (
    WEATHER_API_BASE,
    WEATHER_CITY_LAT,
    WEATHER_CITY_LON,
    WEATHER_CACHE_FILE,
    WEATHER_HOURLY_VARS,
    FORECAST_HORIZON_H,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────


def _build_params(lat: float, lon: float) -> dict:
    """Construct Open-Meteo query-string parameters."""
    return {
        "latitude": lat,
        "longitude": lon,
        "hourly": ",".join(WEATHER_HOURLY_VARS),
        "forecast_days": 4,  # gives ≥ 72 h of hourly data
        "timezone": "Asia/Kolkata",
    }


def _parse_response(weather_json: dict) -> pd.DataFrame:
    """
    Flatten the Open-Meteo hourly payload into a tidy DataFrame.

    Columns produced
    ----------------
    timestamp           datetime64[ns, Asia/Kolkata]
    temperature_2m      float  (°C)
    relativehumidity_2m float  (%)
    windspeed_10m       float  (km/h)
    precipitation       float  (mm)
    """
    hourly = weather_json.get("hourly", {})
    if not hourly:
        raise ValueError("Unexpected API response shape — 'hourly' key missing.")

    df = pd.DataFrame(hourly)
    df.rename(columns={"time": "timestamp"}, inplace=True)
    df["timestamp"] = pd.to_datetime(df["timestamp"], format="ISO8601")

    # Keep only the first FORECAST_HORIZON_H rows (72 h)
    df = df.head(FORECAST_HORIZON_H).reset_index(drop=True)

    # Round numeric columns to 2 dp for cleanliness
    num_cols = [c for c in df.columns if c != "timestamp"]
    df[num_cols] = df[num_cols].round(2)

    log.info(
        "Parsed %d rows of weather data (%.0f hours).", len(df), FORECAST_HORIZON_H
    )
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────


def fetch_weather(
    lat: float = WEATHER_CITY_LAT,
    lon: float = WEATHER_CITY_LON,
    cache: bool = True,
) -> pd.DataFrame:
    """
    Fetch a 72-hour hourly weather forecast from Open-Meteo and
    (optionally) write it to the local JSON cache.

    Parameters
    ----------
    lat, lon : float
        Geographic coordinates of the target city.
    cache : bool
        If True, persist the raw JSON response to WEATHER_CACHE_FILE.

    Returns
    -------
    pd.DataFrame
        72-row DataFrame with columns:
        timestamp, temperature_2m, relativehumidity_2m,
        windspeed_10m, precipitation
    """
    params = _build_params(lat, lon)
    endpoint = WEATHER_API_BASE

    log.info("Fetching weather from Open-Meteo (lat=%.4f, lon=%.4f)…", lat, lon)
    try:
        response = requests.get(endpoint, params=params, timeout=15)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        raise RuntimeError("Open-Meteo request timed out after 15 s.")
    except requests.exceptions.HTTPError as exc:
        raise RuntimeError(f"Open-Meteo HTTP error: {exc}") from exc
    except requests.exceptions.ConnectionError as exc:
        raise RuntimeError(f"Network error reaching Open-Meteo: {exc}") from exc

    weather_json: dict = response.json()

    if cache:
        _write_cache(weather_json)

    return _parse_response(weather_json)


def _write_cache(weather_json: dict) -> None:
    """Persist raw JSON to disk with a fetched_at timestamp."""
    cache_path = Path(WEATHER_CACHE_FILE)
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "fetched_at": datetime.now(tz=timezone.utc).isoformat(),
        "data": weather_json,
    }
    cache_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    log.info("Weather cache written → %s", cache_path)


def load_cached_weather() -> Optional[pd.DataFrame]:
    """
    Load the most recent weather data from the local JSON cache.

    Returns
    -------
    pd.DataFrame | None
        Parsed DataFrame, or None if the cache does not exist.
    """
    cache_path = Path(WEATHER_CACHE_FILE)
    if not cache_path.exists():
        log.warning("No weather cache found at %s.", cache_path)
        return None

    payload = json.loads(cache_path.read_text(encoding="utf-8"))
    fetched_at = payload.get("fetched_at", "unknown")
    weather_json = payload.get("data", {})

    log.info("Loaded weather cache (fetched %s).", fetched_at)
    return _parse_response(weather_json)


def get_weather_dataframe(
    lat: float = WEATHER_CITY_LAT,
    lon: float = WEATHER_CITY_LON,
    force_refresh: bool = False,
) -> pd.DataFrame:
    """
    Cache-first weather loader.

    Tries the local cache first to avoid unnecessary API calls.
    Falls back to a live fetch if the cache is missing or
    force_refresh=True.

    Parameters
    ----------
    lat, lon : float
        Target coordinates (defaults to Chennai from config).
    force_refresh : bool
        Bypass the cache and always fetch from the API.

    Returns
    -------
    pd.DataFrame
        72-row weather DataFrame.
    """
    if not force_refresh:
        cached = load_cached_weather()
        if cached is not None:
            return cached

    return fetch_weather(lat=lat, lon=lon, cache=True)


# ─────────────────────────────────────────────────────────────────────────────
# CLI smoke-test
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print(" PowerPulse AI — weather_api.py smoke test")
    print("=" * 60)

    df = fetch_weather()
    print(f"\nRows returned : {len(df)}")
    print(f"Columns       : {list(df.columns)}")
    print("\nFirst 5 rows:")
    print(df.head().to_string(index=False))
    print("\nLast 5 rows:")
    print(df.tail().to_string(index=False))
    print("\n✓  weather_api.py works correctly.")
