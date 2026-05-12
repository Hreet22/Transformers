"""
tests/test_pipeline.py  —  Member 4 | Data & Integration
=========================================================
Unit tests for weather_api.py and data_pipeline.py.
Run with:  python -m pytest tests/test_pipeline.py -v
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

# ── ensure project root is on sys.path ──────────────────────────────────────
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline.weather_api import (
    _parse_response,
    _build_params,
    load_cached_weather,
)
from pipeline.data_pipeline import (
    _synthetic_load_stub,
    merge_load_weather,
    prepare_prophet_input,
    run_pipeline,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────

MOCK_OPEN_METEO_RESPONSE = {
    "latitude": 13.08,
    "longitude": 80.27,
    "timezone": "Asia/Kolkata",
    "hourly": {
        "time": [
            t.strftime("%Y-%m-%dT%H:%M")
            for t in pd.date_range("2024-12-30", periods=72, freq="h")
        ],
        "temperature_2m": [30.0 + (i % 10) * 0.5 for i in range(72)],
        "relativehumidity_2m": [60.0 + (i % 5) for i in range(72)],
        "windspeed_10m": [10.0 + (i % 8) * 0.3 for i in range(72)],
        "precipitation": [0.0 + (i % 3) * 0.1 for i in range(72)],
    },
}


# ── weather_api tests ─────────────────────────────────────────────────────────


class TestParseResponse:
    def test_returns_dataframe(self):
        df = _parse_response(MOCK_OPEN_METEO_RESPONSE)
        assert isinstance(df, pd.DataFrame)

    def test_row_count_is_72(self):
        df = _parse_response(MOCK_OPEN_METEO_RESPONSE)
        assert len(df) == 72

    def test_expected_columns(self):
        df = _parse_response(MOCK_OPEN_METEO_RESPONSE)
        for col in [
            "timestamp",
            "temperature_2m",
            "relativehumidity_2m",
            "windspeed_10m",
            "precipitation",
        ]:
            assert col in df.columns, f"Missing column: {col}"

    def test_timestamp_is_datetime(self):
        df = _parse_response(MOCK_OPEN_METEO_RESPONSE)
        assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])

    def test_missing_hourly_key_raises(self):
        with pytest.raises(ValueError, match="hourly"):
            _parse_response({})


class TestBuildParams:
    def test_keys_present(self):
        p = _build_params(13.08, 80.27)
        for key in ("latitude", "longitude", "hourly", "forecast_days", "timezone"):
            assert key in p

    def test_coordinates_match(self):
        p = _build_params(13.08, 80.27)
        assert p["latitude"] == 13.08
        assert p["longitude"] == 80.27


class TestFetchWeather:
    @patch("pipeline.weather_api.requests.get")
    def test_live_fetch_returns_dataframe(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = MOCK_OPEN_METEO_RESPONSE
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        from pipeline.weather_api import fetch_weather

        df = fetch_weather(cache=False)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 72

    @patch("pipeline.weather_api.requests.get")
    def test_http_error_raises_runtime_error(self, mock_get):
        import requests as req

        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = req.exceptions.HTTPError("404")
        mock_get.return_value = mock_resp

        from pipeline.weather_api import fetch_weather

        with pytest.raises(RuntimeError, match="HTTP error"):
            fetch_weather(cache=False)


# ── data_pipeline tests ───────────────────────────────────────────────────────


class TestSyntheticLoadStub:
    def test_returns_dataframe(self):
        df = _synthetic_load_stub()
        assert isinstance(df, pd.DataFrame)

    def test_has_required_columns(self):
        df = _synthetic_load_stub()
        for col in ["timestamp", "transformer_id", "load_kva"]:
            assert col in df.columns

    def test_8760_rows(self):
        df = _synthetic_load_stub()
        assert len(df) == 8760


class TestMergeLoadWeather:
    @pytest.fixture
    def df_load(self):
        return _synthetic_load_stub()

    @pytest.fixture
    def df_weather(self):
        return _parse_response(MOCK_OPEN_METEO_RESPONSE)

    def test_returns_dataframe(self, df_load, df_weather):
        df = merge_load_weather(df_load, df_weather)
        assert isinstance(df, pd.DataFrame)

    def test_row_count_is_72(self, df_load, df_weather):
        df = merge_load_weather(df_load, df_weather)
        assert len(df) == 72

    def test_has_weather_columns(self, df_load, df_weather):
        df = merge_load_weather(df_load, df_weather)
        assert "temperature_2m" in df.columns

    def test_no_all_null_weather(self, df_load, df_weather):
        df = merge_load_weather(df_load, df_weather)
        assert not df["temperature_2m"].isna().all()


class TestPrepareProphetInput:
    @pytest.fixture
    def df_merged(self):
        load = _synthetic_load_stub()
        weather = _parse_response(MOCK_OPEN_METEO_RESPONSE)
        return merge_load_weather(load, weather)

    def test_has_ds_and_y(self, df_merged):
        df = prepare_prophet_input(df_merged)
        assert "ds" in df.columns
        assert "y" in df.columns

    def test_sorted_by_ds(self, df_merged):
        df = prepare_prophet_input(df_merged)
        assert df["ds"].is_monotonic_increasing

    def test_missing_column_raises(self):
        bad = pd.DataFrame(
            {"timestamp": pd.date_range("2024-01-01", periods=5, freq="h")}
        )
        with pytest.raises(ValueError):
            prepare_prophet_input(bad)


class TestRunPipeline:
    @patch("pipeline.data_pipeline.get_weather_dataframe")
    def test_returns_expected_keys(self, mock_weather):
        mock_weather.return_value = _parse_response(MOCK_OPEN_METEO_RESPONSE)
        result = run_pipeline(save_outputs=False)
        assert set(result.keys()) == {"merged", "prophet", "weather"}

    @patch("pipeline.data_pipeline.get_weather_dataframe")
    def test_prophet_output_valid(self, mock_weather):
        mock_weather.return_value = _parse_response(MOCK_OPEN_METEO_RESPONSE)
        result = run_pipeline(save_outputs=False)
        df_p = result["prophet"]
        assert "ds" in df_p.columns
        assert "y" in df_p.columns
        assert len(df_p) == 72
