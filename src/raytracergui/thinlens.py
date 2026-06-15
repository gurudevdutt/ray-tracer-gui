"""Thin-lens equation solver.

Solves ``1/f = 1/d_i + 1/d_o`` and ``L = d_i + d_o`` for any unknown
given two known quantities.  All pure functions; root selection is left
to the caller or GUI.
"""

from __future__ import annotations

import math
from typing import List, Tuple


def solve_f(d_o: float, d_i: float) -> float:
    """Compute focal length from object and image distances.

    ``1/f = 1/d_i + 1/d_o``

    Parameters
    ----------
    d_o : float
        Object distance, in millimetres.
    d_i : float
        Image distance, in millimetres.

    Returns
    -------
    float
        Focal length ``f``, in millimetres.
    """
    return 1.0 / (1.0 / d_i + 1.0 / d_o)


def solve_di(f: float, d_o: float) -> float:
    """Compute image distance from focal length and object distance.

    ``1/d_i = 1/f - 1/d_o``

    Parameters
    ----------
    f : float
        Focal length, in millimetres.
    d_o : float
        Object distance, in millimetres.

    Returns
    -------
    float
        Image distance ``d_i``, in millimetres.
    """
    return 1.0 / (1.0 / f - 1.0 / d_o)


def solve_do(f: float, d_i: float) -> float:
    """Compute object distance from focal length and image distance.

    ``1/d_o = 1/f - 1/d_i``

    Parameters
    ----------
    f : float
        Focal length, in millimetres.
    d_i : float
        Image distance, in millimetres.

    Returns
    -------
    float
        Object distance ``d_o``, in millimetres.
    """
    return 1.0 / (1.0 / f - 1.0 / d_i)


def solve_L(d_o: float, d_i: float) -> float:
    """Compute total track length from object and image distances.

    ``L = d_o + d_i``

    Parameters
    ----------
    d_o : float
        Object distance, in millimetres.
    d_i : float
        Image distance, in millimetres.

    Returns
    -------
    float
        Track length ``L``, in millimetres.
    """
    return d_o + d_i


def solve_di_do_from_f_L(f: float, L: float) -> List[Tuple[float, float, float]]:
    """Solve for (d_i, d_o) pairs given focal length and track length.

    From ``L = d_i + d_o`` and ``1/f = 1/d_i + 1/d_o`` we derive the
    quadratic::

        d_i^2 - L * d_i + f * L = 0

    Three cases:

    * ``L > 4f``: two distinct real roots → two ``(d_i, d_o)`` pairs.
    * ``L == 4f``: unique double root → one ``(d_i, d_o)`` pair.
    * ``L < 4f``: no real solution → empty list.

    Parameters
    ----------
    f : float
        Focal length, in millimetres.  Must be positive (converging lens).
    L : float
        Track length, in millimetres.

    Returns
    -------
    list of (d_i, d_o, magnification)
        Each entry is ``(d_i, d_o, m)`` where ``m = -d_i / d_o``.
        Zero entries if no real solution; one if ``L == 4f``; two otherwise.
    """
    discriminant = L * L - 4.0 * f * L
    if discriminant < 0.0:
        return []

    sqrt_disc = math.sqrt(discriminant)

    if math.isclose(discriminant, 0.0, abs_tol=1e-10):
        d_i = L / 2.0
        d_o = L - d_i
        m = -d_i / d_o
        return [(d_i, d_o, m)]

    d_i_1 = (L + sqrt_disc) / 2.0
    d_i_2 = (L - sqrt_disc) / 2.0
    results = []
    for d_i in (d_i_1, d_i_2):
        d_o = L - d_i
        m = -d_i / d_o
        results.append((d_i, d_o, m))
    return results


def magnification(d_o: float, d_i: float) -> float:
    """Compute lateral magnification.

    ``m = -d_i / d_o``

    Parameters
    ----------
    d_o : float
        Object distance, in millimetres.
    d_i : float
        Image distance, in millimetres.

    Returns
    -------
    float
        Lateral magnification (negative → inverted image).
    """
    return -d_i / d_o
