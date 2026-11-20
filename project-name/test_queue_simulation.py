import numpy as np
import pytest

from queue_simulation import (
    simulate_mm1,
    simulate_mm2,
    theoretical_mm1_metrics,
    theoretical_mm2_metrics,
    measure_queue_performance,
)


def test_simulation_tracks_fcfs_passenger_times_and_states():
    result = simulate_mm1(2.0, 5.0, duration=100.0, seed=42)
    arrivals = result["arrival_times"]
    starts = result["service_start_times"]
    completions = result["service_completion_times"]
    waits = result["waiting_times"]
    statuses = result["passenger_status"]
    started = np.isfinite(starts)

    assert len(arrivals) == len(starts) == len(completions) == len(waits)
    assert np.all(starts[started] >= arrivals[started])
    assert np.all(waits[started] >= 0)
    assert np.all(np.diff(starts[started]) >= 0)
    assert np.all(np.isfinite(completions[started]))
    assert set(statuses).issubset({"waiting", "in_service", "completed"})
    assert len(result["completed_passengers"]) == np.count_nonzero(statuses == "completed")
    assert 0 <= result["server_utilization"] <= 1
    assert result["time_average_queue_length"] >= 0
    assert result["throughput"] == pytest.approx(
        len(result["completed_passengers"]) / result["duration"]
    )


def test_unfinished_passengers_remain_waiting_or_in_service_at_horizon():
    result = simulate_mm1(1000.0, 0.01, duration=1.0, seed=7)
    statuses = result["passenger_status"]
    service_passenger = result["passengers_in_service"][0]

    assert result["stable"] is False
    assert len(result["passengers_waiting"]) > 0
    assert statuses[service_passenger - 1] == "in_service"
    assert result["service_completion_times"][service_passenger - 1] > result["duration"]
    assert len(result["completed_passengers"]) == 0
    assert np.isnan(result["waiting_times"][list(result["passengers_waiting"])[0] - 1])


def test_simulation_is_reproducible_for_same_seed():
    first = simulate_mm1(0.8, 1.0, duration=100.0, seed=123)
    second = simulate_mm1(0.8, 1.0, duration=100.0, seed=123)

    np.testing.assert_array_equal(first["arrival_times"], second["arrival_times"])
    np.testing.assert_array_equal(first["service_start_times"], second["service_start_times"])
    np.testing.assert_array_equal(first["service_completion_times"], second["service_completion_times"])


def test_finite_horizon_simulation_reports_stability_without_rejecting_unstable_rates():
    result = simulate_mm1(2.0, 1.0, duration=10.0, seed=42)

    assert result["stable"] is False


@pytest.mark.parametrize(
    ("arrival_rate", "service_rate", "duration"),
    [(0, 1.0, 10.0), (-1.0, 1.0, 10.0), (1.0, 0, 10.0), (1.0, -1.0, 10.0), (1.0, 2.0, 0)],
)
def test_invalid_simulation_parameters_are_rejected(arrival_rate, service_rate, duration):
    with pytest.raises(ValueError):
        simulate_mm1(arrival_rate, service_rate, duration)


def test_theoretical_mm1_metrics_match_closed_formulas():
    metrics = theoretical_mm1_metrics(0.8, 1.0)

    assert metrics["rho"] == pytest.approx(0.8)
    assert metrics["Wq"] == pytest.approx(4.0)
    assert metrics["Lq"] == pytest.approx(3.2)
    assert metrics["W"] == pytest.approx(5.0)


@pytest.mark.parametrize(("arrival_rate", "service_rate"), [(1.0, 1.0), (2.0, 1.0)])
def test_theoretical_metrics_reject_unstable_system(arrival_rate, service_rate):
    with pytest.raises(ValueError, match="arrival_rate < service_rate"):
        theoretical_mm1_metrics(arrival_rate, service_rate)


def test_mm2_tracks_passenger_events_and_first_available_bay():
    result = simulate_mm2(2.0, 5.0, duration=100.0, seed=42)
    arrivals = result["arrival_times"]
    starts = result["service_start_times"]
    completions = result["service_completion_times"]
    waits = result["waiting_times"]
    assignments = result["server_assignments"]
    statuses = result["passenger_status"]
    started = np.isfinite(starts)

    assert len(arrivals) == len(starts) == len(completions) == len(waits)
    assert np.all(starts[started] >= arrivals[started])
    assert np.all(waits[started] >= 0)
    assert set(assignments[started]).issubset({1, 2})
    assert np.all(np.isfinite(completions[started]))
    assert set(statuses).issubset({"waiting", "in_service", "completed"})
    assert len(result["completed_passengers"]) == np.count_nonzero(statuses == "completed")
    assert len(result["per_server_utilization"]) == 2
    assert all(0 <= value <= 1 for value in result["per_server_utilization"])
    assert result["overall_utilization"] == pytest.approx(
        sum(result["per_server_utilization"]) / 2
    )
    assert result["time_average_queue_length"] >= 0
    assert result["throughput"] == pytest.approx(
        len(result["completed_passengers"]) / result["duration"]
    )


def test_mm2_uses_one_shared_fcfs_queue_for_both_bays():
    result = simulate_mm2(20.0, 0.1, duration=10.0, seed=8)
    started = np.isfinite(result["service_start_times"])
    started_indices = np.flatnonzero(started)

    assert len(result["passengers_waiting"]) > 0
    assert np.all(np.diff(result["service_start_times"][started]) >= 0)
    assert set(result["server_assignments"][started]).issubset({1, 2})
    assert len(result["passengers_in_service"]) <= 2
    assert len(started_indices) + len(result["passengers_waiting"]) == len(result["arrival_times"])


def test_mm2_keeps_unfinished_passengers_at_simulation_horizon():
    result = simulate_mm2(1000.0, 0.01, duration=1.0, seed=7)

    assert result["stable"] is False
    assert len(result["passengers_waiting"]) > 0
    assert len(result["passengers_in_service"]) == 2
    assert len(result["completed_passengers"]) == 0
    for passenger_number in result["passengers_in_service"]:
        assert result["service_completion_times"][passenger_number - 1] > result["duration"]


def test_mm2_simulation_is_reproducible_for_same_seed():
    first = simulate_mm2(0.8, 1.0, duration=100.0, seed=123)
    second = simulate_mm2(0.8, 1.0, duration=100.0, seed=123)

    np.testing.assert_array_equal(first["arrival_times"], second["arrival_times"])
    np.testing.assert_array_equal(first["service_start_times"], second["service_start_times"])
    np.testing.assert_array_equal(first["service_completion_times"], second["service_completion_times"])
    np.testing.assert_array_equal(first["server_assignments"], second["server_assignments"])


def test_mm2_finite_simulation_reports_stability_condition():
    stable = simulate_mm2(1.9, 1.0, duration=10.0, seed=42)
    unstable = simulate_mm2(2.0, 1.0, duration=10.0, seed=42)

    assert stable["stable"] is True
    assert unstable["stable"] is False


def test_theoretical_mm2_metrics_match_erlang_c_formulas():
    metrics = theoretical_mm2_metrics(0.8, 1.0)

    assert metrics["rho"] == pytest.approx(0.4)
    assert metrics["P0"] == pytest.approx(3 / 7)
    assert metrics["P_wait"] == pytest.approx(8 / 35)
    assert metrics["Wq"] == pytest.approx(4 / 21)
    assert metrics["Lq"] == pytest.approx(16 / 105)
    assert metrics["W"] == pytest.approx(25 / 21)
    assert metrics["L"] == pytest.approx(20 / 21)


@pytest.mark.parametrize(("arrival_rate", "service_rate"), [(2.0, 1.0), (3.0, 1.0)])
def test_theoretical_mm2_metrics_reject_unstable_system(arrival_rate, service_rate):
    with pytest.raises(ValueError, match=r"arrival_rate < 2 \* service_rate"):
        theoretical_mm2_metrics(arrival_rate, service_rate)


def test_performance_metrics_match_manual_mm1_timeline_with_censoring():
    metrics = measure_queue_performance(
        arrival_times=np.array([0.0, 1.0, 2.0, 7.0]),
        service_start_times=np.array([0.0, 3.0, 4.0, 7.0]),
        service_completion_times=np.array([3.0, 4.0, 7.0, 12.0]),
        server_assignments=np.array([1, 1, 1, 1]),
        duration=10.0,
        server_count=1,
    )

    assert metrics["average_waiting_time"] == pytest.approx(4 / 3)
    assert metrics["average_system_time"] == pytest.approx(11 / 3)
    assert metrics["time_average_queue_length"] == pytest.approx(0.4)
    assert metrics["throughput"] == pytest.approx(0.3)
    assert metrics["per_server_utilization"] == pytest.approx((1.0,))
    assert metrics["overall_utilization"] == pytest.approx(1.0)


def test_performance_metrics_match_manual_mm2_timeline():
    metrics = measure_queue_performance(
        arrival_times=np.array([0.0, 1.0, 2.0, 3.0]),
        service_start_times=np.array([0.0, 1.0, 4.0, 5.0]),
        service_completion_times=np.array([4.0, 5.0, 6.0, 7.0]),
        server_assignments=np.array([1, 2, 1, 2]),
        duration=10.0,
        server_count=2,
    )

    assert metrics["average_waiting_time"] == pytest.approx(1.0)
    assert metrics["average_system_time"] == pytest.approx(4.0)
    assert metrics["time_average_queue_length"] == pytest.approx(0.4)
    assert metrics["throughput"] == pytest.approx(0.4)
    assert metrics["per_server_utilization"] == pytest.approx((0.6, 0.6))
    assert metrics["overall_utilization"] == pytest.approx(0.6)


def test_performance_metrics_handle_empty_results_and_zero_duration():
    empty = np.array([], dtype=float)
    metrics = measure_queue_performance(empty, empty, empty, empty, 10.0, 2)

    assert np.isnan(metrics["average_waiting_time"])
    assert np.isnan(metrics["average_system_time"])
    assert metrics["time_average_queue_length"] == 0.0
    assert metrics["throughput"] == 0.0
    assert metrics["per_server_utilization"] == (0.0, 0.0)
    assert metrics["overall_utilization"] == 0.0

    with pytest.raises(ValueError, match="duration"):
        measure_queue_performance(empty, empty, empty, empty, 0.0, 2)