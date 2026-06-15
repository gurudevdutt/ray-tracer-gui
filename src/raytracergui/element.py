"""Optical element data structure (thin lens or plane)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Element:
    """A single optical element: a thin lens or a flat plane.

    Parameters
    ----------
    d : float
        Spacing from the *previous* element (or from the ray origin for the
        first element), in millimetres.  Absolute positions are the cumulative
        sum of spacings computed by :class:`OpticalSystem`.
    f : float
        Focal length, in millimetres.  Positive → converging, negative →
        diverging, ``float('inf')`` → flat plane (no refraction).
    diameter : float
        Lens drawing diameter, in millimetres.  Used for plotting extent only;
        rays are **not** clipped at the aperture.
    on : int
        On/off flag.  ``1`` → element active (effective focal = ``f``);
        ``0`` → element disabled (effective focal = ``inf``, drawn as a dashed
        plane).
    name : str
        Human-readable label rendered on the plot.
    """

    d: float
    f: float
    diameter: float = 25.0
    on: int = 1
    name: str = ""

    @property
    def effective_f(self) -> float:
        """Effective focal length after applying the on/off flag.

        Returns
        -------
        float
            ``f`` when ``on == 1``; ``float('inf')`` when ``on == 0``.
        """
        if self.on == 0:
            return float("inf")
        return self.f
