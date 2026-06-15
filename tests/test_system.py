"""Tests for raytracergui.system — OpticalSystem."""

from raytracergui.element import Element
from raytracergui.system import OpticalSystem


def _elem(d=100.0, f=50.0, name="L"):
    return Element(d=d, f=f, diameter=25.0, on=1, name=name)


def test_empty_system():
    """OpticalSystem([]) has no elements and absolute_positions is empty."""
    sys = OpticalSystem()
    assert len(sys) == 0
    assert sys.absolute_positions == []


def test_single_element_absolute_position():
    """Single element at d=150 has absolute position [150]."""
    sys = OpticalSystem([_elem(d=150.0)])
    assert sys.absolute_positions == [150.0]


def test_two_element_cumulative_positions():
    """Two elements with d=[200, 200] have absolute positions [200, 400]."""
    sys = OpticalSystem([_elem(d=200.0, name="L1"), _elem(d=200.0, name="L2")])
    assert sys.absolute_positions == [200.0, 400.0]


def test_insert_element_preserves_spacing():
    """Inserting element above index 0 with 'preserve' halves the first element's spacing.

    Original: [d=200]. Insert new element at index 0 with preserve strategy.
    Result: new element d=100, original element d=100.
    """
    sys = OpticalSystem([_elem(d=200.0, name="L1")])
    new_elem = _elem(d=0.0, f=75.0, name="NEW")
    sys.insert(0, new_elem, strategy="preserve")
    assert len(sys) == 2
    assert sys[0].d == 100.0
    assert sys[1].d == 100.0


def test_insert_element_adds_space():
    """Inserting element with 'add' strategy keeps downstream spacings unchanged."""
    sys = OpticalSystem([_elem(d=200.0, name="L1"), _elem(d=200.0, name="L2")])
    new_elem = _elem(d=50.0, f=75.0, name="NEW")
    sys.insert(1, new_elem, strategy="add")
    assert len(sys) == 3
    assert sys[1].d == 50.0
    assert sys[2].d == 200.0  # downstream unchanged


def test_insert_front_lens():
    """Inserting a front element at index 0 with 'front' strategy prepends correctly."""
    sys = OpticalSystem([_elem(d=200.0, name="L1")])
    front = _elem(d=30.0, f=40.0, name="FRONT")
    sys.insert(0, front, strategy="front")
    assert len(sys) == 2
    assert sys[0].name == "FRONT"
    assert sys[0].d == 30.0
    assert sys[1].d == 200.0  # original unchanged


def test_remove_element():
    """Removing an element by index adjusts the element list."""
    sys = OpticalSystem([_elem(name="L1"), _elem(name="L2"), _elem(name="L3")])
    removed = sys.remove(1)
    assert removed.name == "L2"
    assert len(sys) == 2
    assert sys[0].name == "L1"
    assert sys[1].name == "L3"


def test_system_length():
    """len(system) returns the number of elements."""
    sys = OpticalSystem([_elem(), _elem()])
    assert len(sys) == 2


def test_system_getitem():
    """system[0] returns the first Element."""
    e = _elem(d=100.0, name="FIRST")
    sys = OpticalSystem([e, _elem(name="SECOND")])
    assert sys[0].name == "FIRST"
