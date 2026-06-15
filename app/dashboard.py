"""Main entry point for the ray-tracer-gui Panel application.

Launch with:
    .venv/bin/panel serve app/dashboard.py --show --port 5007
"""

from __future__ import annotations

import pathlib
import sys
import tempfile

import matplotlib

matplotlib.use("agg")
import matplotlib.pyplot as plt
import panel as pn
import param

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from widgets import LensTableWidget, RayTableWidget

from raytracergui.io import load_jboptics, save_jboptics
from raytracergui.plot import draw_system
from raytracergui.system import OpticalSystem
from raytracergui.thinlens import solve_di_do_from_f_L

pn.extension("tabulator")

DEMO_DIR = pathlib.Path(__file__).parent.parent / "demo_optics_files"
DEFAULT_STARTUP = DEMO_DIR / "default_startup.jboptics"

HELP_TEXT = """
### How to use

**Rays table** — each row is one ray entering the system from `x = 0`.
- *height*: transverse position in mm
- *angle_deg*: angle in degrees (slope u = tan θ internally)
- *color* / *linestyle*: matplotlib codes (`k`, `r`, `b` / `-`, `--`, `-.`)

**Lenses table** — elements in the order light hits them.
- *spacing*: distance from the previous element (or from x = 0 for the first)
- *focal_length*: `f` in mm — positive = converging, negative = diverging, `inf` = flat plane
- *diameter*: drawing height only — rays are **not** clipped
- *on*: 1 = active, 0 = disabled (drawn as dashed plane)

**Workflow**
1. Pick a demo from the dropdown → click **Load demo**
2. Edit the tables directly → click **Update plot**
3. Adjust axis limits — plot auto-updates when *Auto update* is checked
4. Use the **Thin-lens calculator** to solve for d_i / d_o given f and L
5. Enter a filename and click **Save** to write a `.jboptics` file
""".strip()


class RayTracerDashboard(param.Parameterized):
    """Interactive paraxial ray-tracer dashboard."""

    x_min = param.Number(default=-100.0, label="X min (mm)")
    x_max = param.Number(default=800.0, label="X max (mm)")
    y_min = param.Number(default=-10.0, label="Y min (mm)")
    y_max = param.Number(default=10.0, label="Y max (mm)")
    text_y = param.Number(default=4.0, label="Label offset (mm)")
    auto_update = param.Boolean(default=True, label="Auto update")

    def __init__(self, **params):
        super().__init__(**params)
        self._ray_widget = RayTableWidget()
        self._lens_widget = LensTableWidget()
        # Single stable plot pane — we update .object in place, never replace the pane
        self._plot_pane = pn.pane.Matplotlib(self._make_figure(), sizing_mode="stretch_width", tight=True)
        self._load_file(DEFAULT_STARTUP)
        # Watch axis params; fire _refresh when any change
        self.param.watch(
            self._on_axis_change,
            ["x_min", "x_max", "y_min", "y_max", "text_y"],
        )

    # ------------------------------------------------------------------
    # I/O
    # ------------------------------------------------------------------

    def _load_file(self, path: pathlib.Path) -> None:
        if not path.exists():
            return
        result = load_jboptics(path)
        self._ray_widget.data = RayTableWidget._rays_to_df(result["rays"])
        self._lens_widget.data = LensTableWidget._elements_to_df(result["elements"])
        axis = result["axis"]
        if len(axis) == 4:
            # Use param.update to batch so watch fires once
            self.param.update(
                x_min=axis[0], x_max=axis[1],
                y_min=axis[2], y_max=axis[3],
                text_y=result["text_y"],
            )
        else:
            self.text_y = result["text_y"]
        self.refresh()  # always redraw after loading

    def _save_file(self, path: pathlib.Path) -> None:
        save_jboptics(
            path,
            elements=self._lens_widget.to_elements(),
            rays=self._ray_widget.to_rays(),
            axis=[self.x_min, self.x_max, self.y_min, self.y_max],
            text_y=self.text_y,
        )

    # ------------------------------------------------------------------
    # Plot
    # ------------------------------------------------------------------

    def _make_figure(self):
        rays = self._ray_widget.to_rays()
        elements = self._lens_widget.to_elements()
        system = OpticalSystem(elements)
        axis_limits = [self.x_min, self.x_max, self.y_min, self.y_max]

        fig, ax = plt.subplots(figsize=(10, 4))
        draw_system(rays, system, axis_limits=axis_limits, text_y=self.text_y, ax=ax)
        return fig

    def refresh(self) -> None:
        """Regenerate the plot and push the new figure into the stable pane."""
        old = self._plot_pane.object
        self._plot_pane.object = self._make_figure()
        plt.close(old)

    def _on_axis_change(self, *_) -> None:
        if self.auto_update:
            self.refresh()

    # ------------------------------------------------------------------
    # Panel layout
    # ------------------------------------------------------------------

    def panel(self) -> pn.viewable.Viewable:
        # --- update button ---
        update_btn = pn.widgets.Button(name="Update plot", button_type="primary")
        update_btn.on_click(lambda _: self.refresh())

        # --- demo loader ---
        demo_files = sorted(DEMO_DIR.glob("*.jboptics"))
        demo_select = pn.widgets.Select(
            name="Demo file",
            options={p.stem: str(p) for p in demo_files},
        )
        load_demo_btn = pn.widgets.Button(name="Load demo", button_type="primary")
        load_demo_btn.on_click(
            lambda _: self._load_file(pathlib.Path(demo_select.value))
        )

        # --- load file from disk ---
        file_input = pn.widgets.FileInput(accept=".jboptics", name="Upload .jboptics")
        load_file_btn = pn.widgets.Button(name="Load uploaded file", button_type="default")

        def on_load_file(_):
            if file_input.value is None:
                return
            with tempfile.NamedTemporaryFile(suffix=".jboptics", delete=False) as tmp:
                tmp.write(file_input.value)
                tmp_path = pathlib.Path(tmp.name)
            self._load_file(tmp_path)
            tmp_path.unlink(missing_ok=True)

        load_file_btn.on_click(on_load_file)

        # --- save ---
        save_path_input = pn.widgets.TextInput(
            name="Save path", placeholder="output.jboptics", width=180
        )
        save_btn = pn.widgets.Button(name="Save", button_type="success")
        save_btn.on_click(lambda _: self._save_file(
            pathlib.Path(save_path_input.value.strip() or "output.jboptics")
        ))

        # --- thin-lens calculator ---
        calc_f_in = pn.widgets.FloatInput(name="f (mm)", value=100.0, width=90)
        calc_L_in = pn.widgets.FloatInput(name="L (mm)", value=400.0, width=90)
        calc_out = pn.pane.Str("", width=280)
        calc_btn = pn.widgets.Button(name="Solve d_i / d_o", button_type="default")

        def on_calc(_):
            results = solve_di_do_from_f_L(calc_f_in.value, calc_L_in.value)
            if not results:
                calc_out.object = "No real solution (L < 4f)"
            else:
                lines = [f"d_i={d_i:.2f}  d_o={d_o:.2f}  m={m:.3f}" for d_i, d_o, m in results]
                calc_out.object = "\n".join(lines)

        calc_btn.on_click(on_calc)

        # --- sidebar ---
        sidebar = pn.Column(
            pn.pane.Markdown("## Ray Tracer GUI"),
            pn.WidgetBox(
                pn.Row(
                    pn.widgets.FloatInput.from_param(self.param.x_min, width=90),
                    pn.widgets.FloatInput.from_param(self.param.x_max, width=90),
                ),
                pn.Row(
                    pn.widgets.FloatInput.from_param(self.param.y_min, width=90),
                    pn.widgets.FloatInput.from_param(self.param.y_max, width=90),
                ),
                pn.Row(
                    pn.widgets.FloatInput.from_param(self.param.text_y, width=90),
                    pn.widgets.Checkbox.from_param(self.param.auto_update),
                ),
                update_btn,
                name="Axis controls",
            ),
            pn.WidgetBox(
                pn.Row(demo_select, load_demo_btn),
                pn.Spacer(height=4),
                file_input,
                load_file_btn,
                pn.Spacer(height=4),
                pn.Row(save_path_input, save_btn),
                name="File I/O",
            ),
            pn.WidgetBox(
                pn.Row(calc_f_in, calc_L_in, calc_btn),
                calc_out,
                name="Thin-lens calculator",
            ),
            pn.pane.Markdown(HELP_TEXT, width=300),
            width=320,
        )

        # --- main area ---
        main = pn.Column(
            self._plot_pane,
            pn.pane.Markdown("### Rays"),
            self._ray_widget.widget(),
            pn.pane.Markdown("### Lenses"),
            self._lens_widget.widget(),
            sizing_mode="stretch_width",
        )

        return pn.Row(sidebar, main, sizing_mode="stretch_width")


dashboard = RayTracerDashboard()
dashboard.panel().servable(title="Ray Tracer GUI")
