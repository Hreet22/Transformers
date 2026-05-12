import pandas as pd
import joblib
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from prophet import Prophet
from config import (
    DATA_SIM_DIR, MODEL_PATH, FORECAST_HORIZON_H,
    FORECAST_FREQ, PROPHET_SEASONALITY, CHANGEPOINT_SCALE
)

def train_and_forecast(transformer_id="T001"):
    # 1. Load the simulated data
    df = pd.read_csv(DATA_SIM_DIR + "simulated_load_data.csv")

    # 2. Filter for one transformer (Prophet works per unit)
    df = df[df['transformer_id'] == transformer_id].copy()

    # 3. Prepare Prophet format — needs columns: ds (datetime), y (value)
    df_prophet = df[['timestamp', 'load_kva']].rename(
        columns={'timestamp': 'ds', 'load_kva': 'y'}
    )
    df_prophet['ds'] = pd.to_datetime(df_prophet['ds'])

    # 4. Split: train on all except last 72 hours
    df_train = df_prophet.iloc[:-FORECAST_HORIZON_H]

    # 5. Train Prophet model
    model = Prophet(
        seasonality_mode=PROPHET_SEASONALITY,
        changepoint_prior_scale=CHANGEPOINT_SCALE
    )
    model.fit(df_train)

    # 6. Generate future 72-hour frame and predict
    df_future   = model.make_future_dataframe(periods=FORECAST_HORIZON_H, freq=FORECAST_FREQ)
    df_forecast = model.predict(df_future)

    # Key output columns
    yhat       = df_forecast['yhat']        # point forecast
    yhat_lower = df_forecast['yhat_lower']  # lower bound
    yhat_upper = df_forecast['yhat_upper']  # upper bound

    print(df_forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(10))

    # 7. Save model
    os.makedirs("models", exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"✅ Model saved to {MODEL_PATH}")

    return df_forecast

if __name__ == "__main__":
    train_and_forecast()
