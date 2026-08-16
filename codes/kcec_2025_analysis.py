from pathlib import Path

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_FILE = PROJECT_DIR / "raw" / "KCEC_METAR_2025_raw.csv"
INTERVAL_FILE = PROJECT_DIR / "results" / "KCEC_2025_visibility_intervals.csv"
SUMMARY_FILE = PROJECT_DIR / "results" / "KCEC_2025_visibility_summary.csv"

START = pd.Timestamp("2025-01-01 00:00:00", tz="UTC")
END = pd.Timestamp("2026-01-01 00:00:00", tz="UTC")
TOTAL_HOURS = (END - START).total_seconds() / 3600


def main():
    weather = pd.read_csv(RAW_FILE, na_values=["M"])
    raw_rows = len(weather)

    # clean data
    weather["valid"] = pd.to_datetime(
        weather["valid"], utc=True, errors="coerce"
    )
    weather["vsby"] = pd.to_numeric(weather["vsby"], errors="coerce")
    weather = weather.dropna(subset=["valid"])
    weather = weather[
        weather["valid"].between(START, END, inclusive="left")
    ]
    weather = weather.sort_values("valid")
    weather = weather.drop_duplicates(["station", "valid"], keep="last")
    weather = weather.reset_index(drop=True)

    # each report max 1 hr
    weather["next_report_utc"] = weather["valid"].shift(-1).fillna(END)
    weather["one_hour_later"] = weather["valid"] + pd.Timedelta(hours=1)
    weather["interval_end_utc"] = weather[
        ["next_report_utc", "one_hour_later"]
    ].min(axis=1)
    weather["hours"] = (
        weather["interval_end_utc"] - weather["valid"]
    ).dt.total_seconds() / 3600

    # set vis range
    weather["state"] = "both_options"
    weather.loc[weather["vsby"] < 1.00, "state"] = "lower_only"
    weather.loc[weather["vsby"] < 0.75, "state"] = "neither_option"
    weather.loc[weather["vsby"].isna(), "state"] = "unknown"

    known = weather[weather["state"] != "unknown"]
    summary = (
        known.groupby("state")["hours"]
        .sum()
        .reindex(["both_options", "lower_only", "neither_option"], fill_value=0)
        .reset_index()
    )

    # no data is unknown
    unknown_hours = TOTAL_HOURS - known["hours"].sum()
    summary.loc[len(summary)] = ["unknown", unknown_hours]
    summary["equivalent_days"] = summary["hours"] / 24
    summary["percent_of_year"] = summary["hours"] / TOTAL_HOURS * 100

    intervals = weather[
        ["valid", "interval_end_utc", "vsby", "hours", "state"]
    ].rename(columns={"valid": "interval_start_utc", "vsby": "visibility_miles"})

    intervals.to_csv(INTERVAL_FILE, index=False, date_format="%Y-%m-%dT%H:%M:%SZ")
    summary.to_csv(SUMMARY_FILE, index=False, float_format="%.6f")

    target_hours = summary.loc[summary["state"] == "lower_only", "hours"].iloc[0]
    print(f"raw_rows={raw_rows}")
    print(f"clean_rows={len(weather)}")
    print(f"missing_visibility={weather['vsby'].isna().sum()}")
    print(f"known_hours={known['hours'].sum():.2f}")
    print(f"unknown_hours={unknown_hours:.2f}")
    print(f"lower_only_hours={target_hours:.2f}")


if __name__ == "__main__":
    main()
