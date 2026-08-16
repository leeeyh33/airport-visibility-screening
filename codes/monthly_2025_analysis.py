from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "results"
OUTPUT_CSV = DATA_DIR / "airport_2025_monthly.csv"
OUTPUT_CHART = PROJECT_DIR / "pics" / "airport_2025_monthly_lower_only_hours.png"

AIRPORTS = [
    ("KAST", "America/Los_Angeles", 0.75, 1.00),
    ("KCEC", "America/Los_Angeles", 0.75, 1.00),
    ("KHQM", "America/Los_Angeles", 0.50, 1.25),
    ("KGRI", "America/Chicago", 0.50, 0.75),
]

MONTH_NAMES = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]


def monthly_hours(intervals, time_zone):
    totals = {month: 0.0 for month in range(1, 13)}

    target = intervals[intervals["state"] == "lower_only"].copy()
    target["local_start"] = target["interval_start_utc"].dt.tz_convert(time_zone)
    target["local_end"] = target["interval_end_utc"].dt.tz_convert(time_zone)

    # split time btw months
    for row in target.itertuples():
        current = row.local_start
        while current < row.local_end:
            next_month = (current + pd.offsets.MonthBegin(1)).normalize()
            part_end = min(row.local_end, next_month)
            totals[current.month] += (part_end - current).total_seconds() / 3600
            current = part_end

    return totals


def main():
    rows = []

    for airport, time_zone, lower_limit, higher_limit in AIRPORTS:
        interval_file = DATA_DIR / f"{airport}_2025_visibility_intervals.csv"
        intervals = pd.read_csv(
            interval_file,
            parse_dates=["interval_start_utc", "interval_end_utc"],
        )
        totals = monthly_hours(intervals, time_zone)
        airport_total = sum(totals.values())

        for month in range(1, 13):
            hours = totals[month]
            rows.append(
                {
                    "airport": airport,
                    "time_zone": time_zone,
                    "month": month,
                    "month_name": MONTH_NAMES[month - 1],
                    "lower_limit_miles": lower_limit,
                    "higher_limit_miles": higher_limit,
                    "lower_only_hours": hours,
                    "share_of_airport_target_percent": hours / airport_total * 100,
                }
            )

    monthly = pd.DataFrame(rows)
    monthly.to_csv(OUTPUT_CSV, index=False, float_format="%.6f")

    fig, ax = plt.subplots(figsize=(9, 5.4))
    colors = ["#4C78A8", "#F58518", "#54A24B", "#E45756"]

    for (airport, _, lower_limit, higher_limit), color in zip(AIRPORTS, colors):
        airport_data = monthly[monthly["airport"] == airport]
        ax.plot(
            airport_data["month"],
            airport_data["lower_only_hours"],
            marker="o",
            linewidth=2,
            color=color,
            label=f"{airport} ({lower_limit:.2f}-{higher_limit:.2f} mi)",
        )

    ax.set_title("2025 Monthly Hours When Only the Lower-Visibility Option Helps")
    ax.set_xlabel("Local month")
    ax.set_ylabel("Hours")
    ax.set_xticks(range(1, 13), MONTH_NAMES)
    ax.set_ylim(bottom=0)
    ax.grid(axis="y", alpha=0.25)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(ncol=2, frameon=False)
    fig.text(
        0.5,
        0.01,
        "Months use each airport's local time; each airport keeps its own published visibility range.",
        ha="center",
        fontsize=8,
    )
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(OUTPUT_CHART, dpi=200, bbox_inches="tight")
    plt.close(fig)

    airport_totals = monthly.groupby("airport")["lower_only_hours"].sum()
    peak = monthly.loc[monthly["lower_only_hours"].idxmax()]

    print(f"monthly_rows={len(monthly)}")
    for airport, _, _, _ in AIRPORTS:
        print(f"{airport}_total_hours={airport_totals[airport]:.2f}")
    print(f"peak_airport_month={peak['airport']}_{peak['month_name']}")
    print(f"peak_month_hours={peak['lower_only_hours']:.2f}")


if __name__ == "__main__":
    main()
