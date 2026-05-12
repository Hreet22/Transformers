import pandas as pd
import numpy as np
from pulp import *

# STEP 1 — CREATE SAMPLE GRID DATA

# Synthetic dataset 

data = {
    "Zone": ["Zone_A", "Zone_B", "Zone_C", "Zone_D"],
    
    # Predicted Load in %
    "Predicted_Load": [92, 78, 88, 65],
    
    # Transformer Capacity in %
    "Safe_Capacity": [85, 85, 85, 85],
    
    # Temperature in Celsius
    "Temperature": [41, 36, 39, 33],
    
    # EV Charging Demand %
    "EV_Load": [25, 15, 22, 10],
    
    # Historical Failure Count
    "Failure_History": [8, 3, 6, 1]
}

df = pd.DataFrame(data)

print("\n================ GRID DATA ================\n")
print(df)

# STEP 2 — NORMALIZE VALUES

# Convert all values into 0–1 scale

df["Load_Factor"] = df["Predicted_Load"] / 100
df["Temp_Factor"] = df["Temperature"] / 50
df["EV_Factor"] = df["EV_Load"] / 100
df["Failure_Factor"] = df["Failure_History"] / 10

# STEP 3 — RISK SCORE CALCULATION

# Risk Formula:
# Risk Score =
# 0.5 × Load Utilization
# + 0.2 × Temperature
# + 0.2 × EV Demand
# + 0.1 × Failure History

df["Risk_Score"] = (
    0.5 * df["Load_Factor"] +
    0.2 * df["Temp_Factor"] +
    0.2 * df["EV_Factor"] +
    0.1 * df["Failure_Factor"]
) * 100

# STEP 4 — CLASSIFY RISK LEVELS

def classify_risk(score):
    if score >= 75:
        return "HIGH"
    elif score >= 50:
        return "MEDIUM"
    else:
        return "SAFE"

df["Risk_Level"] = df["Risk_Score"].apply(classify_risk)

print("\n================ RISK ANALYSIS ================\n")
print(df[["Zone", "Predicted_Load", "Risk_Score", "Risk_Level"]])

# STEP 5 — IDENTIFY OVERLOADED ZONES

overloaded = df[df["Predicted_Load"] > df["Safe_Capacity"]]

print("\n================ OVERLOADED ZONES ================\n")
print(overloaded[["Zone", "Predicted_Load"]])

# STEP 6 — PULP OPTIMIZATION MODEL

model = LpProblem("Grid_Load_Optimization", LpMinimize)

# Decision Variables:
# How much load to reduce from each overloaded zone

load_shift = {
    zone: LpVariable(f"Shift_{zone}", lowBound=0, upBound=20)
    for zone in overloaded["Zone"]
}

# OBJECTIVE FUNCTION
# Minimize total shifted load

model += lpSum(load_shift[zone] for zone in load_shift)

# CONSTRAINTS
# Ensure final load <= safe capacity

for index, row in overloaded.iterrows():
    
    zone = row["Zone"]
    predicted = row["Predicted_Load"]
    safe = row["Safe_Capacity"]

    model += (
        predicted - load_shift[zone] <= safe,
        f"Safety_Constraint_{zone}"
    )

# STEP 7 — SOLVE OPTIMIZATION

model.solve()

print("\n================ OPTIMIZATION STATUS ================\n")
print("Status:", LpStatus[model.status])

# STEP 8 — DISPLAY REDISTRIBUTION RESULTS

recommendations = []

print("\n================ LOAD REDISTRIBUTION ================\n")

for zone in load_shift:
    
    shifted = load_shift[zone].varValue
    
    final_load = (
        df.loc[df["Zone"] == zone, "Predicted_Load"].values[0]
        - shifted
    )

    print(f"{zone}")
    print(f"  Load to Shift: {shifted:.2f}%")
    print(f"  Final Load: {final_load:.2f}%")

    # Recommendation Logic
    if shifted > 10:
        action = "Delay EV Charging + Reroute Supply"
    else:
        action = "Minor Load Redistribution"

    recommendations.append({
        "Zone": zone,
        "Shifted_Load": shifted,
        "Final_Load": final_load,
        "Recommended_Action": action
    })

# STEP 9 — FINAL RECOMMENDATION TABLE

recommend_df = pd.DataFrame(recommendations)

print("\n================ FINAL ACTIONS ================\n")
print(recommend_df)

# STEP 10 — IMPACT ANALYSIS

before_avg = overloaded["Predicted_Load"].mean()
after_avg = recommend_df["Final_Load"].mean()

print("\n================ IMPACT ANALYSIS ================\n")

print(f"Average Load BEFORE Optimization : {before_avg:.2f}%")
print(f"Average Load AFTER Optimization  : {after_avg:.2f}%")

reduction = before_avg - after_avg

print(f"Peak Load Reduction Achieved     : {reduction:.2f}%")

print("\n================ SYSTEM COMPLETE ================\n")