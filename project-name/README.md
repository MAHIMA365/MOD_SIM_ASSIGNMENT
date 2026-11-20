# Simulation of Passenger Queues at a Bus Halt: Comparing One and Two Boarding Bays.

This project will use queueing theory and discrete-event simulation to compare passenger waiting and service performance at a bus halt with one boarding bay (M/M/1) and two boarding bays (M/M/2).

**Live demo:** Pending implementation and deployment. GitHub Pages will be used if supported by the assignment requirements. · **Google Colab notebook:** Pending project setup.

**Web demo screenshot:** Pending implementation.

## The problem

Passengers arriving at a bus halt may wait in a queue before boarding. The available number of boarding bays and the rates at which passengers arrive and are served can affect waiting time and queue build-up.

This project will simulate passenger arrivals and service durations, then compare one boarding bay (M/M/1) with two boarding bays (M/M/2) under different arrival and service rates. The comparison will consider average waiting time, average queue length, throughput, and utilisation.

## Quick start

**Notebook:** The simulation notebook and Colab link are pending. Once available, open the notebook in Google Colab and select *Runtime → Run all*.

**Web demo:** Pending implementation. The planned demonstration will use HTML, CSS, and JavaScript. GitHub Pages deployment is subject to assignment requirements; a local `docs/index.html` option may be provided.

**Run locally (optional):**

```bash
pip install -r requirements.txt
jupyter notebook notebook/project-name.ipynb
```

## Using the demo

The interactive web demonstration is pending implementation. It is intended to let users explore the queue scenarios and compare the resulting performance measures. Instructions will be added to the [user guide](USER_GUIDE.md) when the demo is available.

## Model and mathematics

The project will compare an M/M/1 queue, representing one boarding bay, with an M/M/2 queue, representing two boarding bays. Passenger inter-arrival intervals and service durations will be generated randomly, and the system will be advanced using discrete-event simulation. Arrival and service rates will be varied to examine their effects on average waiting time, average queue length, throughput, and utilisation. Model assumptions, parameter definitions, and equations are pending documentation in [THEORY.md](THEORY.md).

## Verification

Verification checks and results are pending. They will be reported after the simulation has been implemented and tested.

**Verification plot:** Pending.

## Concepts applied

The project applies M/M/1 and M/M/2 queueing models to represent one and two boarding bays, respectively, and discrete-event simulation to model passenger arrivals and service. Random arrival intervals and service durations will be used to explore how changing arrival and service rates affects queue performance. The specific random variate generation and statistical analysis methods will be documented with the completed model.

## Results

Experimental results and the comparison between one and two boarding bays are pending; no results are reported at this stage.

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
