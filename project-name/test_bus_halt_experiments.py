import numpy as np

from run_bus_halt_experiments import (
    confidence_interval,
    seed_for,
    validate_conservation,
)
from queue_simulation import simulate_mm1


def test_experiment_seed_is_reproducible_and_parameter_distinct():
    first = seed_for(1, 2, 3)
    second = seed_for(1, 2, 3)
    distinct = seed_for(1, 3, 3)

    assert first == second
    assert distinct != first


def test_confidence_interval_returns_finite_bounds():
    mean, standard_deviation, low, high = confidence_interval(
        [1.0, 1.2, 0.9, 1.1, 1.0]
    )

    assert mean == np.mean([1.0, 1.2, 0.9, 1.1, 1.0])
    assert standard_deviation > 0
    assert low < mean < high


def test_passenger_conservation_accepts_a_valid_run():
    result = simulate_mm1(0.5, 1.0, duration=100.0, seed=123)
    validate_conservation(result)
