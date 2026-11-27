# Simulation of Passenger Queues at a Bus Halt: Comparing One and Two Boarding Bays.

This project uses queueing theory and discrete-event simulation to compare passenger waiting and service performance at a bus halt with one boarding bay (M/M/1) and two boarding bays (M/M/2).

**Live demo:** The browser-only demo is implemented in [`docs/index.html`](docs/index.html). The repository-root `docs/` folder can be published with GitHub Pages. **Notebook:** The complete Python notebook is [`notebook/bus_halt_queue_simulation.ipynb`](notebook/bus_halt_queue_simulation.ipynb).

**User guide:** See [`USER_GUIDE.md`](USER_GUIDE.md) for controls, examples and result interpretation.

## The problem

Passengers arriving at a bus halt may wait in a queue before boarding. The available number of boarding bays and the rates at which passengers arrive and are served affect waiting time and queue build-up.

This project simulates passenger arrivals and service durations, then compares one boarding bay (M/M/1) with two boarding bays (M/M/2) under different arrival and service rates. The comparison considers average waiting time, average queue length, throughput, and utilisation.

## Quick start

**Notebook:** Open [`notebook/bus_halt_queue_simulation.ipynb`](notebook/bus_halt_queue_simulation.ipynb) locally or upload it to Google Colab, then select *Runtime → Run all*.

**Web demo:** Open [`docs/index.html`](docs/index.html) directly in a modern browser. It uses only local HTML, CSS, and JavaScript and needs no server or network connection. For GitHub Pages, publish the repository-root `docs/` folder from `main`; the live site is not available until Pages is enabled and its public URL is tested.

**Run locally (optional):**

```bash
pip install -r requirements.txt
jupyter notebook notebook/bus_halt_queue_simulation.ipynb
```

### Arrival generation example

Generate passenger arrival timestamps for a five-unit simulation with an arrival
rate of 2 passengers per time unit. The fixed seed makes the output repeatable.

```python
from arrival_generator import generate_arrival_times

arrivals = generate_arrival_times(arrival_rate=2.0, duration=5.0, seed=42)
print(arrivals[:5])
```

Example output:

```text
[0.1281 0.5399 0.6161 0.7963 1.9776]
```

## Using the demo

Open [`docs/index.html`](docs/index.html) in a modern browser. Choose one or two
boarding bays, set arrival rate λ, per-bay service rate μ, simulation duration,
and a random seed, then select **Start simulation**. **Pause simulation**
pauses the event animation; **Resume** continues the same run. **Reset** clears
the run and applies the current inputs. The results are calculated from the
displayed stochastic run, not from hard-coded example values. The About and
How to use sections in the page describe the model and metrics.

## Model and mathematics

The project compares an M/M/1 queue, representing one boarding bay, with an M/M/2 queue, representing two boarding bays with a shared FCFS queue. Passenger inter-arrival intervals and service durations are generated randomly, and next-event time advancement tracks the system. Arrival and service rates are varied to examine their effects on average waiting time, average queue length, throughput, and utilisation. Assumptions, parameter definitions, equations and metric conventions are documented in [THEORY.md](THEORY.md).

## Verification

Verification has been implemented and run. Stable M/M/1 and M/M/2 results are checked against closed-form queueing values, event-level passenger and server accounting is tested, and 69 automated Python tests pass. Detailed results are in [`verification_results.csv`](verification_results.csv).

**Verification plot:** [`figures/verification.png`](figures/verification.png).

## Concepts applied

The project applies M/M/1 and M/M/2 queueing models to represent one and two boarding bays, respectively, and discrete-event simulation to model passenger arrivals and service. Random arrival intervals and service durations are used to explore how changing arrival and service rates affects queue performance. Replication studies, confidence intervals, inverse-transform sampling and analytical verification provide the statistical and mathematical methods.

## Results

### Experimental design

The experiments use the project's M/M/1 and shared-queue M/M/2 models. Each
condition has 40 replications of 50,000 simulation time units, starts empty,
and has no warm-up period. Arrival and per-bay service rates are held identical
between the one-bay and two-bay models. Seeds are distinct between replications
and parameter combinations; each paired one-bay/two-bay condition uses the
same seed to generate the same arrival stream.

| Experiment | Fixed parameter | Varied parameter |
|---|---|---|
| 1: Arrival sensitivity | Service rate μ = 1.0 | Arrival rate λ = 0.20, 0.40, 0.60, 0.80, 0.95, 1.00, 1.20, 1.40, 1.60, 1.80 |
| 2: Service sensitivity | Arrival rate λ = 0.90 | Per-bay service rate μ = 0.60, 0.75, 0.90, 1.00, 1.20, 1.50, 2.00 |
| 3: Bay comparison | Per-bay service rate μ = 1.0 | Arrival rate λ = 0.20, 0.90, 1.80 |
| 4: Variability | Derived from Experiments 1–3 | Replication-level variability for each condition |

Rates are in passengers per simulation time unit. For each condition and model,
the CSV summaries report the replication mean, sample standard deviation, and
two-sided 95% Student-t confidence interval for average waiting time and
time-average queue length. Raw files retain each replication's seed, parameters,
and performance measures.

### Findings from generated results

The generated results show that two bays reduce both measured waiting time and
time-average queue length in every matched condition tested. This includes low
arrival demand; one bay is more heavily utilized there, but the model does not
include a cost for operating a second bay.

With μ = 1.0, increasing λ causes waiting and queues to grow sharply for one
bay as it approaches capacity. At λ = 0.95, both systems are stable, but the
mean waiting time is 18.765 time units (95% CI 17.870–19.659) for one bay
versus 0.292 (0.289–0.295) for two; mean queue length is 17.856
(16.985–18.727) versus 0.278 (0.275–0.281). At λ = 1.20, the one-bay model is
unstable (λ ≥ μ), with a mean time-average queue length of 5,008.55
(4,943.93–5,073.17), while the two-bay model is stable and has a mean queue
length of 0.672 (0.665–0.679). At λ = 1.80, one bay remains unstable and has a
mean queue length of 20,004.10; two bays remain stable and average 7.766
(7.592–7.940).

Increasing service rate at fixed λ = 0.90 improves both configurations. For
example, when μ increases from 1.0 to 2.0, one-bay mean waiting time decreases
from 9.103 to 0.413, and two-bay mean waiting time decreases from 0.257 to
0.0266. The one-bay system is unstable for μ ≤ 0.90, whereas all tested
two-bay service-rate conditions are stable.

Replication variability is especially important near or beyond one-bay
capacity. At λ = μ = 1.0, the one-bay waiting-time estimate has a sample
standard deviation of 93.44 and a 95% CI of 138.50–198.26; the two-bay estimate
has a standard deviation of 0.0112 and a CI of 0.3296–0.3368. This reinforces
that one-bay estimates near capacity are much less stable.

**Metric limitation:** The simulator's average waiting time includes only
passengers completed by the end of the run. Passengers still waiting are not
included in that waiting-time mean, so it is completion-conditioned and can
understate waits in overloaded finite-horizon runs. Queue length, by contrast,
counts passengers still waiting throughout the horizon. Treat waiting-time
results for unstable conditions as finite-run diagnostics, not steady-state
means; use them alongside the stability flag and queue-length results.

CSV outputs: [summary and raw experiment files](data/README.md).

### Academic figures

Regenerate all five 300-DPI PNG figures from the experiment CSVs by running
`python plot_bus_halt_experiments.py` from this project directory.

1. [Average waiting time vs arrival rate](figures/arrival_waiting_time.png):
   compares the two models at μ = 1.0 per bay. The logarithmic y-axis makes
   both low waits and the large one-bay waits near/above capacity visible.
   Shading is the 95% confidence interval; the dashed line marks λ = μ. The
   waiting statistic excludes passengers unfinished at the horizon.
2. [Average queue length vs arrival rate](figures/arrival_queue_length.png):
   shows how the time-average queue grows with arrival rate, with 95% confidence
   intervals. The logarithmic scale exposes differences across light and heavy
   loads; queue length includes passengers still waiting.
3. [M/M/1 vs M/M/2 comparison](figures/bay_model_comparison.png): compares
   waiting time and queue length under identical inputs at λ = 0.20, 0.90, and
   1.80. Points show means, bars are 95% confidence intervals, and triangles
   denote unstable model conditions.
4. [Server utilization vs arrival rate](figures/arrival_server_utilization.png):
   plots mean overall busy-bay time as a percentage of available bay time.
   Error bars are 95% confidence intervals calculated from the replication
   standard deviations.
5. [Paired benefit with 95% confidence intervals](figures/paired_bay_benefit_confidence_intervals.png):
   shows the paired replication difference (M/M/1 minus M/M/2) for the three
   Experiment 3 arrival rates. Positive values indicate less waiting or a
   shorter queue with two bays; intervals use matched-seed replication
   differences. The symmetric-log axis shows the zero reference and wide range.

### Python and browser consistency check

The notebook and standalone browser demo are compared as independent
implementations of the same stable M/M/1 condition: λ = 0.8, μ = 1.0 per bay,
50,000 time units, an initially empty system, and no warm-up. Both use
exponential Poisson inter-arrivals and exponential service, FCFS, and the same
finite-horizon metric conventions. The average wait is computed for passengers
completed by the horizon; queue length is exactly integrated over the entire
observation horizon; throughput counts completions divided by duration; and
utilization is busy time divided by total capacity and duration.

The comparison uses 100 independent replications per implementation. Python
uses seeds 710000–710099; JavaScript uses 820000–820099. Seeds make each
implementation's runs repeatable, but the implementations do **not** use
identical random numbers or identical random-number generators.

**Predeclared tolerance:** For each metric, define the difference as Python
mean minus JavaScript mean. The tolerance is the half-width of a two-sided 95%
Welch confidence interval for that difference, computed from the observed
between-replication standard deviations and sample sizes. Declare statistical
consistency when that interval contains zero (equivalently, the absolute
difference is no greater than the tolerance). This tolerance reflects
Monte-Carlo uncertainty under independent random streams; it is not a claim of
numerical identity or proof of implementation equivalence. Results are in
[the consistency-check CSV](data/python_javascript_consistency.csv).

| Metric | Python mean (SD) | JavaScript mean (SD) | Absolute difference | Relative difference | 95% difference CI | Tolerance | Result |
|---|---:|---:|---:|---:|---:|---:|---|
| Average waiting time (time units) | 3.975083 (0.212393) | 3.984138 (0.228740) | 0.009055 | 0.2278% | [-0.070612, 0.052502] | 0.061557 | Pass |
| Time-average queue length (passengers) | 3.179815 (0.178174) | 3.190415 (0.193116) | 0.010599 | 0.3333% | [-0.062417, 0.041218] | 0.051818 | Pass |
| Throughput (passengers/time unit) | 0.799764 (0.004084) | 0.800577 (0.003910) | 0.000813 | 0.1017% | [-0.001928, 0.000302] | 0.001115 | Pass |
| Overall utilization (fraction) | 0.799068 (0.005618) | 0.800181 (0.006222) | 0.001114 | 0.1394% | [-0.002767, 0.000540] | 0.001653 | Pass |

All difference intervals include zero, so all four metrics pass the
predeclared statistical consistency criterion. These small differences are
compatible with independent random-stream variability. Source inspection
confirmed that the model event and measurement conventions match; the RNGs and
random draw ordering differ. This is a consistency check for this one stable
M/M/1 condition, not proof of exact equivalence across all conditions. Python
replications are in `data/python_consistency_replications.csv`; JavaScript
summary statistics are in `data/javascript_consistency_summary.json`. The
comparison can be recomputed with `python validate_cross_implementation.py compare`.

## Limitations and future work

- M/M/1 and M/M/2 are idealised queueing models; how well they represent a real bus halt depends on whether actual arrivals and service durations satisfy the stated assumptions.
- The model assumes exponential service times, no passenger abandonment and unlimited queue capacity.
- Finite-horizon waiting-time estimates exclude passengers unfinished by the horizon and can understate delay in overloaded runs.
- Future work may use suitable observed passenger-arrival and boarding-service data to calibrate the model, subject to data availability and permissions.

## Key references

Verified references for queueing theory, discrete-event simulation, Monte Carlo methods and verification and validation are listed below.

Full list: [REFERENCES.md](REFERENCES.md).

## AI assistance

AI assistance used during the visible report and documentation work is
recorded in [`AI_USAGE_LOG.md`](AI_USAGE_LOG.md). The log lists the tool,
prompts, tasks performed and deliverables created. The author remains
responsible for reviewing, testing and approving the submitted work.

## Licence and credits

Code: [MIT](LICENSE). Data: No data source has been selected or used yet; any future data source and its licence will be documented here.
