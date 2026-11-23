# Simulation of Passenger Queues at a Bus Halt: Comparing One and Two Boarding Bays.

This project will use queueing theory and discrete-event simulation to compare passenger waiting and service performance at a bus halt with one boarding bay (M/M/1) and two boarding bays (M/M/2).

**Live demo:** Pending implementation and deployment. GitHub Pages will be used if supported by the assignment requirements. · **Google Colab notebook:** Pending project setup.

**Web demo screenshot:** Pending implementation.

## The problem

Passengers arriving at a bus halt may wait in a queue before boarding. The available number of boarding bays and the rates at which passengers arrive and are served can affect waiting time and queue build-up.

This project will simulate passenger arrivals and service durations, then compare one boarding bay (M/M/1) with two boarding bays (M/M/2) under different arrival and service rates. The comparison will consider average waiting time, average queue length, throughput, and utilisation.

## Quick start

**Notebook:** The simulation notebook and Colab link are pending. Once available, open the notebook in Google Colab and select *Runtime → Run all*.

**Web demo:** Open [`docs/index.html`](docs/index.html) directly in a modern browser. It uses only local HTML, CSS, and JavaScript and needs no server or network connection. GitHub Pages deployment is subject to assignment requirements.

**Run locally (optional):**

```bash
pip install -r requirements.txt
jupyter notebook notebook/project-name.ipynb
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

The project will compare an M/M/1 queue, representing one boarding bay, with an M/M/2 queue, representing two boarding bays. Passenger inter-arrival intervals and service durations will be generated randomly, and the system will be advanced using discrete-event simulation. Arrival and service rates will be varied to examine their effects on average waiting time, average queue length, throughput, and utilisation. Model assumptions, parameter definitions, and equations are pending documentation in [THEORY.md](THEORY.md).

## Verification

Verification checks and results are pending. They will be reported after the simulation has been implemented and tested.

**Verification plot:** Pending.

## Concepts applied

The project applies M/M/1 and M/M/2 queueing models to represent one and two boarding bays, respectively, and discrete-event simulation to model passenger arrivals and service. Random arrival intervals and service durations will be used to explore how changing arrival and service rates affects queue performance. The specific random variate generation and statistical analysis methods will be documented with the completed model.

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

## Limitations and future work

- M/M/1 and M/M/2 are idealised queueing models; how well they represent a real bus halt depends on the assumptions and input rates used. These assumptions and their implications remain to be specified.
- Future work may use suitable observed, aggregate passenger-arrival and service data to inform model parameters, if such data are available and permitted.

## Key references

References are pending verification and will be added after the sources used for the model and analysis have been identified.

Full list: [REFERENCES.md](REFERENCES.md).

## AI assistance

Any AI assistance used during development will be documented in accordance with the assignment requirements. The author is responsible for reviewing and verifying submitted work.

## Licence and credits

Code: [MIT](LICENSE). Data: No data source has been selected or used yet; any future data source and its licence will be documented here.
