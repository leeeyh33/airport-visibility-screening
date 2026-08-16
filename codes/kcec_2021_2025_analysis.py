from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_FILE = PROJECT_DIR / "raw" / "KCEC_METAR_2021_2025_raw.csv"
INTERVAL_FILE = PROJECT_DIR / "results" / "KCEC_2021_2025_visibility_intervals.csv"
YEARLY_FILE = PROJECT_DIR / "results" / "KCEC_2021_2025_yearly.csv"
CHART_FILE = PROJECT_DIR / "pics" / "KCEC_2021_2025_lower_only_hours.png"


def main():
    weather = pd.read_csv(RAW_FILE, na_values=["M"])
    raw_rows = len(weather)

    # same data clean
    weather["valid"] = pd.to_datetime(
        weather["valid"], utc=True, errors="coerce"
    )
    weather["vsby"] = pd.to_numeric(weather["vsby"], errors="coerce")
    weather = weather.dropna(subset=["valid"])
    weather = weather[
        weather["valid"].between(
            pd.Timestamp("2021-01-01", tz="UTC"),
            pd.Timestamp("2026-01-01", tz="UTC"),
            inclusive="left",
        )
    ]
    weather = weather.sort_values("valid")
    weather = weather.drop_duplicates(["station", "valid"], keep="last")
    weather = weather.reset_index(drop=True)

    yearly_rows = []
    interval_parts = []

    for year in range(2021, 2026):
        start = pd.Timestamp(f"{year}-01-01", tz="UTC")
        end = pd.Timestamp(f"{year + 1}-01-01", tz="UTC")
        calendar_hours = (end - start).total_seconds() / 3600

        current = weather[
            weather["valid"].between(start, end, inclusive="left")
        ].copy()

        # each report max 1 hr
        current["next_report_utc"] = current["valid"].shift(-1).fillna(end)
        current["one_hour_later"] = current["valid"] + pd.Timedelta(hours=1)
        current["interval_end_utc"] = current[
            ["next_report_utc", "one_hour_later"]
        ].min(axis=1)
        current["hours"] = (
            current["interval_end_utc"] - current["valid"]
        ).dt.total_seconds() / 3600

        # set vis range
        current["state"] = "both_options"
        current.loc[current["vsby"] < 1.00, "state"] = "lower_only"
        current.loc[current["vsby"] < 0.75, "state"] = "neither_option"
        current.loc[current["vsby"].isna(), "state"] = "unknown"

        known_hours = current.loc[current["state"] != "unknown", "hours"].sum()
        lower_only_hours = current.loc[
            current["state"] == "lower_only", "hours"
        ].sum()
        unknown_hours = calendar_hours - known_hours

        yearly_rows.append(
            {
                "year": year,
                "calendar_hours": calendar_hours,
                "known_hours": known_hours,
                "unknown_hours": unknown_hours,
                "lower_only_hours": lower_only_hours,
                "lower_only_percent_year": lower_only_hours / calendar_hours * 100,
                "data_coverage_percent": known_hours / calendar_hours * 100,
            }
        )

        intervals = current[
            ["valid", "interval_end_utc", "vsby", "hours", "state"]
        ].rename(
            columns={"valid": "interval_start_utc", "vsby": "visibility_miles"}
        )
        intervals.insert(0, "year", year)
        interval_parts.append(intervals)

    yearly = pd.DataFrame(yearly_rows)
    all_intervals = pd.concat(interval_parts, ignore_index=True)

    all_intervals.to_csv(
        INTERVAL_FILE, index=False, date_format="%Y-%m-%dT%H:%M:%SZ"
    )
    yearly.to_csv(YEARLY_FILE, index=False, float_format="%.6f")

    median_hours = yearly["lower_only_hours"].median()
    minimum_hours = yearly["lower_only_hours"].min()
    maximum_hours = yearly["lower_only_hours"].max()
    value_2025 = yearly.loc[
        yearly["year"] == 2025, "lower_only_hours"
    ].iloc[0]

    fig, ax = plt.subplots(figsize=(8, 4.8))
    bars = ax.bar(
        yearly["year"].astype(str),
        yearly["lower_only_hours"],
        color="#3b82a0",
    )
    ax.axhline(
        median_hours,
        color="#d97706",
        linestyle="--",
        linewidth=1.5,
        label=f"Five-year median: {median_hours:.1f} hours",
    )
    ax.bar_label(bars, fmt="%.1f", padding=3)
    ax.set_title("KCEC: Annual Hours When Only the Lower-Visibility Option Helps")
    ax.set_xlabel("Year")
    ax.set_ylabel("Hours")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_ylim(0, yearly["lower_only_hours"].max() * 1.2)
    fig.text(
        0.5,
        0.01,
        "Weather-only screen: visibility from 0.75 to below 1.00 mile",
        ha="center",
        fontsize=9,
        color="#555555",
    )
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    fig.savefig(CHART_FILE, dpi=160)
    plt.close(fig)

    print(f"raw_rows={raw_rows}")
    print(f"clean_rows={len(weather)}")
    print(f"yearly_rows={len(yearly)}")
    for row in yearly.itertuples():
        print(f"{row.year}_lower_only_hours={row.lower_only_hours:.2f}")
    print(f"median_lower_only_hours={median_hours:.2f}")
    print(f"minimum_lower_only_hours={minimum_hours:.2f}")
    print(f"maximum_lower_only_hours={maximum_hours:.2f}")
    print(f"2025_minus_median_hours={value_2025 - median_hours:.2f}")


if __name__ == "__main__":
    main()
