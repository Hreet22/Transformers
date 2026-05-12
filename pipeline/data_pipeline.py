"""
pipeline/data_pipeline.py  —  Member 4 | Data & Integration
============================================================
Joins the cleaned transformer-load data produced by Member 1
with the 72-hour weather forecast fetched by weather_api.py,
then emits a Prophet-ready DataFrame that the ML model
(Member 1) and the Risk Engine (Member 2) consume.

Public interface
----------------
  run_pipeline()           → dict[str, pd.DataFrame]
    Keys: "merged", "prophet", "weather"

  load_processed_load()    → pd.DataFrame   (load data from disk)
  merge_load_weather()     → pd.DataFrame   (joined frame)
  prepare_prophet_input()  → pd.DataFrame   (ds / y frame)
  save_pipeline_outputs()  → None           (writes Parquet files)
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import numpy as np

# ── project imports ───────────────────────────────────────────────────────────
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import (
    DATA_SIM_DIR,
    DATA_PROC_DIR,
    FORECAST_HORIZON_H,
    CAPACITY_KVA,
)
from pipeline.weather_api import get_weather_dataframe

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Column name constants  (single source of truth)
# ─────────────────────────────────────────────────────────────────────────────
COL_TIMESTAMP = "timestamp"
COL_LOAD = "load_kva"
COL_TEMP = "temperature_2m"
COL_HUMIDITY = "relativehumidity_2m"
COL_WIND = "windspeed_10m"
COL_PRECIP = "precipitation"
COL_FAULT = "fault_flag"
COL_UNIT = "transformer_id"

FEATURE_COLS = [COL_LOAD, COL_TEMP, COL_HUMIDITY, COL_WIND, COL_PRECIP]
TARGET_COL = COL_LOAD  # Prophet y-column


# ─────────────────────────────────────────────────────────────────────────────
# Step 1 — Load processed transformer data from disk
# ─────────────────────────────────────────────────────────────────────────────


def load_processed_load(path: str | None = None) -> pd.DataFrame:
    """
    Read the cleaned, processed load CSV produced by Member 1.

    Falls back to the simulated CSV if no processed file exists yet,
    so Member 4 can develop and test independently.

    Parameters
    ----------
    path : str | None
        Explicit file path.  If None, searches DATA_PROC_DIR then
        DATA_SIM_DIR for any *.csv or *.parquet.

    Returns
    -------
    pd.DataFrame
        Must contain at least: timestamp, load_kva, transformer_id
    """
    search_dirs = [DATA_PROC_DIR, DATA_SIM_DIR]

    if path is None:
        for d in search_dirs:
            p = Path(d)
            for ext in ("*.parquet", "*.csv"):
                files = sorted(p.glob(ext))
                if files:
                    path = str(files[0])
                    log.info("Auto-discovered load file: %s", path)
                    break
            if path:
                break

    if path is None:
        log.warning(
            "No processed or simulated CSV found. "
            "Generating a minimal synthetic stub for pipeline testing."
        )
        return _synthetic_load_stub()

    p = Path(path)
    df: pd.DataFrame = pd.read_parquet(p) if p.suffix == ".parquet" else pd.read_csv(p)
    df[COL_TIMESTAMP] = pd.to_datetime(df[COL_TIMESTAMP])
    log.info("Loaded %d load rows from %s.", len(df), p)
    return df


def _synthetic_load_stub() -> pd.DataFrame:
    """
    Tiny synthetic dataset used when Member 1's data isn't available yet.
    Generates 8 760 h × 1 transformer so the pipeline can be tested end-to-end.
    """
    rng = np.random.default_rng(42)
    hours = 8760
    timestamps = pd.date_range("2024-01-01", periods=hours, freq="h")
    df = pd.DataFrame(
        {
            COL_TIMESTAMP: timestamps,
            COL_UNIT: "T001",
            COL_LOAD: rng.uniform(50, 500, hours).round(2),
            COL_TEMP: rng.uniform(15, 42, hours).round(2),
            COL_FAULT: rng.choice([0, 1], hours, p=[0.98, 0.02]),
        }
    )
    log.info("Synthetic stub created: %d rows.", len(df))
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Step 2 — Merge load data with weather forecast
# ─────────────────────────────────────────────────────────────────────────────


def merge_load_weather(
    df_load: pd.DataFrame,
    df_weather: pd.DataFrame,
    horizon_h: int = FORECAST_HORIZON_H,
) -> pd.DataFrame:
    df_load = df_load.copy()
    df_weather = df_weather.copy()
    df_load[COL_TIMESTAMP] = pd.to_datetime(df_load[COL_TIMESTAMP])
    df_weather[COL_TIMESTAMP] = pd.to_datetime(df_weather[COL_TIMESTAMP])

    # ── ADD THIS BLOCK ──────────────────────────────────────────────
    # Drop any weather columns already present in df_load to prevent
    # duplicate column collision during merge (e.g. temperature_2m
    # exists in both the synthetic stub and the weather DataFrame).
    weather_cols_to_drop = [
        c for c in df_weather.columns if c != COL_TIMESTAMP and c in df_load.columns
    ]
    if weather_cols_to_drop:
        log.info(
            "Dropping pre-existing weather columns from load data: %s",
            weather_cols_to_drop,
        )
        df_load = df_load.drop(columns=weather_cols_to_drop)
    # ────────────────────────────────────────────────────────────────

    df_load_slice = (
        df_load.sort_values(COL_TIMESTAMP).tail(horizon_h).reset_index(drop=True)
    )

    # --- Round timestamps to the nearest hour for alignment ---------------
    df_load_slice[COL_TIMESTAMP] = df_load_slice[COL_TIMESTAMP].dt.round("h")
    df_weather[COL_TIMESTAMP] = df_weather[COL_TIMESTAMP].dt.round("h")

    # --- Merge on timestamp (left join keeps all load rows) ---------------
    df_merged: pd.DataFrame = pd.merge(
        df_load_slice,
        df_weather,
        on=COL_TIMESTAMP,
        how="left",
        suffixes=("", "_weather"),
    )

    # --- Forward-fill any unmatched weather rows --------------------------
    weather_cols = [c for c in df_weather.columns if c != COL_TIMESTAMP]
    df_merged[weather_cols] = df_merged[weather_cols].ffill().bfill()

    log.info(
        "Merged frame: %d rows × %d columns.",
        len(df_merged),
        df_merged.shape[1],
    )
    return df_merged


# ─────────────────────────────────────────────────────────────────────────────
# Step 3 — Prepare Prophet input
# ─────────────────────────────────────────────────────────────────────────────


def prepare_prophet_input(df_merged: pd.DataFrame) -> pd.DataFrame:
    """
    Produce a Prophet-compatible DataFrame.

    Prophet requires exactly two columns: `ds` (datestamp) and `y` (target).
    We also attach the weather regressors so Member 1 can optionally add
    them as extra regressors to the model.

    Returns
    -------
    pd.DataFrame
        Columns: ds, y, temperature_2m, relativehumidity_2m,
                 windspeed_10m, precipitation
    """
    required = {COL_TIMESTAMP, TARGET_COL}
    missing = required - set(df_merged.columns)
    if missing:
        raise ValueError(f"Merged DataFrame is missing columns: {missing}")

    regressor_cols = [
        c for c in FEATURE_COLS if c in df_merged.columns and c != TARGET_COL
    ]

    df_prophet = df_merged[[COL_TIMESTAMP, TARGET_COL, *regressor_cols]].copy()
    df_prophet.rename(
        columns={COL_TIMESTAMP: "ds", TARGET_COL: "y"},
        inplace=True,
    )
    df_prophet.sort_values("ds", inplace=True)
    df_prophet.reset_index(drop=True, inplace=True)

    log.info(
        "Prophet input ready: %d rows, regressors=%s.",
        len(df_prophet),
        regressor_cols,
    )
    return df_prophet


# ─────────────────────────────────────────────────────────────────────────────
# Step 4 — Persist pipeline outputs
# ─────────────────────────────────────────────────────────────────────────────


def save_pipeline_outputs(
    df_merged: pd.DataFrame,
    df_prophet: pd.DataFrame,
    df_weather: pd.DataFrame,
    out_dir: str = DATA_PROC_DIR,
) -> None:
    """
    Write all three pipeline DataFrames to Parquet in DATA_PROC_DIR
    so every team member can load a consistent snapshot.

    Files written
    -------------
    data/processed/merged_pipeline.parquet
    data/processed/prophet_input.parquet
    data/processed/weather_72h.parquet
    """
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    outputs = {
        "merged_pipeline.parquet": df_merged,
        "prophet_input.parquet": df_prophet,
        "weather_72h.parquet": df_weather,
    }
    for fname, df in outputs.items():
        fpath = Path(out_dir) / fname
        df.to_parquet(fpath, index=False)
        log.info("Saved → %s  (%d rows)", fpath, len(df))


# ─────────────────────────────────────────────────────────────────────────────
# Orchestrator — run the full pipeline in one call
# ─────────────────────────────────────────────────────────────────────────────


def run_pipeline(
    load_path: str | None = None,
    force_weather: bool = False,
    save_outputs: bool = True,
) -> dict[str, pd.DataFrame]:
    """
    Execute the full Member 4 pipeline:

      1. Load processed transformer data.
      2. Fetch (or load cached) 72-hour weather forecast.
      3. Merge on timestamp.
      4. Prepare Prophet input.
      5. (Optional) Save all outputs to Parquet.

    Parameters
    ----------
    load_path : str | None
        Path to load CSV/Parquet. Auto-detected if None.
    force_weather : bool
        Force a fresh API call even if a cache exists.
    save_outputs : bool
        Write Parquet files to data/processed/.

    Returns
    -------
    dict with keys: "merged", "prophet", "weather"
    """
    log.info("─── PowerPulse AI Data Pipeline START ───")

    # 1 — Load
    df_load = load_processed_load(path=load_path)

    # 2 — Weather
    df_weather = get_weather_dataframe(force_refresh=force_weather)

    # 3 — Merge
    df_merged = merge_load_weather(df_load, df_weather)

    # 4 — Prophet
    df_prophet = prepare_prophet_input(df_merged)

    # 5 — Persist
    if save_outputs:
        save_pipeline_outputs(df_merged, df_prophet, df_weather)

    log.info("─── PowerPulse AI Data Pipeline DONE  ───")

    return {
        "merged": df_merged,
        "prophet": df_prophet,
        "weather": df_weather,
    }


# ─────────────────────────────────────────────────────────────────────────────
# CLI smoke-test
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print(" PowerPulse AI — data_pipeline.py smoke test")
    print("=" * 60)

    results = run_pipeline(save_outputs=True)

    for name, df in results.items():
        print(f"\n[{name}]  shape={df.shape}")
        print(df.head(3).to_string(index=False))

    print("\n✓  data_pipeline.py works correctly.")
