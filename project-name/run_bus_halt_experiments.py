"""Run controlled M/M/1 and M/M/2 bus-halt experiments."""

import csv
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from scipy.stats import t

from queue_simulation import simulate_mm1, simulate_mm2


REPLICATIONS = 40
DURATION = 50_000.0
CONFIDENCE_LEVEL = 0.95
SEED_BASE = 200_000

OUTPUT_DIRECTORY = Path(__file__).resolve().parent
DATA_DIRECTORY = OUTPUT_DIRECTORY / "data"


RAW_FIELDS = [
    "experiment",
    "model",
    "server_count",
    "arrival_rate",
    "service_rate",
    "duration",
    "replication",
    "seed",
    "stable",
    "arrivals",
    "completed",
    "waiting",
    "in_service",
    "average_waiting_time",
    "time_average_queue_length",
    "average_system_time",
    "throughput",
    "overall_utilization",
]

SUMMARY_FIELDS = [
    "experiment",
    "model",
    "server_count",
    "arrival_rate",
    "service_rate",
    "duration",
    "replications",
    "stable",
    "average_waiting_time_mean",
    "average_waiting_time_sd",
    "average_waiting_time_ci_low",
    "average_waiting_time_ci_high",
    "time_average_queue_length_mean",
    "time_average_queue_length_sd",
    "time_average_queue_length_ci_low",
    "time_average_queue_length_ci_high",
    "throughput_mean",
    "throughput_sd",
    "overall_utilization_mean",
    "overall_utilization_sd",
]


def confidence_interval(values: list[float]) -> tuple[float, float, float, float]:
    sample = np.asarray(values, dtype=float)
    sample = sample[np.isfinite(sample)]
    if sample.size < 2:
        mean = float(sample[0]) if sample.size else float("nan")
        return mean, float("nan"), float("nan"), float("nan")

    mean = float(np.mean(sample))
    standard_deviation = float(np.std(sample, ddof=1))
    standard_error = standard_deviation / np.sqrt(sample.size)
    critical_value = float(t.ppf((1.0 + CONFIDENCE_LEVEL) / 2.0, df=sample.size - 1))
    margin = critical_value * standard_error
    return mean, standard_deviation, mean - margin, mean + margin


def seed_for(experiment_index: int, parameter_index: int, replication: int) -> int:
    return SEED_BASE + experiment_index * 100_000 + parameter_index * 100 + replication


def validate_conservation(result: dict[str, object]) -> None:
    arrivals = np.asarray(result["arrival_times"], dtype=float)
    completed = len(result["completed_passengers"])
    waiting = len(result["passengers_waiting"])
    in_service = len(result["passengers_in_service"])
    if completed + waiting + in_service != arrivals.size:
        raise RuntimeError(
            "Passenger conservation failed: "
            f"completed={completed}, waiting={waiting}, "
            f"in_service={in_service}, arrivals={arrivals.size}"
        )


def validate_events(result: dict[str, object], server_count: int) -> None:
    arrivals = np.asarray(result["arrival_times"], dtype=float)
    starts = np.asarray(result["service_start_times"], dtype=float)
    completions = np.asarray(result["service_completion_times"], dtype=float)
    assignments = np.asarray(result["server_assignments"], dtype=int)
    started = np.isfinite(starts)

    if not np.all(np.diff(arrivals) > 0):
        raise RuntimeError("Arrival timestamps are not strictly increasing")
    if np.any(starts[started] < arrivals[started]):
        raise RuntimeError("A passenger starts service before arrival")
    if np.any(completions[started] < starts[started]):
        raise RuntimeError("A passenger completes service before starting")

    for server_number in range(1, server_count + 1):
        on_server = started & (assignments == server_number)
        intervals = sorted(
            (float(start), float(completion))
            for start, completion in zip(starts[on_server], completions[on_server])
        )
        if any(
            previous[1] > following[0] + 1e-12
            for previous, following in zip(intervals, intervals[1:])
        ):
            raise RuntimeError(f"Server {server_number} has overlapping services")


def run_replication(
    experiment: str,
    model: str,
    server_count: int,
    arrival_rate: float,
    service_rate: float,
    replication: int,
    seed: int,
) -> dict[str, object]:
    if model == "M/M/1":
        result = simulate_mm1(arrival_rate, service_rate, DURATION, seed=seed)
    else:
        result = simulate_mm2(arrival_rate, service_rate, DURATION, seed=seed)

    validate_conservation(result)
    validate_events(result, server_count)

    arrivals = np.asarray(result["arrival_times"], dtype=float)
    return {
        "experiment": experiment,
        "model": model,
        "server_count": server_count,
        "arrival_rate": arrival_rate,
        "service_rate": service_rate,
        "duration": DURATION,
        "replication": replication,
        "seed": seed,
        "stable": bool(result["stable"]),
        "arrivals": arrivals.size,
        "completed": len(result["completed_passengers"]),
        "waiting": len(result["passengers_waiting"]),
        "in_service": len(result["passengers_in_service"]),
        "average_waiting_time": float(result["average_waiting_time"]),
        "time_average_queue_length": float(result["time_average_queue_length"]),
        "average_system_time": float(result["average_system_time"]),
        "throughput": float(result["throughput"]),
        "overall_utilization": float(result["overall_utilization"]),
    }


def summarize(
    experiment: str,
    model: str,
    server_count: int,
    arrival_rate: float,
    service_rate: float,
    replications: list[dict[str, object]],
) -> dict[str, object]:
    def metric(name: str) -> list[float]:
        return [float(row[name]) for row in replications]

    waiting_mean, waiting_sd, waiting_low, waiting_high = confidence_interval(
        metric("average_waiting_time")
    )
    queue_mean, queue_sd, queue_low, queue_high = confidence_interval(
        metric("time_average_queue_length")
    )
    throughput_mean, throughput_sd, _, _ = confidence_interval(metric("throughput"))
    utilization_mean, utilization_sd, _, _ = confidence_interval(
        metric("overall_utilization")
    )
    stable = bool(replications[0]["stable"])

    return {
        "experiment": experiment,
        "model": model,
        "server_count": server_count,
        "arrival_rate": arrival_rate,
        "service_rate": service_rate,
        "duration": DURATION,
        "replications": len(replications),
        "stable": stable,
        "average_waiting_time_mean": waiting_mean,
        "average_waiting_time_sd": waiting_sd,
        "average_waiting_time_ci_low": waiting_low,
        "average_waiting_time_ci_high": waiting_high,
        "time_average_queue_length_mean": queue_mean,
        "time_average_queue_length_sd": queue_sd,
        "time_average_queue_length_ci_low": queue_low,
        "time_average_queue_length_ci_high": queue_high,
        "throughput_mean": throughput_mean,
        "throughput_sd": throughput_sd,
        "overall_utilization_mean": utilization_mean,
        "overall_utilization_sd": utilization_sd,
    }


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def run_model_replications(
    experiment_name: str,
    experiment_index: int,
    parameter_index: int,
    model: str,
    server_count: int,
    arrival_rate: float,
    service_rate: float,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    model_replications: list[dict[str, object]] = []
    for replication in range(REPLICATIONS):
        seed = seed_for(experiment_index, parameter_index, replication)
        model_replications.append(
            run_replication(
                experiment_name,
                model,
                server_count,
                arrival_rate,
                service_rate,
                replication,
                seed,
            )
        )

    summary = summarize(
        experiment_name,
        model,
        server_count,
        arrival_rate,
        service_rate,
        model_replications,
    )
    return model_replications, summary


def run_experiment(
    experiment_name: str,
    experiment_index: int,
    combinations: list[tuple[float, float]],
    summary_filename: str,
    raw_filename: str,
) -> list[dict[str, object]]:
    raw_rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []
    tasks = []
    for parameter_index, (arrival_rate, service_rate) in enumerate(combinations):
        for model, server_count in (("M/M/1", 1), ("M/M/2", 2)):
            tasks.append(
                (
                    experiment_name,
                    experiment_index,
                    parameter_index,
                    model,
                    server_count,
                    arrival_rate,
                    service_rate,
                )
            )

    workers = min(6, os.cpu_count() or 1)
    with ProcessPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(run_model_replications, *zip(*tasks)))

    for model_replications, summary in results:
        raw_rows.extend(model_replications)
        summary_rows.append(summary)

    write_csv(DATA_DIRECTORY / raw_filename, RAW_FIELDS, raw_rows)
    write_csv(DATA_DIRECTORY / summary_filename, SUMMARY_FIELDS, summary_rows)
    return summary_rows


def main() -> None:
    DATA_DIRECTORY.mkdir(parents=True, exist_ok=True)

    experiment_1 = run_experiment(
        "Experiment 1: Arrival rate sensitivity",
        1,
        [(arrival_rate, 1.0) for arrival_rate in
         (0.20, 0.40, 0.60, 0.80, 0.95, 1.00, 1.20, 1.40, 1.60, 1.80)],
        "experiment_1_arrival_sensitivity.csv",
        "experiment_1_arrival_sensitivity_raw.csv",
    )

    experiment_2 = run_experiment(
        "Experiment 2: Service rate sensitivity",
        2,
        [(0.90, service_rate) for service_rate in
         (0.60, 0.75, 0.90, 1.00, 1.20, 1.50, 2.00)],
        "experiment_2_service_sensitivity.csv",
        "experiment_2_service_sensitivity_raw.csv",
    )

    experiment_3 = run_experiment(
        "Experiment 3: One bay vs two bays",
        3,
        [(arrival_rate, 1.0) for arrival_rate in (0.20, 0.90, 1.80)],
        "experiment_3_bay_comparison.csv",
        "experiment_3_bay_comparison_raw.csv",
    )

    variability_rows: list[dict[str, object]] = []
    for row in experiment_1 + experiment_2 + experiment_3:
        variability_rows.append(
            {
                "experiment": row["experiment"],
                "model": row["model"],
                "server_count": row["server_count"],
                "arrival_rate": row["arrival_rate"],
                "service_rate": row["service_rate"],
                "duration": row["duration"],
                "replications": row["replications"],
                "average_waiting_time_mean": row["average_waiting_time_mean"],
                "average_waiting_time_sd": row["average_waiting_time_sd"],
                "average_waiting_time_ci_low": row["average_waiting_time_ci_low"],
                "average_waiting_time_ci_high": row["average_waiting_time_ci_high"],
                "time_average_queue_length_mean":
                    row["time_average_queue_length_mean"],
                "time_average_queue_length_sd":
                    row["time_average_queue_length_sd"],
                "time_average_queue_length_ci_low":
                    row["time_average_queue_length_ci_low"],
                "time_average_queue_length_ci_high":
                    row["time_average_queue_length_ci_high"],
            }
        )
    write_csv(
        DATA_DIRECTORY / "experiment_4_variability.csv",
        [
            "experiment",
            "model",
            "server_count",
            "arrival_rate",
            "service_rate",
            "duration",
            "replications",
            "average_waiting_time_mean",
            "average_waiting_time_sd",
            "average_waiting_time_ci_low",
            "average_waiting_time_ci_high",
            "time_average_queue_length_mean",
            "time_average_queue_length_sd",
            "time_average_queue_length_ci_low",
            "time_average_queue_length_ci_high",
        ],
        variability_rows,
    )

    print(
        f"Completed {REPLICATIONS} replications per model/parameter combination "
        f"at duration {DURATION:g}"
    )
    print(f"Saved experiment CSV files in {DATA_DIRECTORY}")


if __name__ == "__main__":
    main()
