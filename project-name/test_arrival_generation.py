import numpy as np
import pytest

from arrival_generator import generate_arrival_times, generate_service_times


def test_positive_arrival_rate_generates_sorted_positive_times():
    times = generate_arrival_times(arrival_rate=2.0, duration=5.0, seed=7)

    assert times.ndim == 1
    assert np.all(np.isfinite(times))
    assert np.all(times >= 0)
    assert np.all(np.diff(times) > 0)
    assert np.all(times <= 5.0)


@pytest.mark.parametrize("arrival_rate", [0, -0.5, -10])
def test_zero_or_negative_arrival_rate_is_rejected(arrival_rate):
    with pytest.raises(ValueError, match="arrival_rate"):
        generate_arrival_times(arrival_rate, duration=10.0, seed=42)


@pytest.mark.parametrize("arrival_rate", [np.inf, -np.inf, np.nan])
def test_non_finite_arrival_rate_is_rejected(arrival_rate):
    with pytest.raises(ValueError, match="arrival_rate"):
        generate_arrival_times(arrival_rate, duration=10.0, seed=42)


def test_reproducible_seed_returns_identical_timestamps():
    first = generate_arrival_times(3.0, 20.0, seed=123)
    second = generate_arrival_times(3.0, 20.0, seed=123)

    np.testing.assert_array_equal(first, second)


def test_higher_arrival_rate_generates_more_passengers():
    counts = [
        len(generate_arrival_times(rate, duration=20.0, seed=seed))
        for seed in range(40)
        for rate in (2.0, 10.0)
    ]

    low_counts = counts[0::2]
    high_counts = counts[1::2]

    assert sum(high_counts) > sum(low_counts)
    assert np.mean(high_counts) > np.mean(low_counts)


def test_zero_duration_returns_no_arrivals():
    times = generate_arrival_times(5.0, duration=0.0, seed=42)

    assert times.size == 0


def test_no_timestamp_exceeds_simulation_duration():
    duration = 12.25
    times = generate_arrival_times(4.0, duration=duration, seed=99)

    assert np.all(times <= duration)


@pytest.mark.parametrize("duration", [-1.0, np.inf, -np.inf, np.nan])
def test_invalid_duration_is_rejected(duration):
    with pytest.raises(ValueError, match="duration"):
        generate_arrival_times(2.0, duration, seed=42)


@pytest.mark.parametrize("passenger_count", [1, 25, 100])
def test_positive_service_rate_generates_positive_durations(passenger_count):
    durations = generate_service_times(
        service_rate=0.5,
        passenger_count=passenger_count,
        seed=42,
    )

    assert durations.shape == (passenger_count,)
    assert np.all(np.isfinite(durations))
    assert np.all(durations > 0)


@pytest.mark.parametrize("service_rate", [0, -0.5, -10])
def test_zero_or_negative_service_rate_is_rejected(service_rate):
    with pytest.raises(ValueError, match="service_rate"):
        generate_service_times(service_rate, passenger_count=10, seed=42)


@pytest.mark.parametrize("service_rate", [np.inf, -np.inf, np.nan])
def test_non_finite_service_rate_is_rejected(service_rate):
    with pytest.raises(ValueError, match="service_rate"):
        generate_service_times(service_rate, passenger_count=10, seed=42)


def test_service_generation_is_reproducible():
    first = generate_service_times(1.5, 30, seed=123)
    second = generate_service_times(1.5, 30, seed=123)

    np.testing.assert_array_equal(first, second)


def test_different_seeds_change_service_times():
    first = generate_service_times(1.5, 30, seed=123)
    second = generate_service_times(1.5, 30, seed=124)

    assert not np.array_equal(first, second)


def test_higher_service_rate_produces_shorter_durations():
    slow = generate_service_times(0.5, 10000, seed=77)
    fast = generate_service_times(2.0, 10000, seed=77)

    assert np.mean(fast) < np.mean(slow)
    assert np.mean(fast) == pytest.approx(1 / 2.0, rel=0.05)


@pytest.mark.parametrize("passenger_count", [-1, -10])
def test_negative_passenger_count_is_rejected(passenger_count):
    with pytest.raises(ValueError, match="passenger_count"):
        generate_service_times(1.0, passenger_count, seed=42)


def test_zero_passenger_count_returns_empty_array():
    durations = generate_service_times(1.0, 0, seed=42)

    assert durations.shape == (0,)


@pytest.mark.parametrize("seed", [-1, -100])
def test_negative_seed_is_rejected(seed):
    with pytest.raises(ValueError, match="seed"):
        generate_service_times(1.0, 10, seed=seed)


@pytest.mark.parametrize(
    ("service_rate", "passenger_count"),
    [(True, 10), ("fast", 10), (1.0, 3.5), (1.0, True)],
)
def test_invalid_parameter_types_are_rejected(service_rate, passenger_count):
    with pytest.raises((TypeError, ValueError)):
        generate_service_times(service_rate, passenger_count, seed=42)
