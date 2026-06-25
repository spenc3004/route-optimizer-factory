import pandas as pd
import numpy as np

def ensure_numeric(df):
    for c in ["Mailing Qty", "RO's", "Responded", "Revenue", "Expense", "Response"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def aggregate(df):
    if "Campaigns" not in df.columns:
        raise ValueError("Missing 'Campaigns' column in the DataFrame. Cannot create summary.")

    df = df.copy()

    if "In Homes Week Of" in df.columns:
        df["In Homes Week Of"] = pd.to_datetime(df["In Homes Week Of"], errors="coerce")

    agg_map = {
            "Times Mailed To": ("Campaigns", "size"), 
            "Overall Mailing Qty": ("Mailing Qty", "sum"),
            "Overall RO's": ("RO's", "sum"),
            "Overall Responded": ("Responded", "sum"),
            "Overall Revenue": ("Revenue", "sum"),
            "Overall Expense": ("Expense", "sum"),
        }

    if "In Homes Week Of" in df.columns:
        agg_map["Most Recent Mailed To"] = ("In Homes Week Of", "max")

    roi_summary = df.groupby("Campaigns", as_index=False).agg(**agg_map)

    if "Most Recent Mailed To" in roi_summary.columns:
        roi_summary["Most Recent Mailed To"] = roi_summary["Most Recent Mailed To"].dt.strftime("%m-%d-%Y")

    return roi_summary

def overall_rr_roas(summary):
    summary["Response Rate"] = np.where(
        summary["Overall Mailing Qty"] > 0,
        summary["Overall Responded"] / summary["Overall Mailing Qty"],
        np.nan
    )

    summary["Overall ROAS"] = np.where(
        (summary["Overall Mailing Qty"] > 0) & (summary["Overall Expense"] > 0),
        summary["Overall Revenue"] / summary["Overall Expense"],
        np.nan
    )
    return summary

def roi_merge(roi, ranked):
    # Aggregate by Campaigns (one row per Campaign/Geocode)
    try:
        summary = aggregate(roi)
    except Exception as e:
        return None, None, f"Failed to aggregate ROI data: {e}"

    # Calculate Response Rate and ROAS
    try:
        summary = overall_rr_roas(summary)
    except Exception as e:
        return None, None, f"Failed to calculate Response Rate and ROAS: {e}"                  

    # --- Merge the summary to ranked on Geocode (left) vs Campaigns (right) ---
    merged_df = ranked.merge(summary, left_on="Geocode", right_on="Campaigns", how="left")

    # Hide the right-side key after merge
    if "Campaigns" in merged_df.columns:
        merged_df = merged_df.drop(columns=["Campaigns"])

    # Convert to percentage
    if "Response Rate" in merged_df.columns:
        merged_df["Response Rate %"] = (merged_df["Response Rate"] * 100).round(2)

    return merged_df, summary, None