"""Tests for raytracergui.io — .jboptics load/save.

Uses demo_4f_reimaging.jboptics as the canonical round-trip fixture.
"""

import math
import pathlib
import tempfile

import pytest

from raytracergui.io import load_jboptics, save_jboptics


DEMO_DIR = pathlib.Path(__file__).parent.parent / "demo_optics_files"
TOL = 1e-10


def test_load_demo_4f_returns_correct_element_count(demo_jboptics_path):
    """Loading demo_4f_reimaging.jboptics yields 2 elements (lens + plane)."""
    result = load_jboptics(demo_jboptics_path)
    assert len(result["elements"]) == 2


def test_load_demo_4f_lens_focal_length(demo_jboptics_path):
    """First element has f=100 mm."""
    result = load_jboptics(demo_jboptics_path)
    assert abs(result["elements"][0].f - 100.0) < TOL


def test_load_demo_4f_plane_is_inf(demo_jboptics_path):
    """Second element has f=inf (flat plane)."""
    result = load_jboptics(demo_jboptics_path)
    assert math.isinf(result["elements"][1].f)


def test_load_demo_4f_spacings(demo_jboptics_path):
    """Both elements have spacing d=200 mm."""
    result = load_jboptics(demo_jboptics_path)
    for elem in result["elements"]:
        assert abs(elem.d - 200.0) < TOL


def test_load_demo_4f_ray_count(demo_jboptics_path):
    """Loading demo_4f_reimaging.jboptics yields 9 rays (3 heights × 3 angles)."""
    result = load_jboptics(demo_jboptics_path)
    assert len(result["rays"]) == 9


def test_load_demo_4f_ray_heights_include_negative(demo_jboptics_path):
    """Parsed rays include negative-height rays (exercises dtype coercion)."""
    result = load_jboptics(demo_jboptics_path)
    heights = [r.y for r in result["rays"]]
    assert any(h < 0 for h in heights)


def test_load_demo_4f_ray_angles_include_negative(demo_jboptics_path):
    """Parsed rays include negative-angle rays stored as slope u=tan(theta)."""
    result = load_jboptics(demo_jboptics_path)
    slopes = [r.u for r in result["rays"]]
    assert any(u < 0 for u in slopes)


def test_load_coerces_all_numerics_to_float(demo_jboptics_path):
    """All numeric fields (spacing, f, diameter, on, height, angle) are Python float."""
    result = load_jboptics(demo_jboptics_path)
    for elem in result["elements"]:
        assert isinstance(elem.d, float)
        assert isinstance(elem.f, float)
        assert isinstance(elem.diameter, float)
    for ray in result["rays"]:
        assert isinstance(ray.y, float)
        assert isinstance(ray.u, float)


def test_load_preserves_inf_focal_length(demo_jboptics_path):
    """f=inf is preserved as float('inf') — not coerced to a large finite number."""
    result = load_jboptics(demo_jboptics_path)
    inf_elements = [e for e in result["elements"] if math.isinf(e.f)]
    assert len(inf_elements) >= 1


def test_load_unwraps_string_cells(demo_jboptics_path):
    """Color and linestyle fields are plain Python str, not numpy arrays."""
    result = load_jboptics(demo_jboptics_path)
    for ray in result["rays"]:
        assert isinstance(ray.color, str)
        assert isinstance(ray.linestyle, str)


def test_round_trip_elements(demo_jboptics_path):
    """Save then reload: element spacings, focal lengths, diameters, on/off flags are unchanged."""
    original = load_jboptics(demo_jboptics_path)
    with tempfile.NamedTemporaryFile(suffix=".jboptics", delete=False) as tmp:
        tmp_path = pathlib.Path(tmp.name)
    try:
        save_jboptics(
            tmp_path,
            original["elements"],
            original["rays"],
            original["axis"],
            original["text_y"],
        )
        reloaded = load_jboptics(tmp_path)
        assert len(reloaded["elements"]) == len(original["elements"])
        for orig_e, new_e in zip(original["elements"], reloaded["elements"]):
            assert abs(orig_e.d - new_e.d) < TOL
            if math.isinf(orig_e.f):
                assert math.isinf(new_e.f)
            else:
                assert abs(orig_e.f - new_e.f) < TOL
            assert abs(orig_e.diameter - new_e.diameter) < TOL
            assert orig_e.on == new_e.on
    finally:
        tmp_path.unlink(missing_ok=True)


def test_round_trip_rays(demo_jboptics_path):
    """Save then reload: ray heights, slopes, colors, linestyles are unchanged."""
    original = load_jboptics(demo_jboptics_path)
    with tempfile.NamedTemporaryFile(suffix=".jboptics", delete=False) as tmp:
        tmp_path = pathlib.Path(tmp.name)
    try:
        save_jboptics(
            tmp_path,
            original["elements"],
            original["rays"],
            original["axis"],
            original["text_y"],
        )
        reloaded = load_jboptics(tmp_path)
        assert len(reloaded["rays"]) == len(original["rays"])
        for orig_r, new_r in zip(original["rays"], reloaded["rays"]):
            assert abs(orig_r.y - new_r.y) < TOL
            assert abs(orig_r.u - new_r.u) < 1e-6  # atan(tan(x)) round-trip
            assert orig_r.color == new_r.color
            assert orig_r.linestyle == new_r.linestyle
    finally:
        tmp_path.unlink(missing_ok=True)


def test_round_trip_axis(demo_jboptics_path):
    """Save then reload: current_axis [xmin, xmax, ymin, ymax] is unchanged."""
    original = load_jboptics(demo_jboptics_path)
    with tempfile.NamedTemporaryFile(suffix=".jboptics", delete=False) as tmp:
        tmp_path = pathlib.Path(tmp.name)
    try:
        save_jboptics(
            tmp_path,
            original["elements"],
            original["rays"],
            original["axis"],
            original["text_y"],
        )
        reloaded = load_jboptics(tmp_path)
        for a, b in zip(original["axis"], reloaded["axis"]):
            assert abs(a - b) < TOL
    finally:
        tmp_path.unlink(missing_ok=True)


def test_round_trip_text_y(demo_jboptics_path):
    """Save then reload: text_y is unchanged."""
    original = load_jboptics(demo_jboptics_path)
    with tempfile.NamedTemporaryFile(suffix=".jboptics", delete=False) as tmp:
        tmp_path = pathlib.Path(tmp.name)
    try:
        save_jboptics(
            tmp_path,
            original["elements"],
            original["rays"],
            original["axis"],
            original["text_y"],
        )
        reloaded = load_jboptics(tmp_path)
        assert abs(original["text_y"] - reloaded["text_y"]) < TOL
    finally:
        tmp_path.unlink(missing_ok=True)


@pytest.mark.parametrize("jboptics_file", list(DEMO_DIR.glob("*.jboptics")))
def test_all_demo_files_load_without_error(jboptics_file):
    """Every .jboptics file in demo_optics_files/ loads without raising an exception."""
    result = load_jboptics(jboptics_file)
    assert "elements" in result
    assert "rays" in result
    assert "axis" in result
    assert "text_y" in result
