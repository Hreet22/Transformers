import numpy as np
import pandas as pd
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import (
    NUM_TRANSFORMERS, SIM_HOURS, SIM_START_DATE,
    LOAD_MIN_KVA, LOAD_MAX_KVA, FAULT_RATE,
    TEMP_MIN_C, TEMP_MAX_C, DATA_SIM_DIR
)

def generate_data():
    os.makedirs(DATA_SIM_DIR, exist_ok=True)

    date_range = pd.date_range(start=SIM_START_DATE, periods=SIM_HOURS, freq='h')
    transformer_ids = [f"T{str(i+1).zfill(3)}" for i in range(NUM_TRANSFORMERS)]

    all_dfs = []

    for unit in transformer_ids:
        load_kva   = np.random.uniform(LOAD_MIN_KVA, LOAD_MAX_KVA, SIM_HOURS)
        temp_c     = np.random.uniform(TEMP_MIN_C, TEMP_MAX_C, SIM_HOURS)
        fault_flag = np.random.choice([0, 1], size=SIM_HOURS, p=[1 - FAULT_RATE, FAULT_RATE])

        df = pd.DataFrame({
            'timestamp':      date_range,
            'transformer_id': unit,
            'load_kva':       load_kva,
            'temp_c':         temp_c,
            'fault_flag':     fault_flag
        })
        all_dfs.append(df)

    df_sim = pd.concat(all_dfs, ignore_index=True)
    output_path = DATA_SIM_DIR + "simulated_load_data.csv"
    df_sim.to_csv(output_path, index=False)
    print(f"Saved {len(df_sim)} rows to {output_path}")
    return df_sim

if __name__ == "__main__":
    generate_data()
