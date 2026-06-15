"""Reusable Panel widgets for the ray-tracer-gui dashboard."""

from __future__ import annotations

import math
from typing import List

import pandas as pd
import panel as pn
import param

from raytracergui.element import Element
from raytracergui.ray import Ray


class RayTableWidget(param.Parameterized):
    """Editable table of rays.

    Columns: height (mm), angle (deg), color, linestyle.
    """

    data = param.DataFrame(
        default=pd.DataFrame(columns=["height", "angle_deg", "color", "linestyle"])
    )

    def __init__(self, rays: List[Ray] = None, **params):
        super().__init__(**params)
        if rays:
            self.data = self._rays_to_df(rays)

    @staticmethod
    def _rays_to_df(rays: List[Ray]) -> pd.DataFrame:
        rows = []
        for r in rays:
            rows.append(
                {
                    "height": r.y,
                    "angle_deg": math.degrees(math.atan(r.u)),
                    "color": r.color,
                    "linestyle": r.linestyle,
                }
            )
        return pd.DataFrame(rows)

    def to_rays(self) -> List[Ray]:
        rays = []
        for _, row in self.data.iterrows():
            u = math.tan(math.radians(float(row["angle_deg"])))
            rays.append(
                Ray(
                    y=float(row["height"]),
                    u=u,
                    color=str(row["color"]),
                    linestyle=str(row["linestyle"]),
                )
            )
        return rays

    def widget(self) -> pn.widgets.Tabulator:
        editors = {
            "height": {"type": "number"},
            "angle_deg": {"type": "number"},
            "color": {"type": "input"},
            "linestyle": {"type": "input"},
        }
        return pn.widgets.Tabulator(
            self.param.data,
            editors=editors,
            show_index=False,
            sizing_mode="stretch_width",
            height=200,
        )


class LensTableWidget(param.Parameterized):
    """Editable table of optical elements.

    Columns: spacing (mm), focal_length (mm), diameter (mm), on, name.
    """

    data = param.DataFrame(
        default=pd.DataFrame(columns=["spacing", "focal_length", "diameter", "on", "name"])
    )

    def __init__(self, elements: List[Element] = None, **params):
        super().__init__(**params)
        if elements:
            self.data = self._elements_to_df(elements)

    @staticmethod
    def _elements_to_df(elements: List[Element]) -> pd.DataFrame:
        rows = []
        for e in elements:
            rows.append(
                {
                    "spacing": e.d,
                    "focal_length": e.f,
                    "diameter": e.diameter,
                    "on": e.on,
                    "name": e.name,
                }
            )
        return pd.DataFrame(rows)

    def to_elements(self) -> List[Element]:
        elements = []
        for _, row in self.data.iterrows():
            elements.append(
                Element(
                    d=float(row["spacing"]),
                    f=float(row["focal_length"]),
                    diameter=float(row["diameter"]),
                    on=int(row["on"]),
                    name=str(row["name"]),
                )
            )
        return elements

    def widget(self) -> pn.widgets.Tabulator:
        editors = {
            "spacing": {"type": "number"},
            "focal_length": {"type": "number"},
            "diameter": {"type": "number"},
            "on": {"type": "tickCross"},
            "name": {"type": "input"},
        }
        return pn.widgets.Tabulator(
            self.param.data,
            editors=editors,
            show_index=False,
            sizing_mode="stretch_width",
            height=200,
        )
