from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent.parent
INTERVAL_FILE = PROJECT_DIR / "results" / "KHQM_2021_2025_visibility_intervals.csv"
EVENT_FILE = PROJECT_DIR / "results" / "KHQM_2021_2025_lower_only_events.csv"
SUMMARY_FILE = PROJECT_DIR / "results" / "KHQM_2021_2025_event_summary.csv"
CHART_FILE = PROJECT_DIR / "pics" / "KHQM_2021_2025_event_durations.png"


def main():
    intervals = pd.read_csv(
        INTERVAL_FILE,
        parse_dates=["interval_start_utc", "interval_end_utc"],
    )
    target = intervals[intervals["state"] == "lower_only"].copy()
    target = target.sort_values("interval_start_utc").reset_index(drop=True)

    # new event after gap
    target["new_event"] = (
        target["interval_start_utc"]
        > target["interval_end_utc"].shift(1)
    )
    target.loc[0, "new_event"] = True
    target["event_id"] = target["new_event"].cumsum()

    events = (
        target.groupby("event_id")
        .agg(
            event_start_utc=("interval_start_utc", "min"),
            event_end_utc=("interval_end_utc", "max"),
            duration_hours=("hours", "sum"),
            interval_count=("hours", "size"),
        )
        .reset_index()
    )
    events["duration_minutes"] = events["duration_hours"] * 60
    events["start_year"] = events["event_start_utc"].dt.year

    duration_labels = ["Under 30 min", "30-59 min", "1-2 hours", "2+ hours"]
    events["duration_group"] = pd.cut(
        events["duration_hours"],
        bins=[0, 0.5, 1, 2, float("inf")],
        labels=duration_labels,
        right=False,
    )

    events = events[
        [
            "event_id",
            "event_start_utc",
            "event_end_utc",
            "duration_hours",
            "duration_minutes",
            "interval_count",
            "start_year",
            "duration_group",
        ]
    ]

    event_count = len(events)
    total_event_hours = events["duration_hours"].sum()
    long_events = events[events["duration_hours"] >= 1]
    two_hour_events = events[events["duration_hours"] >= 2]

    summary = pd.DataFrame(
        [
            {
                "airport": "KHQM",
                "start_year": 2021,
                "end_year": 2025,
                "event_count": event_count,
                "total_event_hours": total_event_hours,
                "median_event_minutes": events["duration_minutes"].median(),
                "mean_event_minutes": events["duration_minutes"].mean(),
                "maximum_event_hours": events["duration_hours"].max(),
                "events_at_least_1_hour": len(long_events),
                "events_at_least_2_hours": len(two_hour_events),
                "share_events_at_least_1_hour_percent": len(long_events)
                / event_count
                * 100,
                "share_hours_from_events_at_least_1_hour_percent": long_events[
                    "duration_hours"
                ].sum()
                / total_event_hours
                * 100,
            }
        ]
    )

    events.to_csv(EVENT_FILE, index=False, date_format="%Y-%m-%dT%H:%M:%SZ")
    summary.to_csv(SUMMARY_FILE, index=False, float_format="%.6f")

    duration_counts = (
        events["duration_group"].value_counts().reindex(duration_labels, fill_value=0)
    )
    fig, ax = plt.subplots(figsize=(7.6, 4.8))
    bars = ax.bar(duration_counts.index, duration_counts.values, color="#59A14F")
    ax.bar_label(bars, padding=3)
    ax.set_title("KHQM Target-Weather Event Durations, 2021-2025")
    ax.set_xlabel("Event duration")
    ax.set_ylabel("Number of events")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.25)
    ax.set_axisbelow(True)
    ax.set_ylim(0, duration_counts.max() * 1.13)
    fig.text(
        0.5,
        0.01,
        "An event ends when the weather leaves the target range or the data has a gap.",
        ha="center",
        fontsize=8.5,
        color="#555555",
    )
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(CHART_FILE, dpi=200, bbox_inches="tight")
    plt.close(fig)

    row = summary.iloc[0]
    print(f"event_count={event_count}")
    print(f"total_event_hours={total_event_hours:.2f}")
    print(f"median_event_minutes={row['median_event_minutes']:.2f}")
    print(f"mean_event_minutes={row['mean_event_minutes']:.2f}")
    print(f"maximum_event_hours={row['maximum_event_hours']:.2f}")
    print(f"events_at_least_1_hour={len(long_events)}")
    print(f"events_at_least_2_hours={len(two_hour_events)}")
    print(
        "share_events_at_least_1_hour_percent="
        f"{row['share_events_at_least_1_hour_percent']:.2f}"
    )
    print(
        "share_hours_from_events_at_least_1_hour_percent="
        f"{row['share_hours_from_events_at_least_1_hour_percent']:.2f}"
    )


if __name__ == "__main__":
    main()
