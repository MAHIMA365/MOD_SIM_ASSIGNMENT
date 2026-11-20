import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import notebook
import pandas as pd
import pytest
from scipy.stats import t


def test_numpy_exponential_random_generator():
    rng = np.random.default_rng(42)
    samples = rng.exponential(scale=0.5, size=100)

    assert samples.shape == (100,)
    assert np.all(np.isfinite(samples))
    assert np.all(samples > 0)


def test_pandas_can_store_simulation_results():
    results = pd.DataFrame(
        {
            "boarding_bays": [1, 2],
            "average_wait": [2.5, 1.2],
        }
    )

    assert results.shape == (2, 2)
    assert results["average_wait"].mean() == 1.85


def test_scipy_student_t_quantile():
    critical_value = t.ppf(0.975, df=19)

    assert 2.0 < critical_value < 2.2


def test_matplotlib_can_render_a_plot():
    figure, axes = plt.subplots()
    axes.plot([0, 1], [0, 1])
    figure.canvas.draw()

    assert len(axes.lines) == 1
    plt.close(figure)


def test_jupyter_notebook_is_importable():
    assert notebook.__version__


def test_pytest_is_installed():
    assert pytest.__version__
