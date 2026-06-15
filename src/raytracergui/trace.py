"""Paraxial ray propagation engine."""

from __future__ import annotations

import math
from typing import List, Tuple

from raytracergui.element import Element
from raytracergui.ray import Ray
from raytracergui.system import OpticalSystem


def propagate_ray(ray: Ray, elements: List[Element]) -> List[Tuple[float, float]]:
    """Propagate a single ray through an ordered list of elements.

    Implements the MATLAB propagate-then-refract recurrence exactly::

        y_{j+1} = y_j + u_j * d_j          # free-space propagation
        u_{j+1} = u_j - y_{j+1} / f_j      # thin-lens refraction kick

    A flat plane (``f = inf``) leaves the slope unchanged because the
    refraction term ``y / inf = 0``.

    Parameters
    ----------
    ray : Ray
        Initial ray (height in mm, slope ``u = tan(theta)``).
    elements : list of Element
        Ordered elements.  Each element's ``effective_f`` is used (respects
        the on/off flag).

    Returns
    -------
    list of (float, float)
        ``(y, u)`` state at the initial position (index 0) plus the position
        immediately *after* each element (index 1 … N).  Length is
        ``len(elements) + 1``.
    """
    y = float(ray.y)
    u = float(ray.u)
    history: List[Tuple[float, float]] = [(y, u)]

    for elem in elements:
        # free-space propagation to element plane
        y = y + u * float(elem.d)
        # thin-lens refraction kick (vanishes for f = inf)
        f = elem.effective_f
        if not math.isinf(f):
            u = u - y / f
        history.append((y, u))

    return history


def trace(rays: List[Ray], system: OpticalSystem) -> List[List[Tuple[float, float]]]:
    """Trace multiple rays through an optical system.

    Parameters
    ----------
    rays : list of Ray
        Rays to trace.
    system : OpticalSystem
        Optical system containing an ordered list of elements.

    Returns
    -------
    list of list of (float, float)
        One history list per ray.  Each history is a list of ``(y, u)`` tuples
        at the initial position and after each element.  See
        :func:`propagate_ray` for the indexing convention.
    """
    elements = list(system)
    return [propagate_ray(ray, elements) for ray in rays]
