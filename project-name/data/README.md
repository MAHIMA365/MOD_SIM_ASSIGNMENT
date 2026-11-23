# Data

The CSV files in this folder contain generated simulation experiments, not collected personal or external data.

| File | Description |
|---|---|
| `experiment_1_arrival_sensitivity.csv` | Summary statistics and 95% confidence intervals for fixed service rate and varying arrival rate |
| `experiment_1_arrival_sensitivity_raw.csv` | One row per M/M/1 or M/M/2 replication for Experiment 1 |
| `experiment_2_service_sensitivity.csv` | Summary statistics and 95% confidence intervals for fixed arrival rate and varying service rate |
| `experiment_2_service_sensitivity_raw.csv` | One row per M/M/1 or M/M/2 replication for Experiment 2 |
| `experiment_3_bay_comparison.csv` | Summary statistics and 95% confidence intervals directly comparing one and two bays under equal inputs |
| `experiment_3_bay_comparison_raw.csv` | One row per M/M/1 or M/M/2 replication for Experiment 3 |
| `experiment_4_variability.csv` | Replication-based waiting-time and queue-length means, standard deviations, and 95% confidence intervals for conditions in Experiments 1–3 |

Each condition uses 40 independent replications and a 50,000-time-unit horizon. The raw files record model, bay count, arrival and service rates, horizon, replication index, seed, stability, and the measured outputs. Seeds are reproducible and distinct across conditions and replications; corresponding one-bay/two-bay runs share the seed to match arrival streams. Summary files report sample means and standard deviations, with two-sided 95% Student-t confidence intervals for average waiting time and time-average queue length.

The waiting-time metric includes only passengers completed by the horizon. It excludes passengers still waiting, which can understate waits in overloaded finite-horizon runs. The queue-length metric includes passengers waiting throughout the observation period. Unstable scenarios should not be interpreted as steady-state results. The experiment runner is `run_bus_halt_experiments.py`.

The five publication-quality plots in `figures/` are generated directly from
these summary and raw CSVs by `plot_bus_halt_experiments.py`. The script does not
modify experiment data; it validates paired model inputs and derives the
Experiment 3 paired-difference confidence intervals from the raw replication
rows.
