from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "results"
OUTPUT_FILE = DATA_DIR / "airport_2021_2025_event_comparison.csv"
CHART_FILE = PROJECT_DIR / "pics" / "airport_2021_2025_event_comparison.png"

AIRPORTS = ["KCEC", "KAST", "KHQM", "KGRI"]
COLORS = ["#4C78A8", "#F28E2B", "#59A14F", "#E15759"]


def main():
    yearly = pd.read_csv(DATA_DIR / "airport_2021_2025_comparison.csv")

    event_tables = []
    for airport in AIRPORTS:
        event_tables.append(
            pd.read_csv(DATA_DIR / f"{airport}_2021_2025_event_summary.csv")
        )
    events = pd.concat(event_tables, ignore_index=True)

    comparison = yearly.merge(events, on="airport", how="inner")
    comparison["target_visibility_range"] = comparison.apply(
        lambda row: (
            f"{row['lower_limit_miles']:.2f} to "
            f"below {row['higher_limit_miles']:.2f} miles"
        ),
        axis=1,
    )
    comparison["airport_order"] = pd.Categorical(
        comparison["airport"], categories=AIRPORTS, ordered=True
    )
    comparison = comparison.sort_values("airport_order")

    comparison = comparison[
        [
            "airport",
            "target_visibility_range",
            "median_annual_hours",
            "total_event_hours",
            "event_count",
            "median_event_minutes",
            "maximum_event_hours",
            "share_events_at_least_1_hour_percent",
            "share_hours_from_events_at_least_1_hour_percent",
        ]
    ]
    comparison.to_csv(OUTPUT_FILE, index=False, float_format="%.6f")

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.8))

    hour_bars = axes[0].bar(
        comparison["airport"], comparison["median_annual_hours"], color=COLORS
    )
    axes[0].bar_label(hour_bars, fmt="%.1f", padding=3)
    axes[0].set_title("Typical annual target hours")
    axes[0].set_ylabel("Hours per year")

    share_bars = axes[1].bar(
        comparison["airport"],
        comparison["share_hours_from_events_at_least_1_hour_percent"],
        color=COLORS,
    )
    axes[1].bar_label(share_bars, fmt="%.1f%%", padding=3)
    axes[1].set_title("Target hours from 1+ hour events")
    axes[1].set_ylabel("Percent of target hours")
    axes[1].set_ylim(0, 60)

    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", alpha=0.25)
        ax.set_axisbelow(True)

    axes[0].set_ylim(0, comparison["median_annual_hours"].max() * 1.18)
    fig.suptitle("Four-Airport Weather Value and Event Continuity, 2021-2025")
    fig.text(
        0.5,
        0.01,
        "Airports use different visibility ranges; KCEC and KAST are the closest direct comparison.",
        ha="center",
        fontsize=8.5,
        color="#555555",
    )
    fig.tight_layout(rect=(0, 0.05, 1, 0.95))
    fig.savefig(CHART_FILE, dpi=200, bbox_inches="tight")
    plt.close(fig)

    highest_hours = comparison.loc[comparison["median_annual_hours"].idxmax()]
    highest_share = comparison.loc[
        comparison["share_hours_from_events_at_least_1_hour_percent"].idxmax()
    ]
    kcec = comparison[comparison["airport"] == "KCEC"].iloc[0]
    kast = comparison[comparison["airport"] == "KAST"].iloc[0]

    print(f"comparison_rows={len(comparison)}")
    print(f"highest_typical_hours_airport={highest_hours['airport']}")
    print(f"highest_typical_hours={highest_hours['median_annual_hours']:.2f}")
    print(f"highest_long_event_share_airport={highest_share['airport']}")
    print(
        "highest_long_event_share_percent="
        f"{highest_share['share_hours_from_events_at_least_1_hour_percent']:.2f}"
    )
    print(
        "same_range_KCEC_typical_hours="
        f"{kcec['median_annual_hours']:.2f}"
    )
    print(
        "same_range_KAST_typical_hours="
        f"{kast['median_annual_hours']:.2f}"
    )
    print(
        "same_range_KCEC_long_event_share_percent="
        f"{kcec['share_hours_from_events_at_least_1_hour_percent']:.2f}"
    )
    print(
        "same_range_KAST_long_event_share_percent="
        f"{kast['share_hours_from_events_at_least_1_hour_percent']:.2f}"
    )
    print(f"output_csv={OUTPUT_FILE.name}")
    print(f"output_chart={CHART_FILE.name}")


if __name__ == "__main__":
    main()
