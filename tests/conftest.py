"""Shared pytest fixtures for ray-tracer-gui tests."""

import pytest


@pytest.fixture
def single_lens_system():
    """Return a simple one-lens OpticalSystem: f=100 mm, spacing 200 mm."""
    from raytracergui.element import Element
    from raytracergui.system import OpticalSystem

    elem = Element(d=200.0, f=100.0, diameter=25.0, on=1, name="L1")
    return OpticalSystem(elements=[elem])


@pytest.fixture
def four_f_system():
    """Return the 4f relay: lens f=100 at x=200, flat plane at x=400.

    Matches demo_4f_reimaging.jboptics: lens spacing 200, plane spacing 200.
    """
    from raytracergui.element import Element
    from raytracergui.system import OpticalSystem

    lens = Element(d=200.0, f=100.0, diameter=25.0, on=1, name="L1")
    plane = Element(d=200.0, f=float("inf"), diameter=25.0, on=1, name="plane")
    return OpticalSystem(elements=[lens, plane])


@pytest.fixture
def demo_jboptics_path():
    """Return the path to the canonical demo .jboptics file."""
    import pathlib

    return pathlib.Path(__file__).parent.parent / "demo_optics_files" / "demo_4f_reimaging.jboptics"
