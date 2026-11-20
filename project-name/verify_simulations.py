"""Run replicated M/M/1 and M/M/2 verification; write CSV and PNG artifacts."""

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import t

from arrival_generator import generate_arrival_times, generate_service_times
from queue_simulation import (
    simulate_mm1,
    simulate_mm2,
    theoretical_mm1_metrics,
    theoretical_mm2_metrics,
)


REPLICATIONS = 20
DURATION = 20_000.0
SERVICE_RATE = 1.0
BASE_SEED = 10_000
OUTPUT_DIRECTORY = Path(__file__).resolve().parent
CSV_PATH = OUTPUT_DIRECTORY / "verification_results.csv"
FIGURE_PATH = OUTPUT_DIRECTORY / "figures" / "verification.png"


def _check_invariants(result: dict[str, object], server_count: int) -> dict[str, bool]:
    arrivals = np.asarray(result["arrival_times"], dtype=float)
    starts = np.asarray(result["service_start_times"], dtype=float)
    completions = np.asarray(result["service_completion_times"], dtype=float)
    waits = np.asarray(result["waiting_times"], dtype=float)
    assignments = np.asarray(result["server_assignments"], dtype=int)
    statuses = np.asarray(result["passenger_status"])
    duration = float(result["duration"])
    started = np.isfinite(starts)
    completed = statuses == "completed"
    expected_completed = np.isfinite(completions) & (completions <= duration)

    completed_ids = set(result["completed_passengers"])
    waiting_ids = set(result["passengers_waiting"])
    serving_ids = set(result["passengers_in_service"])
    known_ids = completed_ids | waiting_ids | serving_ids
    all_ids = set(range(1, len(arrivals) + 1))

    non_overlapping = True
    for server_number in range(1, server_count + 1):
        on_server = started & (assignments == server_number)
        intervals = sorted(zip(starts[on_server], completions[on_server]))
        non_overlapping &= all(
            previous[1] <= following[0] + 1e-12
            for previous, following in zip(intervals, intervals[1:])
        )

    states_match_horizon = np.array_equal(completed, expected_completed)
    return {
        "arrival_times_sorted_and_in_horizon": bool(
            np.all(np.isfinite(arrivals))
            and np.all(np.diff(arrivals) > 0)
            and np.all((arrivals >= 0) & (arrivals <= duration))
        ),
        "event_order_and_fcfs": bool(
            np.all(starts[started] >= arrivals[started])
            and np.all(waits[started] >= 0)
            and np.allclose(waits[started], starts[started] - arrivals[started])
            and np.all(np.diff(starts[started]) >= -1e-12)
        ),
        "service_durations_positive": bool(
            np.all(np.isfinite(completions[started]))
            and np.all(completions[started] > starts[started])
        ),
        "no_server_overlap": bool(non_overlapping),
        "passenger_conservation": bool(
            len(completed_ids) + len(waiting_ids) + len(serving_ids) == len(arrivals)
            and known_ids == all_ids
        ),
        "termination_states_match_horizon": bool(
            states_match_horizon
            and len(waiting_ids) == np.count_nonzero(statuses == "waiting")
            and len(serving_ids) == np.count_nonzero(statuses == "in_service")
        ),
        "utilization_and_queue_bounds": bool(
            0 <= result["time_average_queue_length"]
            and 0 <= result["overall_utilization"] <= 1
            and all(0 <= value <= 1 for value in result["per_server_utilization"])
        ),
    }


def _confidence_interval(values: list[float]) -> tuple[float, float, float]:
    sample = np.asarray(values, dtype=float)
    mean = float(np.mean(sample))
    margin = float(t.ppf(0.975, df=sample.size - 1) * np.std(sample, ddof=1) / np.sqrt(sample.size))
    return mean, mean - margin, mean + margin


def _verification_row(
    check: str,
    expected: float,
    samples: list[float],
) -> dict[str, str]:
    mean, lower, upper = _confidence_interval(samples)
    difference = mean - expected
    relative_error = abs(difference) / abs(expected) if expected else float("nan")
    passed = lower <= expected <= upper
    return {
        "Check": check,
        "Theoretical expected value": f"{expected:.8g}",
        "Simulated value": f"{mean:.8g}",
        "95% confidence interval": f"[{lower:.8g}, {upper:.8g}]",
        "Difference": f"{difference:.8g}",
        "Relative error": f"{relative_error:.4%}" if np.isfinite(relative_error) else "n/a",
        "Pass/fail": "PASS" if passed else "FAIL",
    }


def main() -> None:
    model_specs = {
        "M/M/1": (simulate_mm1, theoretical_mm1_metrics, 1),
        "M/M/2": (simulate_mm2, theoretical_mm2_metrics, 2),
    }
    scenarios = [
        ("low arrival", {"M/M/1": 0.1, "M/M/2": 0.1}),
        ("same lambda comparison", {"M/M/1": 0.9, "M/M/2": 0.9}),
        ("near capacity", {"M/M/1": 0.9, "M/M/2": 1.8}),
    ]
    rows: list[dict[str, str]] = []
    plot_data: dict[tuple[str, str], dict[str, object]] = {}

    for scenario_name, model_rates in scenarios:
        for model_name, arrival_rate in model_rates.items():
            simulate, theory_function, server_count = model_specs[model_name]
            theoretical = theory_function(arrival_rate, SERVICE_RATE)
            replications: list[dict[str, object]] = []
            invariant_results: dict[str, list[bool]] = {}

            for replication in range(REPLICATIONS):
                result = simulate(
                    arrival_rate,
                    SERVICE_RATE,
                    duration=DURATION,
                    seed=BASE_SEED + replication,
                )
                replications.append(result)
                for name, passed in _check_invariants(result, server_count).items():
                    invariant_results.setdefault(name, []).append(passed)

            metrics: dict[str, list[float]] = {
                "arrival_rate_estimate": [],
                "service_rate_estimate": [],
                "rho": [],
                "Wq": [],
                "Lq": [],
                "W": [],
                "throughput": [],
                "overall_utilization": [],
            }
            for server_number in range(1, server_count + 1):
                metrics[f"bay_{server_number}_utilization"] = []

            for result in replications:
                arrivals = np.asarray(result["arrival_times"], dtype=float)
                starts = np.asarray(result["service_start_times"], dtype=float)
                completions = np.asarray(result["service_completion_times"], dtype=float)
                started = np.isfinite(starts)
                service_durations = completions[started] - starts[started]
                metrics["arrival_rate_estimate"].append(len(arrivals) / DURATION)
                metrics["service_rate_estimate"].append(1.0 / float(np.mean(service_durations)))
                metrics["rho"].append(float(result["overall_utilization"]))
                metrics["Wq"].append(float(result["average_waiting_time"]))
                metrics["Lq"].append(float(result["time_average_queue_length"]))
                metrics["W"].append(float(result["average_system_time"]))
                metrics["throughput"].append(float(result["throughput"]))
                metrics["overall_utilization"].append(float(result["overall_utilization"]))
                for server_number, utilization in enumerate(result["per_server_utilization"], start=1):
                    metrics[f"bay_{server_number}_utilization"].append(float(utilization))

            expected_metrics = {
                "arrival_rate_estimate": arrival_rate,
                "service_rate_estimate": SERVICE_RATE,
                "rho": theoretical["rho"],
                "Wq": theoretical["Wq"],
                "Lq": theoretical["Lq"],
                "W": theoretical["W"],
                "throughput": arrival_rate,
                "overall_utilization": theoretical["rho"],
            }
            for server_number in range(1, server_count + 1):
                expected_metrics[f"bay_{server_number}_utilization"] = theoretical["rho"]

            for metric, samples in metrics.items():
                rows.append(
                    _verification_row(
                        f"{model_name} / {scenario_name} / {metric}",
                        expected_metrics[metric],
                        samples,
                    )
                )

            for invariant, outcomes in invariant_results.items():
                rows.append(
                    {
                        "Check": f"{model_name} / {scenario_name} / {invariant}",
                        "Theoretical expected value": "true for every replication",
                        "Simulated value": f"{sum(outcomes)}/{len(outcomes)} passed",
                        "95% confidence interval": "n/a",
                        "Difference": "n/a",
                        "Relative error": "n/a",
                        "Pass/fail": "PASS" if all(outcomes) else "FAIL",
                    }
                )

            plot_data[(model_name, scenario_name)] = {
                "rho": theoretical["rho"],
                "mean": _confidence_interval(metrics["Wq"])[0],
                "lower": _confidence_interval(metrics["Wq"])[1],
                "upper": _confidence_interval(metrics["Wq"])[2],
            }

    comparison_values = [
        plot_data[("M/M/1", "same lambda comparison")]["mean"],
        plot_data[("M/M/2", "same lambda comparison")]["mean"],
    ]
    rows.append(
        {
            "Check": "same lambda: M/M/2 has lower average waiting time",
            "Theoretical expected value": "M/M/2 < M/M/1",
            "Simulated value": f"{comparison_values[1]:.8g} < {comparison_values[0]:.8g}",
            "95% confidence interval": "see corresponding metric rows",
            "Difference": f"{comparison_values[1] - comparison_values[0]:.8g}",
            "Relative error": "n/a",
            "Pass/fail": "PASS" if comparison_values[1] < comparison_values[0] else "FAIL",
        }
    )

    with CSV_PATH.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    figure, axes = plt.subplots(1, 2, figsize=(12, 5), constrained_layout=True)
    utilization_grid = np.linspace(0.005, 0.95, 200)
    for axis, model_name in zip(axes, ("M/M/1", "M/M/2")):
        theory_function = model_specs[model_name][1]
        server_count = model_specs[model_name][2]
        theoretical_waits = [
            theory_function(
                utilization * server_count * SERVICE_RATE,
                SERVICE_RATE,
            )["Wq"]
            for utilization in utilization_grid
        ]
        axis.plot(utilization_grid, theoretical_waits, color="black", label="theory")
        for scenario_name, _ in scenarios:
            point = plot_data.get((model_name, scenario_name))
            if point is None:
                continue
            axis.errorbar(
                point["rho"],
                point["mean"],
                yerr=[[point["mean"] - point["lower"]], [point["upper"] - point["mean"]]],
                marker="o",
                capsize=3,
                linestyle="none",
                label=scenario_name,
            )
        axis.set_title(model_name)
        axis.set_xlabel("Utilisation per server, rho")
        axis.set_ylabel("Average waiting time, Wq")
        axis.grid(True, alpha=0.25)
        axis.legend()

    FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(FIGURE_PATH, dpi=180)
    plt.close(figure)

    print(f"Replications per scenario: {REPLICATIONS}; duration each: {DURATION:g}")
    print(f"CSV verification table: {CSV_PATH}")
    print(f"Verification graph: {FIGURE_PATH}")
    for row in rows:
        if row["Pass/fail"] == "FAIL":
            print("FAIL:", row["Check"], row["Simulated value"], row["95% confidence interval"])
    print(f"Verification rows: {len(rows)}; passed: {sum(row['Pass/fail'] == 'PASS' for row in rows)}")


if __name__ == "__main__":
    main()