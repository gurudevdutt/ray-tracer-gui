"""Tests for raytracergui.element — Element dataclass."""

import math
from raytracergui.element import Element


def test_element_thin_lens():
    """Element with finite f is a thin lens; effective_f == f."""
    e = Element(d=100.0, f=50.0, diameter=25.0, on=1, name="L1")
    assert e.effective_f == 50.0


def test_element_flat_plane():
    """Element with f=inf is a flat plane; effective_f == inf."""
    e = Element(d=100.0, f=float("inf"), diameter=25.0, on=1, name="P1")
    assert math.isinf(e.effective_f)


def test_element_on_off_flag():
    """Element with on=0 has effective_f == inf regardless of stored f."""
    e = Element(d=100.0, f=50.0, diameter=25.0, on=0, name="L1")
    assert math.isinf(e.effective_f)


def test_element_on_flag_restores_f():
    """Element with on=1 and finite f has effective_f == f."""
    e = Element(d=100.0, f=200.0, diameter=25.0, on=1, name="L2")
    assert e.effective_f == 200.0


def test_element_negative_focal_length():
    """Element with f < 0 is a diverging lens; effective_f == f (negative)."""
    e = Element(d=50.0, f=-75.0, diameter=25.0, on=1, name="DL")
    assert e.effective_f == -75.0


def test_element_repr_contains_name():
    """repr(Element(..., name='L1')) includes the element name."""
    e = Element(d=100.0, f=50.0, name="L1")
    assert "L1" in repr(e)


def test_element_equality():
    """Two Element instances with identical fields compare equal."""
    e1 = Element(d=100.0, f=50.0, diameter=25.0, on=1, name="L1")
    e2 = Element(d=100.0, f=50.0, diameter=25.0, on=1, name="L1")
    assert e1 == e2
