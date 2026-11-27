# User Guide: Bus Halt Queue Simulation

## Open the demo

Open [`docs/index.html`](../docs/index.html) in a modern browser such as Chrome,
Edge or Firefox. The demo runs entirely in the browser and does not require
Python, a server or an internet connection.

For the GitHub Pages version, enable Pages for the repository and publish the
repository-root `docs/` folder.

## Controls

| Control | What it does | Allowed range | Default |
|---|---|---|---|
| Boarding bays | Chooses M/M/1 (one bay) or M/M/2 (two bays with a shared queue) | 1 or 2 | 2 |
| Passenger arrival rate λ | Sets the average number of passengers arriving per simulation time unit | 0.05–3.00 | 0.90 |
| Service rate per bay μ | Sets the average number of passengers each bay can serve per time unit | 0.05–3.00 | 1.00 |
| Simulation duration | Sets the observation horizon; the simulation starts empty | 50–5,000 time units | 500 |
| Random seed | Makes the random run reproducible | 0–2,147,483,647 | 42 |
| Animation pace | Changes how many events are processed per animation frame; it does not change the model | 1–80 events/frame | 12 |
| Start simulation | Starts or restarts the displayed stochastic run | — | — |
| Pause / Resume | Temporarily pauses or continues the current run | — | — |
| Reset | Clears the current run and applies the values in the controls | — | — |

## Stability

The model is stable only when:

- One bay: `λ < μ`
- Two bays: `λ < 2μ`

The demo marks an unstable run in the status area. At or above the capacity
limit, the queue can grow continuously during the observation horizon.

## Reading the visualisation

- **Waiting passenger:** An orange circle in the queue.
- **Passenger in service:** A blue circle at a boarding bay.
- **Boarding bay:** An outlined bay area on the platform.
- **Clock:** Shows the current simulation time and observation horizon.
- **Run status:** Shows whether the run is Ready, Running, Paused or Unstable.

The animation is a visual representation of the selected stochastic run. It is
not a separate or hard-coded example.

## Reading the outputs

| Output | Meaning |
|---|---|
| Average waiting time | Mean queue delay for passengers that complete service before the horizon ends |
| Average queue length | Time-average number of passengers waiting; it is integrated over the whole run |
| Throughput | Number of passengers completed divided by the simulation duration |
| Server utilisation | Busy bay time divided by the total capacity of all selected bays |

For unstable runs, waiting-time output should be interpreted carefully.
Passengers still waiting or in service when the horizon ends are excluded from
the completed-passenger waiting-time average. Queue length and the stability
status provide stronger evidence of overload.

## Try these examples

### 1. Compare one bay and two bays

1. Choose **1 bay**.
2. Set λ = 0.90, μ = 1.00 and duration = 500.
3. Select **Start simulation**.
4. Record or estimate the final waiting time and queue length.
5. Reset.
6. Choose **2 bays** and keep the same λ, μ and duration.
7. Start the run and compare the outputs.

The two-bay run should usually have a much shorter wait and queue.

### 2. Observe overload

1. Choose **1 bay**.
2. Set λ = 1.20 and μ = 1.00.
3. Start the run.
4. Because λ is greater than μ, the queue should grow and the run should be
   identified as unstable.

### 3. Replay the same result

Use the same values and random seed in separate runs. Equal settings and seeds
produce reproducible event sequences. Change only the bay count to make a
matched comparison.

## Check against the analytical model

For stable settings, the browser result can be compared with the steady-state
model described in [`THEORY.md`](THEORY.md). Finite simulation runs are
stochastic, so an individual run will not be exactly equal to the analytical
value. Longer durations and repeated runs should produce estimates closer to
the theoretical result.

For example, with λ = 0.8 and μ = 1.0:

- M/M/1 theoretical queue waiting time is `Wq = 4.0`
- M/M/1 theoretical mean queue length is `Lq = 3.2`

These theoretical values assume a steady state and an infinitely long
observation horizon. The browser reports a finite-horizon stochastic result.

## Limitations

- This is an idealised M/M/1 or M/M/2 queueing model, not a measured real-world
  bus-halt dataset.
- Passenger arrivals are assumed to follow a Poisson process.
- Service durations are assumed to be exponential.
- Passengers follow first-come, first-served discipline.
- There is unlimited queue capacity and no passenger abandonment.
- A second bay is assumed to have the same service rate as the first bay.
- Very short durations may give noisy results that are not close to steady state.
- Waiting-time averages exclude passengers not completed by the horizon.
- The demo measures one stochastic run; it does not report confidence intervals.

For replicated means and confidence intervals, use the Python experiments and
the CSV summaries in [`data/`](data/). The corresponding theory and equations
are documented in [`THEORY.md`](THEORY.md).
