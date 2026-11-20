"""Passenger arrival generation for the bus-halt queue simulation."""

from numbers import Real

import numpy as np


def generate_arrival_times(
    arrival_rate: float,
    duration: float,
    seed: int | np.random.Generator | None = 42,
) -> np.ndarray:
    """Generate passenger arrival timestamps for a homogeneous Poisson process.

    Parameters
    ----------
    arrival_rate:
        Positive passenger arrival rate, in passengers per simulation time unit.
    duration:
        Non-negative observation horizon. An arrival exactly at ``duration``
        is included.
    seed:
        A non-negative integer, an existing NumPy Generator, or ``None``.
        Integers make the generated timestamps reproducible.

    Returns
    -------
    numpy.ndarray
        Strictly increasing arrival timestamps in ``[0, duration]``.

    Raises
    ------
    TypeError
        If a numeric parameter is not a real number or ``seed`` has an invalid
        type.
    ValueError
        If ``arrival_rate`` is not positive, ``duration`` is negative, or
        ``seed`` is negative.
    """
    if isinstance(arrival_rate, bool) or not isinstance(arrival_rate, Real):
        raise TypeError("arrival_rate must be a real number")
    if isinstance(duration, bool) or not isinstance(duration, Real):
        raise TypeError("duration must be a real number")

    arrival_rate = float(arrival_rate)
    duration = float(duration)

    if not np.isfinite(arrival_rate) or arrival_rate <= 0:
        raise ValueError("arrival_rate must be a finite positive number")
    if not np.isfinite(duration) or duration < 0:
        raise ValueError("duration must be a finite non-negative number")

    if isinstance(seed, np.random.Generator):
        rng = seed
    elif isinstance(seed, bool) or (seed is not None and not isinstance(seed, int)):
        raise TypeError("seed must be an integer, a NumPy Generator, or None")
    elif seed is not None and seed < 0:
        raise ValueError("seed must be non-negative")
    else:
        rng = np.random.default_rng(seed)

    if duration == 0:
        return np.empty(0, dtype=float)

    arrival_times: list[float] = []
    elapsed_time = 0.0

    while True:
        # Generate inter-arrivals by inverse transform sampling:
        # A = -ln(U) / lambda, where U is Uniform(0, 1).
        uniforms = rng.random(1024)
        uniforms = np.maximum(uniforms, np.finfo(float).eps)
        inter_arrivals = -np.log(uniforms) / arrival_rate
        cumulative_times = elapsed_time + np.cumsum(inter_arrivals)

        within_horizon = cumulative_times[cumulative_times <= duration]
        if within_horizon.size:
            arrival_times.extend(within_horizon.tolist())

        if cumulative_times[-1] > duration:
            break

        elapsed_time = float(cumulative_times[-1])

    timestamps = np.asarray(arrival_times, dtype=float)

    # Floating-point subtraction can theoretically collapse two very close gaps.
    # The queue model normally starts after time zero and requires finite values.
    timestamps = timestamps[np.isfinite(timestamps)]
    return timestamps


def generate_service_times(
    service_rate: float,
    passenger_count: int,
    seed: int | np.random.Generator | None = 42,
) -> np.ndarray:
    """Generate exponential boarding-service durations.

    Parameters
    ----------
    service_rate:
        Positive service rate for one boarding bay, in passengers per
        simulation time unit.
    passenger_count:
        Non-negative number of passenger service durations to generate.
    seed:
        A non-negative integer, an existing NumPy Generator, or ``None``.

    Returns
    -------
    numpy.ndarray
        One positive service duration per passenger.

    Raises
    ------
    TypeError
        If a parameter has an invalid type.
    ValueError
        If a numeric parameter is invalid or seed is negative.
    """
    if isinstance(service_rate, bool) or not isinstance(service_rate, Real):
        raise TypeError("service_rate must be a real number")
    if isinstance(passenger_count, bool) or not isinstance(passenger_count, int):
        raise TypeError("passenger_count must be an integer")

    service_rate = float(service_rate)

    if not np.isfinite(service_rate) or service_rate <= 0:
        raise ValueError("service_rate must be a finite positive number")
    if passenger_count < 0:
        raise ValueError("passenger_count must be non-negative")

    if isinstance(seed, np.random.Generator):
        rng = seed
    elif isinstance(seed, bool) or (seed is not None and not isinstance(seed, int)):
        raise TypeError("seed must be an integer, a NumPy Generator, or None")
    elif seed is not None and seed < 0:
        raise ValueError("seed must be non-negative")
    else:
        rng = np.random.default_rng(seed)

    if passenger_count == 0:
        return np.empty(0, dtype=float)

    uniforms = rng.random(passenger_count)
    uniforms = np.maximum(uniforms, np.finfo(float).eps)
    return -np.log(uniforms) / service_rate
