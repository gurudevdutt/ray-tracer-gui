"""Tests for raytracergui.trace — paraxial propagation engine.

All numerical tolerances are 1e-10 unless stated otherwise.
MATLAB reference values are marked with # MATLAB reference value.
"""

from raytracergui.element import Element
from raytracergui.ray import Ray
from raytracergui.system import OpticalSystem
from raytracergui.trace import propagate_ray, trace


TOL = 1e-10


def test_flat_plane_leaves_ray_unchanged():
    """A flat plane (f=inf) propagates y by d but does not change slope u.

    Ray(y=1.0, u=0.1), Element(d=100, f=inf):
      y_out = 1.0 + 0.1*100 = 11.0
      u_out = 0.1 - 11.0/inf = 0.1
    Tolerance: 1e-10.
    """
    ray = Ray(y=1.0, u=0.1)
    elem = Element(d=100.0, f=float("inf"))
    history = propagate_ray(ray, [elem])
    y_out, u_out = history[-1]
    assert abs(y_out - 11.0) < TOL
    assert abs(u_out - 0.1) < TOL


def test_thin_lens_on_axis_source_images_at_correct_distance():
    """Single thin lens (f=100) images an on-axis point source placed at d_o=200.

    Per 1/f = 1/d_i + 1/d_o → d_i = 200. A marginal ray starting at y=0, u=0.05
    propagated through d=200 to the lens, then refracted by f=100, should
    reach y=0 after exactly another 200 mm propagation (verified analytically).
    Tolerance: 1e-10.
    """
    ray = Ray(y=0.0, u=0.05)
    # lens at d=200 from origin
    lens = Element(d=200.0, f=100.0)
    # image plane at d=200 past the lens
    image_plane = Element(d=200.0, f=float("inf"))
    history = propagate_ray(ray, [lens, image_plane])
    y_image, _ = history[-1]
    assert abs(y_image) < TOL


def test_diverging_lens_bends_ray_away():
    """A diverging lens (f=-50) bends rays away from the axis.

    Ray(y=1.0, u=0.0), Element(d=0, f=-50):
      y_after_prop = 1.0 + 0.0*0 = 1.0
      u_out = 0.0 - 1.0/(-50) = 0.02 (positive: bending away from axis)
    Tolerance: 1e-10.
    """
    ray = Ray(y=1.0, u=0.0)
    elem = Element(d=0.0, f=-50.0)
    history = propagate_ray(ray, [elem])
    _, u_out = history[-1]
    assert abs(u_out - 0.02) < TOL


def test_multi_element_recurrence_matches_matlab():
    """Two-element system matches the MATLAB propagate-then-refract recurrence.

    System: lens f=100 at d=200, flat plane at d=200.
    Ray: y=0, u=0.05.
    Step 1 (propagate to lens):  y1 = 0 + 0.05*200 = 10.0   # MATLAB reference value
    Step 1 (refract at lens):    u1 = 0.05 - 10.0/100 = -0.05  # MATLAB reference value
    Step 2 (propagate to plane): y2 = 10 + (-0.05)*200 = 0.0   # MATLAB reference value
    Step 2 (refract at plane):   u2 = -0.05 - 0.0/inf = -0.05  # MATLAB reference value
    Tolerance: 1e-10.
    """
    ray = Ray(y=0.0, u=0.05)
    lens = Element(d=200.0, f=100.0)
    plane = Element(d=200.0, f=float("inf"))
    history = propagate_ray(ray, [lens, plane])
    # history[0] = initial, history[1] = after lens, history[2] = after plane
    y1, u1 = history[1]
    y2, u2 = history[2]
    assert abs(y1 - 10.0) < TOL
    assert abs(u1 - (-0.05)) < TOL
    assert abs(y2 - 0.0) < TOL
    assert abs(u2 - (-0.05)) < TOL


def test_negative_height_negative_angle():
    """Negative initial height and angle propagate correctly.

    Ray(y=-2.0, u=-0.03), Element(d=100, f=200):
      y_out = -2.0 + (-0.03)*100 = -5.0
      u_out = -0.03 - (-5.0)/200 = -0.005
    Tolerance: 1e-10.
    """
    ray = Ray(y=-2.0, u=-0.03)
    elem = Element(d=100.0, f=200.0)
    history = propagate_ray(ray, [elem])
    y_out, u_out = history[-1]
    assert abs(y_out - (-5.0)) < TOL
    assert abs(u_out - (-0.005)) < TOL


def test_empty_system_returns_ray_unchanged():
    """Tracing through an empty system returns the original (y, u) unchanged."""
    ray = Ray(y=3.0, u=0.07)
    history = propagate_ray(ray, [])
    assert len(history) == 1
    y, u = history[0]
    assert abs(y - 3.0) < TOL
    assert abs(u - 0.07) < TOL


def test_no_rays_returns_empty():
    """Tracing zero rays returns an empty list."""
    sys = OpticalSystem([Element(d=100.0, f=50.0)])
    result = trace([], sys)
    assert result == []


def test_multiple_rays_vectorized():
    """Tracing three rays through a single lens returns three independent histories."""
    rays = [Ray(y=0.0, u=0.05), Ray(y=1.0, u=0.0), Ray(y=-1.0, u=0.0)]
    sys = OpticalSystem([Element(d=100.0, f=50.0)])
    result = trace(rays, sys)
    assert len(result) == 3
    # each history has 2 entries: initial + after element
    for hist in result:
        assert len(hist) == 2


def test_off_element_treated_as_flat_plane():
    """An on=0 element (effective f=inf) acts like a flat plane — slope is unchanged."""
    ray = Ray(y=1.0, u=0.05)
    # f=50 but on=0 → effective_f=inf
    elem = Element(d=100.0, f=50.0, on=0)
    history = propagate_ray(ray, [elem])
    y_out, u_out = history[-1]
    # propagation: y = 1 + 0.05*100 = 6.0; no refraction
    assert abs(y_out - 6.0) < TOL
    assert abs(u_out - 0.05) < TOL


def test_trace_returns_full_history():
    """trace() returns the (y, u) state at every element plane, not just the final value."""
    ray = Ray(y=0.0, u=0.05)
    sys = OpticalSystem(
        [
            Element(d=100.0, f=50.0, name="L1"),
            Element(d=100.0, f=float("inf"), name="P1"),
            Element(d=100.0, f=75.0, name="L2"),
        ]
    )
    result = trace([ray], sys)
    # 1 ray, history length = n_elements + 1 = 4
    assert len(result) == 1
    assert len(result[0]) == 4
