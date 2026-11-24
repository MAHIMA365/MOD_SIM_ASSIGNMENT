"""Run and analyze the Python/browser queue-model consistency check."""

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from scipy.stats import t

from queue_simulation import simulate_mm1


ROOT = Path(__file__).resolve().parent
DATA_DIRECTORY = ROOT / "data"
REPLICATIONS = 100
ARRIVAL_RATE = 0.8
SERVICE_RATE = 1.0
DURATION = 50_000.0
PYTHON_SEED_START = 710_000
JAVASCRIPT_SEED_START = 820_000
CONFIDENCE_LEVEL = 0.95
METRICS = (
    "average_waiting_time",
    "time_average_queue_length",
    "throughput",
    "overall_utilization",
)

RAW_FIELDS = [
    "implementation",
    "replication",
    "seed",
    "server_count",
    "arrival_rate",
    "service_rate",
    "duration",
    "stable",
    "arrivals",
    "completed",
    *METRICS,
]


def run_python_replications() -> None:
    DATA_DIRECTORY.mkdir(parents=True, exist_ok=True)
    rows = []
    for replication in range(REPLICATIONS):
        seed = PYTHON_SEED_START + replication
        result = simulate_mm1(
            ARRIVAL_RATE,
            SERVICE_RATE,
            DURATION,
            seed=seed,
        )
        rows.append(
            {
                "implementation": "Python",
                "replication": replication,
                "seed": seed,
                "server_count": 1,
                "arrival_rate": ARRIVAL_RATE,
                "service_rate": SERVICE_RATE,
                "duration": DURATION,
                "stable": result["stable"],
                "arrivals": len(result["arrival_times"]),
                "completed": len(result["completed_passengers"]),
                "average_waiting_time": result["average_waiting_time"],
                "time_average_queue_length": result["time_average_queue_length"],
                "throughput": result["throughput"],
                "overall_utilization": result["overall_utilization"],
            }
        )

    path = DATA_DIRECTORY / "python_consistency_replications.csv"
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=RAW_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {len(rows)} Python replications to {path}")
    for metric in METRICS:
        values = np.asarray([float(row[metric]) for row in rows])
        print(
            f"{metric}: mean={np.mean(values):.9f}, "
            f"sample_sd={np.std(values, ddof=1):.9f}"
        )


def load_python_rows() -> dict[str, np.ndarray]:
    path = DATA_DIRECTORY / "python_consistency_replications.csv"
    with path.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))
    if len(rows) != REPLICATIONS:
        raise ValueError(f"Expected {REPLICATIONS} Python rows, found {len(rows)}")
    for row in rows:
        if (
            int(row["server_count"]) != 1
            or float(row["arrival_rate"]) != ARRIVAL_RATE
            or float(row["service_rate"]) != SERVICE_RATE
            or float(row["duration"]) != DURATION
        ):
            raise ValueError("Python replication parameters do not match the design")
    return {
        metric: np.asarray([float(row[metric]) for row in rows], dtype=float)
        for metric in METRICS
    }


def load_javascript_summary() -> dict[str, dict[str, float]]:
    path = DATA_DIRECTORY / "javascript_consistency_summary.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    expected = {
        "implementation": "JavaScript",
        "replications": REPLICATIONS,
        "server_count": 1,
        "arrival_rate": ARRIVAL_RATE,
        "service_rate": SERVICE_RATE,
        "duration": DURATION,
        "seed_start": JAVASCRIPT_SEED_START,
        "seed_end": JAVASCRIPT_SEED_START + REPLICATIONS - 1,
    }
    for key, value in expected.items():
        if data.get(key) != value:
            raise ValueError(f"JavaScript summary has unexpected {key}: {data.get(key)!r}")
    return data["metrics"]


def compare() -> None:
    python_values = load_python_rows()
    javascript = load_javascript_summary()
    rows = []
    for metric in METRICS:
        python_sample = python_values[metric]
        python_mean = float(np.mean(python_sample))
        python_sd = float(np.std(python_sample, ddof=1))
        javascript_mean = float(javascript[metric]["mean"])
        javascript_sd = float(javascript[metric]["sample_sd"])
        javascript_n = int(javascript[metric]["replications"])
        if python_sample.size != javascript_n:
            raise ValueError(f"Replication-count mismatch for {metric}")

        difference = python_mean - javascript_mean
        python_variance_term = python_sd**2 / python_sample.size
        javascript_variance_term = javascript_sd**2 / javascript_n
        standard_error = float(np.sqrt(python_variance_term + javascript_variance_term))
        denominator = (
            python_variance_term**2 / (python_sample.size - 1)
            + javascript_variance_term**2 / (javascript_n - 1)
        )
        degrees_of_freedom = (python_variance_term + javascript_variance_term) ** 2 / denominator
        critical_value = float(
            t.ppf((1 + CONFIDENCE_LEVEL) / 2, degrees_of_freedom)
        )
        tolerance = critical_value * standard_error
        lower = difference - tolerance
        upper = difference + tolerance
        relative_difference_percent = (
            abs(difference / python_mean) * 100 if python_mean != 0 else float("nan")
        )

        rows.append(
            {
                "metric": metric,
                "arrival_rate": ARRIVAL_RATE,
                "service_rate": SERVICE_RATE,
                "duration": DURATION,
                "server_count": 1,
                "replications_per_implementation": REPLICATIONS,
                "python_seed_start": PYTHON_SEED_START,
                "python_seed_end": PYTHON_SEED_START + REPLICATIONS - 1,
                "javascript_seed_start": JAVASCRIPT_SEED_START,
                "javascript_seed_end": JAVASCRIPT_SEED_START + REPLICATIONS - 1,
                "python_mean": python_mean,
                "python_sample_sd": python_sd,
                "javascript_mean": javascript_mean,
                "javascript_sample_sd": javascript_sd,
                "difference_python_minus_javascript": difference,
                "absolute_difference": abs(difference),
                "relative_difference_percent_of_python_mean": relative_difference_percent,
                "welch_95ci_difference_low": lower,
                "welch_95ci_difference_high": upper,
                "predeclared_tolerance_half_width": tolerance,
                "statistically_consistent": lower <= 0 <= upper,
            }
        )

    output = DATA_DIRECTORY / "python_javascript_consistency.csv"
    with output.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved implementation comparison to {output}")
    for row in rows:
        print(
            f"{row['metric']}: Python={row['python_mean']:.9f} "
            f"(SD {row['python_sample_sd']:.9f}), "
            f"JavaScript={row['javascript_mean']:.9f} "
            f"(SD {row['javascript_sample_sd']:.9f}), "
            f"abs_diff={row['absolute_difference']:.9f}, "
            f"relative_diff={row['relative_difference_percent_of_python_mean']:.4f}%, "
            f"95% difference CI=[{row['welch_95ci_difference_low']:.9f}, "
            f"{row['welch_95ci_difference_high']:.9f}], "
            f"tolerance=+/-{row['predeclared_tolerance_half_width']:.9f}, "
            f"consistent={row['statistically_consistent']}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("python", "compare"))
    action = parser.parse_args().action
    if action == "python":
        run_python_replications()
    else:
        compare()


if __name__ == "__main__":
    main()
