"""Load and save .jboptics configuration files.

A .jboptics file is a MATLAB v5 .mat file with a custom extension. It contains
a single struct ``data`` with four fields:

  data.lens_data   — cell array (n_elem, 6)
  data.ray_data    — cell array (n_rays, 5)
  data.current_axis — numeric (1, 4): [xmin, xmax, ymin, ymax]
  data.text_y       — numeric (1, 1): label vertical offset

See CLAUDE.md §".jboptics file format" for the full parsing gotchas.
"""

from __future__ import annotations

import math
import pathlib
from typing import Dict, List, Any

import numpy as np
import scipy.io

from raytracergui.element import Element
from raytracergui.ray import Ray


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _unwrap_numeric(cell_val: Any) -> float:
    """Extract a scalar float from a doubly-nested MATLAB cell numeric.

    MATLAB numeric cells come back as e.g. ``array([[0]], dtype=uint8)``.
    Coerce the unwrapped value to ``float`` regardless of stored dtype so that
    negative values stored as ``int16`` are preserved correctly.
    """
    arr = np.asarray(cell_val)
    val = float(arr.ravel()[0])
    return val


def _unwrap_string(cell_val: Any) -> str:
    """Extract a plain Python str from a MATLAB string cell."""
    arr = np.asarray(cell_val)
    return str(arr.ravel()[0])


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_jboptics(path: pathlib.Path) -> Dict[str, Any]:
    """Load a .jboptics file and return the parsed contents.

    Parameters
    ----------
    path : pathlib.Path
        Path to the .jboptics file.

    Returns
    -------
    dict with keys:
        ``"elements"`` : list of :class:`~raytracergui.element.Element`
        ``"rays"``     : list of :class:`~raytracergui.ray.Ray`
        ``"axis"``     : list of float — ``[xmin, xmax, ymin, ymax]``
        ``"text_y"``   : float — label vertical offset in mm
    """
    mat = scipy.io.loadmat(str(path), squeeze_me=False)
    data = mat["data"][0, 0]

    lens_data = data["lens_data"]  # shape (n_elem, 6)
    ray_data = data["ray_data"]  # shape (n_rays, 5)
    current_axis = data["current_axis"]
    text_y_raw = data["text_y"]

    # --- parse elements ---
    elements: List[Element] = []
    for i in range(lens_data.shape[0]):
        d = _unwrap_numeric(lens_data[i, 0])
        f_raw = _unwrap_numeric(lens_data[i, 1])
        diameter = _unwrap_numeric(lens_data[i, 2])
        on = int(_unwrap_numeric(lens_data[i, 3]))
        name = _unwrap_string(lens_data[i, 4])
        # delete flag in column 5 — skip deleted rows
        delete_flag = int(_unwrap_numeric(lens_data[i, 5]))
        if delete_flag:
            continue
        elements.append(Element(d=d, f=f_raw, diameter=diameter, on=on, name=name))

    # --- parse rays ---
    rays: List[Ray] = []
    for i in range(ray_data.shape[0]):
        y = _unwrap_numeric(ray_data[i, 0])
        theta_deg = _unwrap_numeric(ray_data[i, 1])
        color = _unwrap_string(ray_data[i, 2])
        linestyle = _unwrap_string(ray_data[i, 3])
        delete_flag = int(_unwrap_numeric(ray_data[i, 4]))
        if delete_flag:
            continue
        u = math.tan(math.radians(theta_deg))
        rays.append(Ray(y=y, u=u, color=color, linestyle=linestyle))

    # --- parse axis ---
    axis_arr = np.asarray(current_axis).ravel()
    axis = [float(v) for v in axis_arr[:4]]

    # --- parse text_y ---
    text_y = float(np.asarray(text_y_raw).ravel()[0])

    return {"elements": elements, "rays": rays, "axis": axis, "text_y": text_y}


def save_jboptics(
    path: pathlib.Path,
    elements: List[Element],
    rays: List[Ray],
    axis: List[float],
    text_y: float,
) -> None:
    """Save elements and rays to a .jboptics file.

    The output is a MATLAB v5 .mat file compatible with the original MATLAB GUI.

    Parameters
    ----------
    path : pathlib.Path
        Destination path.
    elements : list of Element
        Ordered elements.
    rays : list of Ray
        Rays.
    axis : list of float
        ``[xmin, xmax, ymin, ymax]`` plot bounds, in mm.
    text_y : float
        Label vertical offset, in mm.
    """
    # --- build lens_data cell array (n_elem, 6) ---
    n_elem = len(elements)
    lens_data = np.empty((n_elem, 6), dtype=object)
    for i, e in enumerate(elements):
        lens_data[i, 0] = np.array([[e.d]])
        lens_data[i, 1] = np.array([[e.f]])
        lens_data[i, 2] = np.array([[e.diameter]])
        lens_data[i, 3] = np.array([[e.on]])
        lens_data[i, 4] = np.array([e.name])
        lens_data[i, 5] = np.array([[0]])  # delete flag

    # --- build ray_data cell array (n_rays, 5) ---
    n_rays = len(rays)
    ray_data = np.empty((n_rays, 5), dtype=object)
    for i, r in enumerate(rays):
        theta_deg = math.degrees(math.atan(r.u))
        ray_data[i, 0] = np.array([[r.y]])
        ray_data[i, 1] = np.array([[theta_deg]])
        ray_data[i, 2] = np.array([r.color])
        ray_data[i, 3] = np.array([r.linestyle])
        ray_data[i, 4] = np.array([[0]])  # delete flag

    # --- build current_axis and text_y ---
    current_axis = np.array([axis], dtype=float)
    text_y_arr = np.array([[text_y]], dtype=float)

    # Wrap everything in a struct matching the MATLAB format
    data_struct = np.zeros(
        (1, 1),
        dtype=[
            ("lens_data", object),
            ("ray_data", object),
            ("current_axis", object),
            ("text_y", object),
        ],
    )
    data_struct[0, 0]["lens_data"] = lens_data
    data_struct[0, 0]["ray_data"] = ray_data
    data_struct[0, 0]["current_axis"] = current_axis
    data_struct[0, 0]["text_y"] = text_y_arr

    scipy.io.savemat(str(path), {"data": data_struct})
