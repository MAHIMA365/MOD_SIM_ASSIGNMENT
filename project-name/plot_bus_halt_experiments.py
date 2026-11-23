"""Generate publication-quality figures from the bus-halt experiment CSVs."""

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import PercentFormatter
from scipy.stats import t


ROOT = Path(__file__).resolve().parent
DATA_DIRECTORY = ROOT / "data"
FIGURES_DIRECTORY = ROOT / "figures"

MODEL_ORDER = ("M/M/1", "M/M/2")
MODEL_LABELS = {"M/M/1": "M/M/1 (one bay)", "M/M/2": "M/M/2 (two bays)"}
COLORS = {"M/M/1": "#0072B2", "M/M/2": "#D55E00"}
MARKERS = {"M/M/1": "o", "M/M/2": "s"}
CONFIDENCE_LEVEL = 0.95


def load_csv(filename: str) -> list[dict[str, str]]:
    path = DATA_DIRECTORY / filename
    with path.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))
    if not rows:
        raise ValueError(f"No experiment rows found in {path}")
    return rows


def require_columns(rows: list[dict[str, str]], columns: set[str], filename: str) -> None:
    missing = columns.difference(rows[0])
    if missing:
        raise ValueError(f"{filename} is missing required columns: {sorted(missing)}")


def paired_summary_by_arrival(
    rows: list[dict[str, str]],
) -> dict[float, dict[str, dict[str, str]]]:
    grouped: dict[float, dict[str, dict[str, str]]] = {}
    for row in rows:
        arrival_rate = float(row["arrival_rate"])
        model = row["model"]
        if model not in MODEL_ORDER:
            raise ValueError(f"Unexpected queue model: {model}")
        model_rows = grouped.setdefault(arrival_rate, {})
        if model in model_rows:
            raise ValueError(f"Duplicate summary row for λ={arrival_rate:g}, {model}")
        model_rows[model] = row

    for arrival_rate, models in grouped.items():
        if set(models) != set(MODEL_ORDER):
            raise ValueError(f"Missing model comparison at λ={arrival_rate:g}")
        one_bay, two_bay = (models[model] for model in MODEL_ORDER)
        for field in ("service_rate", "duration", "replications"):
            if one_bay[field] != two_bay[field]:
                raise ValueError(
                    f"Model inputs differ at λ={arrival_rate:g}: {field}"
                )
    return grouped


def confidence_error(
    row: dict[str, str],
    mean_field: str,
    lower_field: str,
    upper_field: str,
) -> tuple[float, float, float]:
    mean = float(row[mean_field])
    return (
        mean,
        mean - float(row[lower_field]),
        float(row[upper_field]) - mean,
    )


def save_figure(figure: plt.Figure, filename: str) -> None:
    FIGURES_DIRECTORY.mkdir(parents=True, exist_ok=True)
    figure.savefig(
        FIGURES_DIRECTORY / filename,
        dpi=300,
        bbox_inches="tight",
        facecolor="white",
    )
    plt.close(figure)


def plot_arrival_metric(
    grouped: dict[float, dict[str, dict[str, str]]],
    mean_field: str,
    lower_field: str,
    upper_field: str,
    title: str,
    y_label: str,
    filename: str,
) -> None:
    arrival_rates = np.asarray(sorted(grouped), dtype=float)
    figure, axis = plt.subplots(figsize=(8.2, 5.4), constrained_layout=True)

    for model in MODEL_ORDER:
        model_rows = [grouped[rate][model] for rate in arrival_rates]
        means = np.asarray([float(row[mean_field]) for row in model_rows])
        lower = np.asarray([float(row[lower_field]) for row in model_rows])
        upper = np.asarray([float(row[upper_field]) for row in model_rows])
        axis.plot(
            arrival_rates,
            means,
            color=COLORS[model],
            marker=MARKERS[model],
            linewidth=2,
            markersize=5,
            label=MODEL_LABELS[model],
        )
        axis.fill_between(
            arrival_rates,
            lower,
            upper,
            color=COLORS[model],
            alpha=0.16,
            linewidth=0,
        )

    axis.axvline(
        1.0,
        color="#555555",
        linestyle="--",
        linewidth=1.2,
        label=r"One-bay capacity ($\lambda=\mu$)",
    )
    axis.set_yscale("log")
    axis.set_xlabel(
        r"Passenger arrival rate, $\lambda$ "
        "(passengers per simulation time unit)"
    )
    axis.set_ylabel(y_label)
    axis.set_title(
        title
        + "\n"
        + r"$\mu=1.0$ per bay; shaded regions are 95% CIs; "
        r"M/M/1 is unstable for $\lambda\geq\mu$"
    )
    axis.grid(True, which="major", color="#D9DDE2", linewidth=0.8)
    axis.grid(True, which="minor", color="#ECEFF2", linewidth=0.5)
    axis.legend(
        handles=[
            Line2D(
                [0],
                [0],
                color=COLORS[model],
                marker=MARKERS[model],
                linewidth=2,
                label=MODEL_LABELS[model],
            )
            for model in MODEL_ORDER
        ]
        + [
            Patch(facecolor="#777777", alpha=0.2, label="95% confidence interval"),
            Line2D(
                [0],
                [0],
                color="#555555",
                linestyle="--",
                label=r"One-bay capacity ($\lambda=\mu$)",
            ),
        ],
        frameon=False,
        loc="upper left",
    )
    save_figure(figure, filename)


def plot_bay_comparison(rows: list[dict[str, str]]) -> None:
    grouped = paired_summary_by_arrival(rows)
    arrival_rates = np.asarray(sorted(grouped), dtype=float)
    figure, axes = plt.subplots(
        1,
        2,
        figsize=(11.2, 5.2),
        sharex=True,
        constrained_layout=True,
    )
    metrics = (
        (
            axes[0],
            "average_waiting_time_mean",
            "average_waiting_time_ci_low",
            "average_waiting_time_ci_high",
            "Mean waiting time (simulation time units)",
        ),
        (
            axes[1],
            "time_average_queue_length_mean",
            "time_average_queue_length_ci_low",
            "time_average_queue_length_ci_high",
            "Mean time-average queue length (passengers)",
        ),
    )
    offsets = {"M/M/1": -0.07, "M/M/2": 0.07}

    for axis, mean_field, lower_field, upper_field, y_label in metrics:
        for model in MODEL_ORDER:
            for arrival_rate in arrival_rates:
                row = grouped[arrival_rate][model]
                mean, low_error, high_error = confidence_error(
                    row, mean_field, lower_field, upper_field
                )
                marker = MARKERS[model] if row["stable"] == "True" else "^"
                axis.errorbar(
                    arrival_rate + offsets[model],
                    mean,
                    yerr=np.asarray([[low_error], [high_error]]),
                    fmt=marker,
                    color=COLORS[model],
                    ecolor=COLORS[model],
                    markersize=6,
                    capsize=3,
                    linewidth=1.2,
                )
        axis.axvline(1.0, color="#777777", linestyle="--", linewidth=1)
        axis.set_yscale("log")
        axis.set_xticks(arrival_rates)
        axis.set_xlabel(
            r"Passenger arrival rate, $\lambda$ "
            "(passengers per simulation time unit)"
        )
        axis.set_ylabel(y_label)
        axis.grid(True, which="major", color="#D9DDE2", linewidth=0.8)
        axis.grid(True, which="minor", color="#ECEFF2", linewidth=0.5)

    figure.suptitle(
        "One-bay and two-bay comparison under identical inputs\n"
        "Experiment 3; points show means and bars show 95% CIs"
    )
    axes[0].legend(
        handles=[
            Line2D(
                [0],
                [0],
                color=COLORS[model],
                marker=MARKERS[model],
                linestyle="none",
                label=MODEL_LABELS[model],
            )
            for model in MODEL_ORDER
        ]
        + [
            Line2D(
                [0],
                [0],
                color="#333333",
                marker="^",
                linestyle="none",
                label="Unstable condition",
            )
        ],
        frameon=False,
        loc="upper left",
    )
    save_figure(figure, "bay_model_comparison.png")


def plot_utilization(grouped: dict[float, dict[str, dict[str, str]]]) -> None:
    arrival_rates = np.asarray(sorted(grouped), dtype=float)
    figure, axis = plt.subplots(figsize=(8.2, 5.4), constrained_layout=True)
    for model in MODEL_ORDER:
        model_rows = [grouped[rate][model] for rate in arrival_rates]
        means = np.asarray(
            [float(row["overall_utilization_mean"]) for row in model_rows]
        )
        replications = np.asarray(
            [int(row["replications"]) for row in model_rows], dtype=float
        )
        standard_deviations = np.asarray(
            [float(row["overall_utilization_sd"]) for row in model_rows]
        )
        critical_values = np.asarray(
            [t.ppf(0.5 + CONFIDENCE_LEVEL / 2.0, n - 1) for n in replications]
        )
        margins = critical_values * standard_deviations / np.sqrt(replications)
        axis.errorbar(
            arrival_rates,
            means * 100,
            yerr=margins * 100,
            color=COLORS[model],
            marker=MARKERS[model],
            linewidth=2,
            markersize=5,
            capsize=3,
            label=MODEL_LABELS[model],
        )

    axis.axhline(100, color="#555555", linestyle=":", linewidth=1.2)
    axis.axvline(1.0, color="#777777", linestyle="--", linewidth=1)
    axis.set_ylim(0, 105)
    axis.yaxis.set_major_formatter(PercentFormatter(xmax=100))
    axis.set_xlabel(
        r"Passenger arrival rate, $\lambda$ "
        "(passengers per simulation time unit)"
    )
    axis.set_ylabel("Mean overall server utilization (percent)")
    axis.set_title(
        r"Overall server utilization vs arrival rate ($\mu=1.0$ per bay)"
        "\nPoints show means; error bars show 95% CIs"
    )
    axis.grid(True, color="#D9DDE2", linewidth=0.8)
    axis.legend(frameon=False, loc="best")
    save_figure(figure, "arrival_server_utilization.png")


def paired_difference_summary(
    rows: list[dict[str, str]],
    metric: str,
) -> dict[float, tuple[float, float, float]]:
    paired: dict[tuple[float, int], dict[str, dict[str, str]]] = {}
    for row in rows:
        key = (float(row["arrival_rate"]), int(row["replication"]))
        model_rows = paired.setdefault(key, {})
        if row["model"] in model_rows:
            raise ValueError(f"Duplicate raw replication for {key}, {row['model']}")
        model_rows[row["model"]] = row

    differences: dict[float, list[float]] = {}
    seed_by_condition: dict[tuple[float, int], str] = {}
    for (arrival_rate, replication), model_rows in paired.items():
        if set(model_rows) != set(MODEL_ORDER):
            raise ValueError(f"Unpaired raw model run at λ={arrival_rate:g}, r={replication}")
        one_bay, two_bay = (model_rows[model] for model in MODEL_ORDER)
        for field in ("seed", "service_rate", "duration"):
            if one_bay[field] != two_bay[field]:
                raise ValueError(
                    f"Unmatched model inputs at λ={arrival_rate:g}, r={replication}: {field}"
                )
        seed_by_condition[(arrival_rate, replication)] = one_bay["seed"]
        differences.setdefault(arrival_rate, []).append(
            float(one_bay[metric]) - float(two_bay[metric])
        )

    summaries: dict[float, tuple[float, float, float]] = {}
    for arrival_rate, values in differences.items():
        if len(values) < 2:
            raise ValueError(f"At least two paired replications are required at λ={arrival_rate:g}")
        sample = np.asarray(values, dtype=float)
        mean = float(np.mean(sample))
        standard_deviation = float(np.std(sample, ddof=1))
        critical_value = float(
            t.ppf(0.5 + CONFIDENCE_LEVEL / 2.0, df=sample.size - 1)
        )
        margin = critical_value * standard_deviation / np.sqrt(sample.size)
        summaries[arrival_rate] = (mean, mean - margin, mean + margin)
    return summaries


def plot_paired_confidence_intervals(rows: list[dict[str, str]]) -> None:
    figure, axes = plt.subplots(
        1,
        2,
        figsize=(11.2, 5.2),
        sharey=True,
        constrained_layout=True,
    )
    metrics = (
        (
            axes[0],
            "average_waiting_time",
            "Paired mean waiting-time reduction\n(simulation time units)",
            0.1,
        ),
        (
            axes[1],
            "time_average_queue_length",
            "Paired mean queue-length reduction\n(passengers)",
            0.01,
        ),
    )

    first_summaries = paired_difference_summary(rows, metrics[0][1])
    arrival_rates = sorted(first_summaries)
    positions = np.arange(len(arrival_rates))
    for axis, metric, x_label, linear_threshold in metrics:
        summaries = (
            first_summaries
            if metric == metrics[0][1]
            else paired_difference_summary(rows, metric)
        )
        means = np.asarray([summaries[rate][0] for rate in arrival_rates])
        lower = np.asarray([summaries[rate][1] for rate in arrival_rates])
        upper = np.asarray([summaries[rate][2] for rate in arrival_rates])
        axis.errorbar(
            means,
            positions,
            xerr=np.vstack((means - lower, upper - means)),
            fmt="o",
            color="#009E73",
            ecolor="#009E73",
            markersize=6,
            capsize=4,
            linewidth=1.4,
        )
        axis.axvline(0, color="#555555", linestyle="--", linewidth=1)
        axis.set_xscale("symlog", linthresh=linear_threshold)
        axis.set_yticks(positions, [f"{rate:g}" for rate in arrival_rates])
        axis.invert_yaxis()
        axis.set_xlabel(x_label)
        axis.grid(True, axis="x", which="major", color="#D9DDE2", linewidth=0.8)
        axis.grid(True, axis="x", which="minor", color="#ECEFF2", linewidth=0.5)

    axes[0].set_ylabel(
        r"Passenger arrival rate, $\lambda$ "
        "(passengers per simulation time unit)"
    )
    figure.suptitle(
        "Benefit of adding a second bay\n"
        "M/M/1 minus M/M/2 paired replication means; bars are 95% CIs"
    )
    save_figure(figure, "paired_bay_benefit_confidence_intervals.png")


def main() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.labelsize": 10,
            "legend.fontsize": 9,
            "figure.titlesize": 14,
            "savefig.dpi": 300,
        }
    )

    arrival_filename = "experiment_1_arrival_sensitivity.csv"
    arrival_rows = load_csv(arrival_filename)
    require_columns(
        arrival_rows,
        {
            "arrival_rate",
            "service_rate",
            "duration",
            "replications",
            "stable",
            "model",
            "average_waiting_time_mean",
            "average_waiting_time_ci_low",
            "average_waiting_time_ci_high",
            "time_average_queue_length_mean",
            "time_average_queue_length_ci_low",
            "time_average_queue_length_ci_high",
            "overall_utilization_mean",
            "overall_utilization_sd",
        },
        arrival_filename,
    )
    arrival_grouped = paired_summary_by_arrival(arrival_rows)
    plot_arrival_metric(
        arrival_grouped,
        "average_waiting_time_mean",
        "average_waiting_time_ci_low",
        "average_waiting_time_ci_high",
        "Mean passenger waiting time vs arrival rate",
        "Mean waiting time (simulation time units)",
        "arrival_waiting_time.png",
    )
    plot_arrival_metric(
        arrival_grouped,
        "time_average_queue_length_mean",
        "time_average_queue_length_ci_low",
        "time_average_queue_length_ci_high",
        "Mean queue length vs arrival rate",
        "Mean time-average queue length (passengers)",
        "arrival_queue_length.png",
    )
    plot_utilization(arrival_grouped)

    comparison_filename = "experiment_3_bay_comparison.csv"
    comparison_rows = load_csv(comparison_filename)
    require_columns(
        comparison_rows,
        {
            "arrival_rate",
            "service_rate",
            "duration",
            "replications",
            "stable",
            "model",
            "average_waiting_time_mean",
            "average_waiting_time_ci_low",
            "average_waiting_time_ci_high",
            "time_average_queue_length_mean",
            "time_average_queue_length_ci_low",
            "time_average_queue_length_ci_high",
        },
        comparison_filename,
    )
    plot_bay_comparison(comparison_rows)

    raw_filename = "experiment_3_bay_comparison_raw.csv"
    raw_rows = load_csv(raw_filename)
    require_columns(
        raw_rows,
        {
            "arrival_rate",
            "service_rate",
            "duration",
            "replication",
            "seed",
            "model",
            "average_waiting_time",
            "time_average_queue_length",
        },
        raw_filename,
    )
    plot_paired_confidence_intervals(raw_rows)

    print(f"Saved five 300-DPI experiment figures in {FIGURES_DIRECTORY}")


if __name__ == "__main__":
    main()
