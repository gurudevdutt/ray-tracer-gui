"""Ray data structure for paraxial ray tracing."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class Ray:
    """A paraxial ray defined by its height and slope at the current plane.

    Parameters
    ----------
    y : float
        Transverse height above the optical axis, in millimetres.
    u : float
        Ray slope, dimensionless — ``u = tan(theta)``.  This is the propagated
        state variable; the small-angle approximation ``u ≈ theta`` is *not* used.
    color : str, optional
        Matplotlib color string (default ``'k'``).  Used for plotting only.
    linestyle : str, optional
        Matplotlib linestyle string (default ``'-'``).  Used for plotting only.
    """

    y: float
    u: float
    color: str = "k"
    linestyle: str = "-"

    @classmethod
    def from_angle(
        cls, y: float, theta_deg: float, color: str = "k", linestyle: str = "-"
    ) -> "Ray":
        """Construct a Ray from a height and an angle in degrees.

        Parameters
        ----------
        y : float
            Initial ray height, in millimetres.
        theta_deg : float
            Ray angle with respect to the optical axis, in degrees.
        color : str, optional
            Matplotlib color string.
        linestyle : str, optional
            Matplotlib linestyle string.

        Returns
        -------
        Ray
            Ray with slope ``u = tan(theta_deg * pi / 180)``.
        """
        u = math.tan(math.radians(theta_deg))
        return cls(y=y, u=u, color=color, linestyle=linestyle)
