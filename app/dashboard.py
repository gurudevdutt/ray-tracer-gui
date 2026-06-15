"""Main entry point for the ray-tracer-gui Panel application.

Launch with:
    panel serve app/dashboard.py --show
"""

from __future__ import annotations

import io
import pathlib

import matplotlib

matplotlib.use("agg")
import matplotlib.pyplot as plt
import panel as pn
import param

from raytracergui.io import load_jboptics, save_jboptics
from raytracergui.plot import draw_system
from raytracergui.system import OpticalSystem
from raytracergui.thinlens import solve_di_do_from_f_L

from app.widgets import LensTableWidget, RayTableWidget

pn.extension("tabulator")

DEMO_DIR = pathlib.Path(__file__).parent.parent / "demo_optics_files"
DEFAULT_STARTUP = DEMO_DIR / "default_startup.jboptics"


# ---------------------------------------------------------------------------
# Dashboard component
# ---------------------------------------------------------------------------


class RayTracerDashboard(param.Parameterized):
    """Interactive paraxial ray-tracer dashboard."""

    # axis controls
    x_min = param.Number(default=-100.0, label="X min (mm)")
    x_max = param.Number(default=800.0, label="X max (mm)")
    y_min = param.Number(default=-10.0, label="Y min (mm)")
    y_max = param.Number(default=10.0, label="Y max (mm)")
    text_y = param.Number(default=4.0, label="Label offset (mm)")

    # auto-update toggle
    auto_update = param.Boolean(default=True, label="Auto update")

    def __init__(self, **params):
        super().__init__(**params)
        self._ray_widget = RayTableWidget()
        self._lens_widget = LensTableWidget()
        self._load_file(DEFAULT_STARTUP)

    # ------------------------------------------------------------------
    # I/O
    # ------------------------------------------------------------------

    def _load_file(self, path: pathlib.Path) -> None:
        if not path.exists():
            return
        result = load_jboptics(path)
        self._ray_widget = RayTableWidget(rays=result["rays"])
        self._lens_widget = LensTableWidget(elements=result["elements"])
        axis = result["axis"]
        if len(axis) == 4:
            self.x_min, self.x_max, self.y_min, self.y_max = axis
        self.text_y = result["text_y"]

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

    def _make_figure(self) -> bytes:
        rays = self._ray_widget.to_rays()
        elements = self._lens_widget.to_elements()
        system = OpticalSystem(elements)
        axis_limits = [self.x_min, self.x_max, self.y_min, self.y_max]

        fig, ax = plt.subplots(figsize=(10, 4))
        draw_system(rays, system, axis_limits=axis_limits, text_y=self.text_y, ax=ax)
        fig.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=100)
        plt.close(fig)
        buf.seek(0)
        return buf.read()

    # ------------------------------------------------------------------
    # Panel layout
    # ------------------------------------------------------------------

    def panel(self) -> pn.viewable.Viewable:
        # --- update button ---
        update_btn = pn.widgets.Button(name="Update plot", button_type="primary")
        plot_pane = pn.pane.PNG(self._make_figure(), sizing_mode="stretch_width")

        def on_update(_):
            plot_pane.object = self._make_figure()

        update_btn.on_click(on_update)

        # auto-update when axis params change
        @param.depends(
            self.param.x_min,
            self.param.x_max,
            self.param.y_min,
            self.param.y_max,
            self.param.text_y,
            watch=True,
        )
        def _auto_update(*_):
            if self.auto_update:
                plot_pane.object = self._make_figure()

        # --- demo loader ---
        demo_files = sorted(DEMO_DIR.glob("*.jboptics"))
        demo_select = pn.widgets.Select(
            name="Load demo",
            options={p.stem: str(p) for p in demo_files},
        )
        load_demo_btn = pn.widgets.Button(name="Load demo", button_type="default")

        def on_load_demo(_):
            path = pathlib.Path(demo_select.value)
            self._load_file(path)
            plot_pane.object = self._make_figure()

        load_demo_btn.on_click(on_load_demo)

        # --- save/load file widgets ---
        file_input = pn.widgets.FileInput(accept=".jboptics")
        load_file_btn = pn.widgets.Button(name="Load file", button_type="default")
        save_path_input = pn.widgets.TextInput(name="Save path", placeholder="output.jboptics")
        save_btn = pn.widgets.Button(name="Save", button_type="success")

        def on_load_file(_):
            if file_input.value is None:
                return
            import tempfile

            with tempfile.NamedTemporaryFile(suffix=".jboptics", delete=False) as tmp:
                tmp.write(file_input.value)
                tmp_path = pathlib.Path(tmp.name)
            self._load_file(tmp_path)
            tmp_path.unlink(missing_ok=True)
            plot_pane.object = self._make_figure()

        def on_save(_):
            p = save_path_input.value.strip() or "output.jboptics"
            self._save_file(pathlib.Path(p))

        load_file_btn.on_click(on_load_file)
        save_btn.on_click(on_save)

        # --- thin-lens calculator ---
        calc_f_in = pn.widgets.FloatInput(name="f", value=100.0)
        calc_L_in = pn.widgets.FloatInput(name="L", value=400.0)
        calc_out = pn.pane.Str("")
        calc_btn = pn.widgets.Button(name="Solve d_i / d_o", button_type="default")

        def on_calc(_):
            results = solve_di_do_from_f_L(calc_f_in.value, calc_L_in.value)
            if not results:
                calc_out.object = "No real solution (L < 4f)"
            else:
                lines = []
                for d_i, d_o, m in results:
                    lines.append(f"d_i={d_i:.3f}  d_o={d_o:.3f}  m={m:.3f}")
                calc_out.object = "\n".join(lines)

        calc_btn.on_click(on_calc)

        # --- layout ---
        axis_controls = pn.WidgetBox(
            pn.Row(
                pn.widgets.FloatInput.from_param(self.param.x_min),
                pn.widgets.FloatInput.from_param(self.param.x_max),
                pn.widgets.FloatInput.from_param(self.param.y_min),
                pn.widgets.FloatInput.from_param(self.param.y_max),
                pn.widgets.FloatInput.from_param(self.param.text_y),
            ),
            pn.Row(
                pn.widgets.Checkbox.from_param(self.param.auto_update),
                update_btn,
            ),
            name="Axis controls",
        )

        io_controls = pn.WidgetBox(
            pn.Row(demo_select, load_demo_btn),
            pn.Row(file_input, load_file_btn),
            pn.Row(save_path_input, save_btn),
            name="File I/O",
        )

        calculator = pn.WidgetBox(
            pn.Row(calc_f_in, calc_L_in, calc_btn),
            calc_out,
            name="Thin-lens calculator",
        )

        sidebar = pn.Column(
            axis_controls,
            io_controls,
            calculator,
            width=320,
        )

        tables = pn.Column(
            pn.pane.Markdown("### Rays"),
            self._ray_widget.widget(),
            pn.pane.Markdown("### Lenses"),
            self._lens_widget.widget(),
        )

        main = pn.Column(
            plot_pane,
            tables,
            sizing_mode="stretch_width",
        )

        return pn.Row(sidebar, main, sizing_mode="stretch_width")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

dashboard = RayTracerDashboard()
dashboard.panel().servable(title="Ray Tracer GUI")
