import numpy as np
import pandas as pd
from utilities.helpers import adaptive_minmax_iqr

def calculate_wps(df, id_series, use_wps, audit):
    if not use_wps:
        return df, audit
    if all(col in df.columns for col in ['$ Total Spend', 'Total Visits', 'Selected']):
        wps = (df['$ Total Spend'] + df['Total Visits']) / df['Selected'].replace(0, np.nan)
        wps = wps.replace([np.inf, -np.inf], np.nan).fillna(0.0)

        df['Weighted Penetration Score'] = wps
        wps_norm, wps_audit = adaptive_minmax_iqr(wps, col_name='Weighted Penetration Score', id_series=id_series)
        audit.append(wps_audit)
        df['Weighted Penetration Score_Norm'] = wps_norm
    else:
        df['Weighted Penetration Score_Norm'] = 0.0
        return df, audit, "Missing required columns for Weighted Penetration Score calculation. Skipping this metric."

    return df, audit, None

def calculate_vds(working, id_series, use_vds, audit):
    if not use_vds:
        return working, audit
    VEHICLE_COLUMNS = {
        '5+ Vehicles': 5,
        '% 4 Vehicles': 4,
        '% 3 Vehicles': 3,
        '% 2 Vehicles': 2,
        '% 1 Vehicle': 1,
        '% No Vehicle': -5
    }

    # Ensure missing vehicle columns do not crash the app
    for col in VEHICLE_COLUMNS.keys():
        if col not in working.columns:
            working[col] = 0

    # Calculate raw Vehicle Density Score
    vds = np.zeros(len(working))
    for col, points in VEHICLE_COLUMNS.items():
        vds += working[col] * points
    working['Vehicle Density Score'] = vds
                   
    vds_norm, vds_audit = adaptive_minmax_iqr(vds, col_name='Vehicle Density Score', id_series=id_series)
    audit.append(vds_audit)
    working['Vehicle Density Score_Norm'] = vds_norm
    return working, audit

def calculate_cpms(working, ideal_map, ideal_values, use_cpms, field_weights=None):
    if not use_cpms:
        return working

    field_scores = []
    weights = []
    field_weights = field_weights or {}
    eps = 1e-9

    for field in ideal_map.keys():
        ideal = ideal_values.get(field)
        if field not in working.columns or ideal is None:
            continue

        actual = pd.to_numeric(working[field], errors="coerce")
        ideal = float(ideal)

        if field == "Distance":
            miss_ratio = np.maximum(actual - ideal, 0.0) / max(abs(ideal), eps)
        else:
            miss_ratio = np.maximum(ideal - actual, 0.0) / max(abs(ideal), eps)

        match = 1 - np.clip(miss_ratio, 0, 1)
        field_scores.append(match.fillna(0.0).to_numpy())
        weights.append(field_weights.get(field, 1.0))

    if field_scores:
        score_matrix = np.vstack(field_scores)
        working["Customer Profile Match Score"] = np.average(score_matrix, axis=0, weights=weights)

    return working


def calculate_cs(working, weights):
    score = np.zeros(len(working))
    for key, w in weights.items():
        if w == 0:
            continue
        if key == 'Customer Profile Match Score' and key in working.columns:
            score += working[key] * w
        elif key == 'Weighted Penetration Score' and 'Weighted Penetration Score_Norm' in working.columns:
            score += working['Weighted Penetration Score_Norm'] * w
        elif key == 'Vehicle Density Score' and 'Vehicle Density Score_Norm' in working.columns:
                score += working['Vehicle Density Score_Norm'] * w
        elif key == 'Distance' and 'Distance_Norm' in working.columns:
            score += (1 - working['Distance_Norm']) * w
        elif f"{key}_Norm" in working.columns:
            score += working[f"{key}_Norm"] * w


    working['Composite Score'] = score

    return working