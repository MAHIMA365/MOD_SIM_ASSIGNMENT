"""Finite-horizon discrete-event simulation for passenger queues."""

from collections import deque
from numbers import Real

import numpy as np

from arrival_generator import generate_arrival_times, generate_service_times


def _validate_rate(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real number")
    value = float(value)
    if not np.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a finite positive number")
    return value


def _random_generator(seed: int | np.random.Generator | None) -> np.random.Generator:
    if isinstance(seed, np.random.Generator):
        return seed
    if isinstance(seed, bool) or (seed is not None and not isinstance(seed, int)):
        raise TypeError("seed must be an integer, a NumPy Generator, or None")
    if seed is not None and seed < 0:
        raise ValueError("seed must be non-negative")
    return np.random.default_rng(seed)


def measure_queue_performance(
    arrival_times: np.ndarray,
    service_start_times: np.ndarray,
    service_completion_times: np.ndarray,
    server_assignments: np.ndarray,
    duration: float,
    server_count: int,
) -> dict[str, object]:
    """Measure finite-horizon queue performance from passenger event records.

    Waiting and system-time averages use only passengers completed by the
    horizon. Queue length is integrated exactly between queue-entry and
    service-start events. Busy time for an unfinished service is truncated at
    the horizon, while passengers still waiting contribute to the queue until
    that horizon.
    """
    if isinstance(duration, bool) or not isinstance(duration, Real):
        raise TypeError("duration must be a real number")
    duration = float(duration)
    if not np.isfinite(duration) or duration <= 0:
        raise ValueError("duration must be a finite positive number")
    if isinstance(server_count, bool) or not isinstance(server_count, int):
        raise TypeError("server_count must be an integer")
    if server_count <= 0:
        raise ValueError("server_count must be positive")

    arrivals = np.asarray(arrival_times, dtype=float)
    starts = np.asarray(service_start_times, dtype=float)
    completions = np.asarray(service_completion_times, dtype=float)
    assignments = np.asarray(server_assignments, dtype=float)
    arrays = (arrivals, starts, completions, assignments)
    if any(array.ndim != 1 for array in arrays):
        raise ValueError("passenger event arrays must be one-dimensional")
    if len({array.size for array in arrays}) != 1:
        raise ValueError("passenger event arrays must have matching lengths")
    if not np.all(np.isfinite(arrivals)) or np.any(arrivals < 0) or np.any(arrivals > duration):
        raise ValueError("arrival_times must be finite and within the simulation horizon")
    if np.isinf(starts).any() or np.isinf(completions).any() or not np.all(np.isfinite(assignments)):
        raise ValueError("event times must be finite or NaN, and assignments must be finite")

    started = np.isfinite(starts)
    completion_known = np.isfinite(completions)
    if np.any(starts[started] > duration):
        raise ValueError("service starts cannot occur after the simulation horizon")
    if np.any(starts[started] < arrivals[started]):
        raise ValueError("service cannot start before passenger arrival")
    if np.any(completion_known & ~started):
        raise ValueError("a service completion requires a recorded service start")
    if np.any(completions[completion_known] < starts[completion_known]):
        raise ValueError("service cannot complete before it starts")
    if np.any(assignments[started] != np.floor(assignments[started])) or np.any(
        (assignments[started] < 1) | (assignments[started] > server_count)
    ):
        raise ValueError("started passengers must have a valid one-based server assignment")

    completed = started & completion_known & (completions <= duration)
    completed_waits = starts[completed] - arrivals[completed]
    completed_system_times = completions[completed] - arrivals[completed]
    average_waiting_time = (
        float(np.mean(completed_waits)) if completed_waits.size else float("nan")
    )
    average_system_time = (
        float(np.mean(completed_system_times))
        if completed_system_times.size
        else float("nan")
    )

    queue_events: list[tuple[float, int]] = []
    for arrival, start in zip(arrivals, starts):
        if not np.isfinite(start) or start > arrival:
            queue_events.append((float(arrival), 1))
            if np.isfinite(start):
                queue_events.append((float(start), -1))

    queue_events.sort()
    queue_area = 0.0
    queue_length = 0
    previous_time = 0.0
    for event_time, change in queue_events:
        queue_area += queue_length * (event_time - previous_time)
        queue_length += change
        previous_time = event_time
    queue_area += queue_length * (duration - previous_time)

    server_busy_times = np.zeros(server_count, dtype=float)
    for start, completion, assignment in zip(starts[started], completions[started], assignments[started]):
        end_time = min(float(completion), duration) if np.isfinite(completion) else duration
        server_busy_times[int(assignment) - 1] += max(0.0, end_time - float(start))

    per_server_utilization = tuple(
        float(busy_time / duration) for busy_time in server_busy_times
    )
    overall_utilization = float(np.sum(server_busy_times) / (server_count * duration))
    return {
        "average_waiting_time": average_waiting_time,
        "time_average_queue_length": float(queue_area / duration),
        "average_system_time": average_system_time,
        "throughput": float(np.count_nonzero(completed) / duration),
        "per_server_utilization": per_server_utilization,
        "overall_utilization": overall_utilization,
    }


def simulate_mm1(
    arrival_rate: float,
    service_rate: float,
    duration: float,
    seed: int | np.random.Generator | None = 42,
) -> dict[str, object]:
    """Simulate a single-server FCFS queue until ``duration``.

    Waiting times are final only for passengers who have started service; a
    passenger still waiting at the horizon has a NaN waiting time. Completion
    timestamps are scheduled timestamps, so an in-service passenger may have
    a completion timestamp beyond the horizon while remaining uncompleted.
    """
    arrival_rate = _validate_rate(arrival_rate, "arrival_rate")
    service_rate = _validate_rate(service_rate, "service_rate")
    if isinstance(duration, bool) or not isinstance(duration, Real):
        raise TypeError("duration must be a real number")
    duration = float(duration)
    if not np.isfinite(duration) or duration <= 0:
        raise ValueError("duration must be a finite positive number")

    rng = _random_generator(seed)
    arrival_times = generate_arrival_times(arrival_rate, duration, seed=rng)
    passenger_count = len(arrival_times)
    service_start_times = np.full(passenger_count, np.nan)
    service_completion_times = np.full(passenger_count, np.nan)
    waiting_times = np.full(passenger_count, np.nan)
    statuses = np.full(passenger_count, "not_arrived", dtype="U11")

    waiting_queue: deque[int] = deque()
    completed_passengers: list[int] = []
    server_assignments = np.full(passenger_count, -1, dtype=int)
    next_arrival_index = 0
    server_passenger: int | None = None
    next_departure_time = np.inf
    current_time = 0.0
    def start_service(passenger_index: int, start_time: float) -> float:
        service_start_times[passenger_index] = start_time
        waiting_times[passenger_index] = start_time - arrival_times[passenger_index]
        server_assignments[passenger_index] = 1
        statuses[passenger_index] = "in_service"
        service_duration = generate_service_times(service_rate, 1, seed=rng)[0]
        completion_time = start_time + float(service_duration)
        service_completion_times[passenger_index] = completion_time
        return completion_time

    while True:
        next_arrival_time = (
            arrival_times[next_arrival_index]
            if next_arrival_index < passenger_count
            else np.inf
        )
        next_event_time = min(next_arrival_time, next_departure_time)

        if next_event_time > duration:
            break

        current_time = float(next_event_time)

        if next_departure_time <= next_arrival_time:
            completed_index = server_passenger
            if completed_index is None:
                raise RuntimeError("departure event occurred without a passenger in service")
            statuses[completed_index] = "completed"
            completed_passengers.append(completed_index + 1)
            server_passenger = None
            next_departure_time = np.inf

            if waiting_queue:
                server_passenger = waiting_queue.popleft()
                next_departure_time = start_service(server_passenger, current_time)
        else:
            arriving_index = next_arrival_index
            next_arrival_index += 1
            statuses[arriving_index] = "waiting"

            if server_passenger is None:
                server_passenger = arriving_index
                next_departure_time = start_service(arriving_index, current_time)
            else:
                waiting_queue.append(arriving_index)

    performance = measure_queue_performance(
        arrival_times,
        service_start_times,
        service_completion_times,
        server_assignments,
        duration,
        server_count=1,
    )
    waiting_passengers = tuple(index + 1 for index in waiting_queue)
    passengers_in_service = (
        (server_passenger + 1,) if server_passenger is not None else ()
    )

    return {
        "arrival_rate": arrival_rate,
        "service_rate": service_rate,
        "duration": duration,
        "stable": arrival_rate < service_rate,
        "arrival_times": arrival_times,
        "service_start_times": service_start_times,
        "service_completion_times": service_completion_times,
        "waiting_times": waiting_times,
        "server_assignments": server_assignments,
        "passenger_status": statuses,
        "passengers_waiting": waiting_passengers,
        "passengers_in_service": passengers_in_service,
        "completed_passengers": tuple(completed_passengers),
        **performance,
        "server_utilization": performance["overall_utilization"],
    }


def theoretical_mm1_metrics(
    arrival_rate: float,
    service_rate: float,
) -> dict[str, float]:
    """Return steady-state M/M/1 metrics; reject unstable rate pairs."""
    arrival_rate = _validate_rate(arrival_rate, "arrival_rate")
    service_rate = _validate_rate(service_rate, "service_rate")
    if arrival_rate >= service_rate:
        raise ValueError("steady-state M/M/1 metrics require arrival_rate < service_rate")

    rho = arrival_rate / service_rate
    return {
        "rho": rho,
        "Wq": arrival_rate / (service_rate * (service_rate - arrival_rate)),
        "Lq": arrival_rate**2 / (service_rate * (service_rate - arrival_rate)),
        "W": 1.0 / (service_rate - arrival_rate),
    }


def simulate_mm2(
    arrival_rate: float,
    service_rate: float,
    duration: float,
    seed: int | np.random.Generator | None = 42,
) -> dict[str, object]:
    """Simulate a two-server FCFS queue with one shared waiting line.

    Bay indices in ``server_assignments`` and ``passengers_in_service`` are
    one-based. Waiting times are NaN for passengers still in the queue at the
    horizon. A service completion scheduled beyond the horizon is retained but
    the passenger remains in service and is not counted as completed.
    """
    arrival_rate = _validate_rate(arrival_rate, "arrival_rate")
    service_rate = _validate_rate(service_rate, "service_rate")
    if isinstance(duration, bool) or not isinstance(duration, Real):
        raise TypeError("duration must be a real number")
    duration = float(duration)
    if not np.isfinite(duration) or duration <= 0:
        raise ValueError("duration must be a finite positive number")

    rng = _random_generator(seed)
    arrival_times = generate_arrival_times(arrival_rate, duration, seed=rng)
    passenger_count = len(arrival_times)
    service_start_times = np.full(passenger_count, np.nan)
    service_completion_times = np.full(passenger_count, np.nan)
    waiting_times = np.full(passenger_count, np.nan)
    server_assignments = np.full(passenger_count, -1, dtype=int)
    statuses = np.full(passenger_count, "not_arrived", dtype="U11")

    waiting_queue: deque[int] = deque()
    completed_passengers: list[int] = []
    server_passengers: list[int | None] = [None, None]
    next_departure_times = [np.inf, np.inf]
    next_arrival_index = 0
    current_time = 0.0

    def start_service(passenger_index: int, server_index: int, start_time: float) -> float:
        service_start_times[passenger_index] = start_time
        waiting_times[passenger_index] = start_time - arrival_times[passenger_index]
        server_assignments[passenger_index] = server_index + 1
        statuses[passenger_index] = "in_service"
        service_duration = generate_service_times(service_rate, 1, seed=rng)[0]
        completion_time = start_time + float(service_duration)
        service_completion_times[passenger_index] = completion_time
        return completion_time

    while True:
        next_arrival_time = (
            arrival_times[next_arrival_index]
            if next_arrival_index < passenger_count
            else np.inf
        )
        next_departure_time = min(next_departure_times)
        next_event_time = min(next_arrival_time, next_departure_time)

        if next_event_time > duration:
            break

        current_time = float(next_event_time)

        if next_departure_time <= next_arrival_time:
            server_index = next_departure_times.index(next_departure_time)
            completed_index = server_passengers[server_index]
            if completed_index is None:
                raise RuntimeError("departure event occurred without a passenger in service")

            statuses[completed_index] = "completed"
            completed_passengers.append(completed_index + 1)
            server_passengers[server_index] = None
            next_departure_times[server_index] = np.inf

            if waiting_queue:
                next_passenger = waiting_queue.popleft()
                server_passengers[server_index] = next_passenger
                next_departure_times[server_index] = start_service(
                    next_passenger,
                    server_index,
                    current_time,
                )
        else:
            arriving_index = next_arrival_index
            next_arrival_index += 1
            statuses[arriving_index] = "waiting"

            available_servers = [
                index
                for index, passenger_index in enumerate(server_passengers)
                if passenger_index is None
            ]
            if available_servers:
                server_index = int(rng.choice(available_servers))
                server_passengers[server_index] = arriving_index
                next_departure_times[server_index] = start_service(
                    arriving_index,
                    server_index,
                    current_time,
                )
            else:
                waiting_queue.append(arriving_index)

    performance = measure_queue_performance(
        arrival_times,
        service_start_times,
        service_completion_times,
        server_assignments,
        duration,
        server_count=2,
    )
    waiting_passengers = tuple(index + 1 for index in waiting_queue)
    passengers_in_service = tuple(
        index + 1 for index in server_passengers if index is not None
    )

    return {
        "arrival_rate": arrival_rate,
        "service_rate": service_rate,
        "duration": duration,
        "stable": arrival_rate < 2.0 * service_rate,
        "arrival_times": arrival_times,
        "service_start_times": service_start_times,
        "service_completion_times": service_completion_times,
        "waiting_times": waiting_times,
        "server_assignments": server_assignments,
        "passenger_status": statuses,
        "passengers_waiting": waiting_passengers,
        "passengers_in_service": passengers_in_service,
        "completed_passengers": tuple(completed_passengers),
        **performance,
    }


def theoretical_mm2_metrics(
    arrival_rate: float,
    service_rate: float,
) -> dict[str, float]:
    """Return steady-state M/M/2 metrics using the Erlang C formula."""
    arrival_rate = _validate_rate(arrival_rate, "arrival_rate")
    service_rate = _validate_rate(service_rate, "service_rate")
    if arrival_rate >= 2.0 * service_rate:
        raise ValueError("steady-state M/M/2 metrics require arrival_rate < 2 * service_rate")

    offered_load = arrival_rate / service_rate
    rho = arrival_rate / (2.0 * service_rate)
    p0 = 1.0 / (1.0 + offered_load + offered_load**2 / (2.0 * (1.0 - rho)))
    probability_wait = offered_load**2 / (2.0 * (1.0 - rho)) * p0
    waiting_time = probability_wait / (2.0 * service_rate - arrival_rate)
    queue_length = arrival_rate * waiting_time
    system_time = waiting_time + 1.0 / service_rate

    return {
        "rho": rho,
        "P0": p0,
        "P_wait": probability_wait,
        "Wq": waiting_time,
        "Lq": queue_length,
        "W": system_time,
        "L": arrival_rate * system_time,
    }