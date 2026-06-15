"""Tests for raytracergui.thinlens — thin-lens equation solver.

Thin-lens equation: 1/f = 1/d_i + 1/d_o
Separation constraint: L = d_i + d_o
Magnification: m = -d_i / d_o

All tolerances 1e-10 unless stated.
"""

from raytracergui.thinlens import (
    magnification,
    solve_di,
    solve_di_do_from_f_L,
    solve_do,
    solve_f,
    solve_L,
)

TOL = 1e-10


def test_solve_f_from_di_do():
    """Given d_i=200, d_o=200: f = 1/(1/200 + 1/200) = 100."""
    assert abs(solve_f(d_o=200.0, d_i=200.0) - 100.0) < TOL


def test_solve_di_from_f_do():
    """Given f=100, d_o=200: 1/d_i = 1/100 - 1/200 = 1/200, d_i=200."""
    assert abs(solve_di(f=100.0, d_o=200.0) - 200.0) < TOL


def test_solve_do_from_f_di():
    """Given f=100, d_i=200: d_o=200 (symmetric case)."""
    assert abs(solve_do(f=100.0, d_i=200.0) - 200.0) < TOL


def test_solve_L_from_f_and_di_do():
    """Given d_i=200, d_o=200: L=400."""
    assert abs(solve_L(d_o=200.0, d_i=200.0) - 400.0) < TOL


def test_solve_di_do_from_f_and_L_two_roots():
    """Given f=75, L=400: two real roots — d_i in {100, 300}, d_o in {300, 100}.

    Quadratic: d_i^2 - 400*d_i + 75*400 = 0 → d_i = (400 ± 200) / 2.
    Verify: 1/100 + 1/300 = 4/300 = 1/75. ✓
    Discriminant = 160000 - 120000 = 40000 > 0.
    """
    results = solve_di_do_from_f_L(f=75.0, L=400.0)
    assert len(results) == 2
    d_i_vals = sorted(r[0] for r in results)
    d_o_vals = sorted(r[1] for r in results)
    assert abs(d_i_vals[0] - 100.0) < TOL
    assert abs(d_i_vals[1] - 300.0) < TOL
    assert abs(d_o_vals[0] - 100.0) < TOL
    assert abs(d_o_vals[1] - 300.0) < TOL


def test_solve_di_do_from_f_and_L_double_root():
    """Given f=100, L=400: unique root d_i = d_o = 200 (L = 4f case)."""
    results = solve_di_do_from_f_L(f=100.0, L=400.0)
    assert len(results) == 1
    d_i, d_o, m = results[0]
    assert abs(d_i - 200.0) < TOL
    assert abs(d_o - 200.0) < TOL
    assert abs(m - (-1.0)) < TOL


def test_solve_di_do_from_f_and_L_no_real_solution():
    """Given f=100, L=300 (L < 4f=400): no real solution; returns empty list."""
    results = solve_di_do_from_f_L(f=100.0, L=300.0)
    assert results == []


def test_magnification_sign():
    """m = -d_i/d_o: for d_i=200, d_o=200, m=-1 (inverted image)."""
    assert abs(magnification(d_o=200.0, d_i=200.0) - (-1.0)) < TOL


def test_diverging_lens_solve_di():
    """Given f=-100, d_o=200: 1/d_i = 1/(-100) - 1/200 = -3/200, d_i = -200/3."""
    expected = -200.0 / 3.0
    assert abs(solve_di(f=-100.0, d_o=200.0) - expected) < TOL
