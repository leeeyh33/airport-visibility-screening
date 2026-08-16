from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "results"
OUTPUT_CSV = DATA_DIR / "airport_2021_2025_comparison.csv"
OUTPUT_CHART = PROJECT_DIR / "pics" / "airport_2021_2025_typical_hours.png"

AIRPORTS = [
    ("KAST", 0.75, 1.00),
    ("KCEC", 0.75, 1.00),
    ("KHQM", 0.50, 1.25),
    ("KGRI", 0.50, 0.75),
]


def main():
    rows = []

    for airport, lower_limit, higher_limit in AIRPORTS:
        yearly_file = DATA_DIR / f"{airport}_2021_2025_yearly.csv"
        yearly = pd.read_csv(yearly_file)
        target_hours = yearly["lower_only_hours"]

        rows.append(
            {
                "airport": airport,
                "lower_limit_miles": lower_limit,
                "higher_limit_miles": higher_limit,
                "median_annual_hours": target_hours.median(),
                "mean_annual_hours": target_hours.mean(),
                "minimum_annual_hours": target_hours.min(),
                "maximum_annual_hours": target_hours.max(),
                "year_to_year_range_hours": target_hours.max()
                - target_hours.min(),
                "minimum_data_coverage_percent": yearly[
                    "data_coverage_percent"
                ].min(),
            }
        )

    comparison = pd.DataFrame(rows)
    comparison.to_csv(OUTPUT_CSV, index=False, float_format="%.6f")

    chart_data = comparison.sort_values("median_annual_hours").reset_index(drop=True)
    labels = [
        f"{row.airport}  ({row.lower_limit_miles:.2f}-{row.higher_limit_miles:.2f} mi)"
        for row in chart_data.itertuples()
    ]
    y_positions = range(len(chart_data))

    fig, ax = plt.subplots(figsize=(8.6, 5.0))
    bars = ax.barh(
        y_positions,
        chart_data["median_annual_hours"],
        color="#4C78A8",
        zorder=2,
    )

    lower_error = (
        chart_data["median_annual_hours"] - chart_data["minimum_annual_hours"]
    )
    upper_error = (
        chart_data["maximum_annual_hours"] - chart_data["median_annual_hours"]
    )
    ax.errorbar(
        chart_data["median_annual_hours"],
        list(y_positions),
        xerr=[lower_error, upper_error],
        fmt="none",
        ecolor="#444444",
        capsize=4,
        linewidth=1.4,
        zorder=3,
    )

    for bar, value in zip(bars, chart_data["median_annual_hours"]):
        ax.text(
            value + 2,
            bar.get_y() + bar.get_height() / 2,
            f"{value:.1f}",
            va="center",
            fontsize=10,
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.8},
            zorder=4,
        )

    ax.set_yticks(list(y_positions), labels)
    ax.set_title(
        "Typical Annual Hours When Only the Lower-Visibility Option Helps"
    )
    ax.set_xlabel("Hours per year (2021-2025)")
    ax.set_xlim(0, chart_data["maximum_annual_hours"].max() * 1.14)
    ax.grid(axis="x", alpha=0.25)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(
        0.5,
        0.01,
        "Bar = five-year median; line = lowest to highest year. Each airport uses its own visibility range.",
        ha="center",
        fontsize=8.5,
        color="#555555",
    )
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(OUTPUT_CHART, dpi=200, bbox_inches="tight")
    plt.close(fig)

    highest = comparison.loc[comparison["median_annual_hours"].idxmax()]
    lowest_coverage = comparison.loc[
        comparison["minimum_data_coverage_percent"].idxmin()
    ]
    kast_median = comparison.loc[
        comparison["airport"] == "KAST", "median_annual_hours"
    ].iloc[0]
    kcec_median = comparison.loc[
        comparison["airport"] == "KCEC", "median_annual_hours"
    ].iloc[0]

    print(f"comparison_rows={len(comparison)}")
    print(f"highest_median_airport={highest['airport']}")
    print(f"highest_median_hours={highest['median_annual_hours']:.2f}")
    print(f"same_range_KCEC_to_KAST_ratio={kcec_median / kast_median:.2f}")
    print(f"lowest_coverage_airport={lowest_coverage['airport']}")
    print(
        "lowest_year_coverage_percent="
        f"{lowest_coverage['minimum_data_coverage_percent']:.2f}"
    )
    print(f"output_csv={OUTPUT_CSV.name}")
    print(f"output_chart={OUTPUT_CHART.name}")


if __name__ == "__main__":
    main()
