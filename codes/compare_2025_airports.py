from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "results"
OUTPUT_CSV = DATA_DIR / "airport_2025_comparison.csv"
OUTPUT_CHART = PROJECT_DIR / "pics" / "airport_2025_lower_only_hours.png"

AIRPORTS = [
    ("KAST", 0.75, 1.00),
    ("KCEC", 0.75, 1.00),
    ("KHQM", 0.50, 1.25),
    ("KGRI", 0.50, 0.75),
]


def main():
    rows = []

    for airport, lower_limit, higher_limit in AIRPORTS:
        summary_file = DATA_DIR / f"{airport}_2025_visibility_summary.csv"
        summary = pd.read_csv(summary_file).set_index("state")

        rows.append(
            {
                "airport": airport,
                "lower_limit_miles": lower_limit,
                "higher_limit_miles": higher_limit,
                "lower_only_hours": summary.loc["lower_only", "hours"],
                "percent_of_year": summary.loc["lower_only", "percent_of_year"],
                "unknown_hours": summary.loc["unknown", "hours"],
            }
        )

    comparison = pd.DataFrame(rows)
    comparison.to_csv(OUTPUT_CSV, index=False, float_format="%.6f")

    chart_data = comparison.sort_values("lower_only_hours")
    labels = [
        f"{row.airport}  ({row.lower_limit_miles:.2f}-{row.higher_limit_miles:.2f} mi)"
        for row in chart_data.itertuples()
    ]

    fig, ax = plt.subplots(figsize=(8, 4.8))
    bars = ax.barh(labels, chart_data["lower_only_hours"], color="#4C78A8")
    ax.bar_label(bars, fmt="%.2f hours", padding=4)
    ax.set_title("2025 Hours When Only the Lower-Visibility Option Helps")
    ax.set_xlabel("Hours in 2025")
    ax.set_xlim(0, chart_data["lower_only_hours"].max() * 1.18)
    ax.grid(axis="x", alpha=0.25)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(
        0.5,
        0.01,
        "Each airport uses its own published visibility range; this is a weather screen, not an investment decision.",
        ha="center",
        fontsize=8,
    )
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(OUTPUT_CHART, dpi=200, bbox_inches="tight")
    plt.close(fig)

    highest = comparison.loc[comparison["lower_only_hours"].idxmax()]
    print(f"comparison_rows={len(comparison)}")
    print(f"highest_airport={highest['airport']}")
    print(f"highest_lower_only_hours={highest['lower_only_hours']:.2f}")
    print(f"output_csv={OUTPUT_CSV.name}")
    print(f"output_chart={OUTPUT_CHART.name}")


if __name__ == "__main__":
    main()
