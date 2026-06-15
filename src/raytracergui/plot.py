"""matplotlib drawing helpers for the ray-tracing GUI.

All functions are UI-agnostic — they draw onto a caller-supplied
``matplotlib.axes.Axes`` and return nothing.  No Panel/param imports.
"""

from __future__ import annotations

import math
from typing import List, Optional

import matplotlib.pyplot as plt
import matplotlib.axes as _mpl_axes

from raytracergui.ray import Ray
from raytracergui.system import OpticalSystem
from raytracergui.trace import trace


def plot_rays(
    ax: _mpl_axes.Axes,
    rays: List[Ray],
    system: OpticalSystem,
) -> None:
    """Draw ray paths through *system* on *ax*.

    Traces each ray through the system and plots the piecewise-linear
    ``y`` vs ``x`` path.  The x-values are the ray origin (``x=0``) and
    the absolute positions of each element.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axes.
    rays : list of Ray
        Rays to trace and draw.
    system : OpticalSystem
        Optical system defining the element positions.
    """
    if not rays:
        return

    x_positions = [0.0] + system.absolute_positions
    histories = trace(rays, system)

    for ray, history in zip(rays, histories):
        y_vals = [state[0] for state in history]
        ax.plot(x_positions, y_vals, color=ray.color, linestyle=ray.linestyle)


def plot_lenses(
    ax: _mpl_axes.Axes,
    system: OpticalSystem,
    text_y: float = 5.0,
) -> None:
    """Draw each element as a vertical line on *ax*.

    Thin lenses are drawn as solid vertical lines; flat planes (``f = inf``
    or ``on = 0``) are drawn as dashed lines.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axes.
    system : OpticalSystem
        Optical system whose elements are drawn.
    text_y : float, optional
        Vertical offset (mm) above the element for the name label.
        Defaults to 5.0 mm.
    """
    abs_positions = system.absolute_positions
    for elem, x_pos in zip(system, abs_positions):
        half_d = elem.diameter / 2.0
        is_plane = math.isinf(elem.effective_f)
        ls = "--" if is_plane else "-"
        ax.plot([x_pos, x_pos], [-half_d, half_d], color="k", linestyle=ls)
        if elem.name:
            ax.text(x_pos, half_d + text_y, elem.name, ha="center", va="bottom", fontsize=8)


def plot_single_lens(
    ax: _mpl_axes.Axes,
    x_pos: float,
    diameter: float,
    is_plane: bool = False,
    name: str = "",
    text_y: float = 5.0,
) -> None:
    """Draw a single element at a given x position.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axes.
    x_pos : float
        Absolute x position, in mm.
    diameter : float
        Full diameter, in mm.
    is_plane : bool, optional
        If True, draw as a dashed line.
    name : str, optional
        Label text.
    text_y : float, optional
        Vertical offset above the element for the label, in mm.
    """
    half_d = diameter / 2.0
    ls = "--" if is_plane else "-"
    ax.plot([x_pos, x_pos], [-half_d, half_d], color="k", linestyle=ls)
    if name:
        ax.text(x_pos, half_d + text_y, name, ha="center", va="bottom", fontsize=8)


def setup_axes(
    ax: _mpl_axes.Axes,
    axis_limits: Optional[List[float]] = None,
) -> None:
    """Apply standard axis labels and optional limits.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axes.
    axis_limits : list of float, optional
        ``[xmin, xmax, ymin, ymax]`` in mm.  If None, autoscale is used.
    """
    ax.set_xlabel("optical axis (mm)")
    ax.set_ylabel("height (mm)")
    ax.axhline(0, color="k", linewidth=0.5, linestyle=":")
    if axis_limits is not None and len(axis_limits) == 4:
        ax.set_xlim(axis_limits[0], axis_limits[1])
        ax.set_ylim(axis_limits[2], axis_limits[3])


def draw_system(
    rays: List[Ray],
    system: OpticalSystem,
    axis_limits: Optional[List[float]] = None,
    text_y: float = 5.0,
    ax: Optional[_mpl_axes.Axes] = None,
) -> _mpl_axes.Axes:
    """Draw a complete optical system: rays + lenses on a single axes.

    Convenience wrapper that calls :func:`plot_rays`, :func:`plot_lenses`,
    and :func:`setup_axes`.

    Parameters
    ----------
    rays : list of Ray
        Rays to trace.
    system : OpticalSystem
        Optical system.
    axis_limits : list of float, optional
        ``[xmin, xmax, ymin, ymax]``.
    text_y : float, optional
        Label vertical offset, in mm.
    ax : matplotlib.axes.Axes, optional
        Axes to draw on.  If None, a new figure is created.

    Returns
    -------
    matplotlib.axes.Axes
        The axes that was drawn on.
    """
    if ax is None:
        _, ax = plt.subplots()
    plot_rays(ax, rays, system)
    plot_lenses(ax, system, text_y=text_y)
    setup_axes(ax, axis_limits)
    return ax
