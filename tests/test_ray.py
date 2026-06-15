"""Tests for raytracergui.ray — Ray dataclass."""

from raytracergui.ray import Ray


def test_ray_default_construction():
    """Ray(y=1.0, u=0.0) creates a ray with height 1.0 and zero slope."""
    r = Ray(y=1.0, u=0.0)
    assert r.y == 1.0
    assert r.u == 0.0


def test_ray_with_angle_conversion():
    """Ray.from_angle(y, theta_deg) stores u = tan(theta_deg * pi/180)."""
    r = Ray.from_angle(y=2.0, theta_deg=45.0)
    assert r.y == 2.0
    assert abs(r.u - 1.0) < 1e-10


def test_ray_zero_height_nonzero_slope():
    """Ray(y=0.0, u=0.1) is valid — on-axis ray with positive slope."""
    r = Ray(y=0.0, u=0.1)
    assert r.y == 0.0
    assert r.u == 0.1


def test_ray_negative_height_negative_slope():
    """Ray(y=-2.0, u=-0.05) stores negative height and slope correctly."""
    r = Ray(y=-2.0, u=-0.05)
    assert r.y == -2.0
    assert r.u == -0.05


def test_ray_repr_contains_y_and_u():
    """repr(Ray(y=1.0, u=0.0)) includes the numeric values of y and u."""
    r = Ray(y=1.0, u=0.0)
    s = repr(r)
    assert "1.0" in s
    assert "0.0" in s


def test_ray_equality():
    """Two Ray instances with identical (y, u) compare equal."""
    assert Ray(y=1.0, u=0.05) == Ray(y=1.0, u=0.05)
