# CLAUDE.md — ray-tracer-gui

This file holds the project facts (layout, environment, conventions, physics, file formats) for
`ray-tracer-gui`. Sub-agent orchestration and review rules live in **[AGENTS.md](./AGENTS.md)** —
read both before working.

---

## Project overview

**ray-tracer-gui** is a Python package for simple 2-D **paraxial ray tracing** through a
sequence of thin lenses and planes along an optical axis. It is a translation and extension of a
MATLAB ray-tracing GUI originally developed by **Jonny Beaumariage** in the **Dutt Group** at the
University of Pittsburgh.

The original MATLAB source is included in this repository in the folder `matlab-ray-tracer-gui/`.
See README.md for attribution details.

The intended users are researchers in quantum optics and photonics who need a quick, interactive
paraxial layout of a lens system — propagating rays through a stack of thin lenses, visualizing
where they cross the axis, and reading off image/object distances — without the ray-cutoff and
aperture complications of a full ray tracer. (Rays are *not* clipped at lens apertures; the
diameter column is used only for drawing the lens extent.)

The package name was chosen to match the MATLAB tool and to avoid conflicts with existing PyPI
packages, which may be installed alongside this one for validation and comparison.

> ⚠️ **Note on the import name.** `ray-tracer-gui` is the *distribution* (PyPI/repo) name, but
> hyphens are illegal in Python import names. The importable package is **`raytracergui`** (see
> repository layout below). Keep the two distinct: `pip install ray-tracer-gui`,
> `import raytracergui`.

---

## Repository layout

```
ray-tracer-gui/
├── CLAUDE.md                        ← you are here (project facts: layout, env, physics, formats)
├── AGENTS.md                        ← sub-agent governance & delegation sequence
├── README.md
├── LICENSE
├── .gitignore
├── pyproject.toml                   ← build system, dependencies, tool config (setuptools)
├── .venv/                           ← local virtual environment (never committed)
├── src/
│   └── raytracergui/                ← importable package (underscore-free, no hyphens)
│       ├── __init__.py
│       ├── ray.py                   ← Ray data structure (height y, slope u = tan θ)
│       ├── element.py               ← thin-lens / plane element (distance, f, diameter, on/off, name)
│       ├── system.py                ← OpticalSystem: ordered list of elements + propagation engine
│       ├── trace.py                 ← paraxial propagate-then-refract loop (the physics core)
│       ├── thinlens.py              ← thin-lens equation solver (f / d_i / d_o / L from any two)
│       ├── io.py                    ← load/save .jboptics (MATLAB .mat) configs via scipy.io
│       └── plot.py                  ← matplotlib plotting helpers (rays, lenses, zoom-in legend)
├── tests/
│   ├── conftest.py
│   ├── test_ray.py
│   ├── test_element.py
│   ├── test_system.py
│   ├── test_trace.py
│   ├── test_thinlens.py
│   └── test_io.py
├── app/                             ← interactive GUI (browser-based)
│   ├── dashboard.py                 ← main entry point
│   └── widgets.py                   ← reusable widgets for ray/lens tables and axis controls
├── notebooks/                       ← Jupyter notebooks for exploration / figures
├── scripts/                         ← standalone run/comparison scripts
├── demo_optics_files/               ← .jboptics demo configs (ported from MATLAB demos folder)
└── matlab-ray-tracer-gui/           ← original MATLAB source, vendored read-only for reference
```

---

## Environment — always use the local `.venv`

**All Python commands must use the project's local virtual environment.**
Never use the system Python or any globally installed packages.

```bash
# Create (one-time, from repo root)
python3 -m venv .venv

# Activate (macOS / zsh)
source .venv/bin/activate

# Install package in editable mode with dev dependencies
pip install -e ".[dev]"
```

When running tests, scripts, or any Python code, always use the venv Python explicitly:

```bash
.venv/bin/python -m pytest tests/
.venv/bin/python scripts/run_demo_system.py
```

**Never** run `pip install` without the venv active. **Never** use `sudo pip`.

---

## Running tests

```bash
# All tests
.venv/bin/python -m pytest tests/ -v

# Single file
.venv/bin/python -m pytest tests/test_trace.py -v

# With coverage
.venv/bin/python -m pytest tests/ --cov=raytracergui --cov-report=term-missing
```

Tests must pass before any commit to `main`. When adding new functionality, write a corresponding
test in `tests/` before declaring the task complete.

---

## pyproject.toml conventions

Uses `pyproject.toml` with a **setuptools** backend. No `setup.py`, `setup.cfg`, or
`requirements.txt`.

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "ray-tracer-gui"
version = "0.1.0"
description = "Simple 2-D paraxial ray tracing through thin-lens systems, with an interactive GUI"
readme = "README.md"
requires-python = ">=3.10"
license = { text = "MIT" }
dependencies = [
    "numpy>=1.24",
    "scipy>=1.10",
    "matplotlib>=3.7",
]

[project.optional-dependencies]
dev = [
    "pytest>=7",
    "pytest-cov",
    "ruff",
]
app = [
    "panel>=1.4",
    "param>=2.1",
    "bokeh>=3.3",
]

[tool.setuptools.packages.find]
where = ["src"]

[tool.ruff]
line-length = 100

[tool.pytest.ini_options]
testpaths = ["tests"]
```

> Note: `scipy` is a hard dependency because `.jboptics` files are MATLAB `.mat` files and are
> read/written with `scipy.io.loadmat` / `savemat`.

---

## Code style

- Formatter / linter: **ruff** (included in `[dev]`)
- Line length: 100 characters
- Docstrings: NumPy style
- Type hints: required for all public functions and class methods
- All physical quantities must document their units in the docstring

```bash
.venv/bin/python -m ruff check src/ tests/
.venv/bin/python -m ruff format src/ tests/
```

---

## Domain conventions

This is a paraxial geometric-optics library. Follow these conventions consistently — they mirror
the MATLAB source exactly.

| Quantity | Symbol | Internal unit | Notes |
|---|---|---|---|
| Position along optical axis | `x` | millimetres | Horizontal axis of the plot |
| Ray height | `y` | millimetres | Transverse distance from the optical axis |
| Ray angle | `theta` | degrees at the API boundary | User enters degrees; stored/computed as a slope (see below) |
| Ray slope | `u` | dimensionless | `u = tan(theta)`; this is the propagated quantity, **not** the angle |
| Focal length | `f` | millimetres | `+` converging, `−` diverging, `inf` = flat plane (no refraction) |
| Element spacing | `d` | millimetres | Distance from the **previous** element (relative, not absolute) |
| Lens diameter | `D` | millimetres | Drawing extent only — rays are **not** clipped at the aperture |
| On/off flag | `on` | `0` or `1` | Effective focal length is `f / on`; `on = 0` → `inf` → drawn as a dashed plane |

**Paraxial propagation core (the heart of the port).** For each ray, starting from the user-supplied
initial height `y₀` and slope `u₀ = tan(θ₀)`, step through the ordered element list. At element `j`
(spacing `d_j`, effective focal `f_j`):

```
y_{j+1} = y_j + u_j · d_j          # free-space propagation to element j+1
u_{j+1} = u_j − y_{j+1} / f_j      # thin-lens refraction kick
```

This is the explicit form of the ABCD ray-transfer matrices (translation `[[1, d],[0, 1]]` then
thin lens `[[1, 0],[-1/f, 1]]`). A flat plane has `f = inf`, so the refraction term vanishes and
the ray passes straight through. The Python port should preserve the convention that `u`, not the
angle, is the propagated state variable. Vectorizing over rays is fine, but keep the per-element
recurrence identical to the MATLAB loop and cover it with a regression test.

**Element ordering:** elements are stored top-down in the order light encounters them; spacings are
**relative to the previous element**, with the first element's `d` measured from the ray origin at
`x = 0`. Absolute positions are the cumulative sum of spacings.

---

## MATLAB codebase summary

The `matlab-ray-tracer-gui/` directory contains the original MATLAB GUIDE application. It is small
(one main file plus a tiny opener and demo configs). Here is what each part does, to guide the port.

### `ray_tracer_gui.m` ★ THE WHOLE APPLICATION
A single-file MATLAB GUIDE app (paired with `ray_tracer_gui.fig`). Responsibilities, by section:

- **GUI scaffolding** (`*_OpeningFcn`, `*_OutputFcn`, `gui_mainfcn`): GUIDE boilerplate; loads
  `demo_optics_files/default_startup.jboptics` on launch and populates the two tables and axis
  inputs. → Replaced by `app/dashboard.py`; not ported into the library.
- **`update_display` / `conditional_update_display`**: master redraw; honours an "auto update"
  toggle. → `app/` redraw logic.
- **`plot_rays`** ★: the physics core. Builds the cumulative `x_vec` of element positions, then for
  each ray runs the propagate-then-refract recurrence above and plots `y` vs `x`. → `trace.py`
  (engine) + `plot.py` (drawing).
- **`plot_rays_zoomin`**: duplicates the main axes into a second axes and auto-scales it to the ray
  origin, giving a quick colour/linestyle legend. Four cases on (zero/finite slope spread) ×
  (zero/finite height spread). → `plot.py` helper; optional in the first port.
- **`plot_lenses` / `plot_single_lens`**: draws each element as a vertical line of height `D`
  centred on the axis; lenses solid, planes (`f = inf`) dashed; renders the name label with a
  vertical offset (`text_y`). → `plot.py`.
- **Ray table callbacks** (`add_ray_button`, `ray_table_CellEditCallback`): columns are
  `{height, angle(deg), color, linestyle, delete-flag}`. Column 5 == 1 deletes the row. → `Ray`
  dataclass + `app/` table handling.
- **Lens table callbacks** (`add_lens_button`, `insert_lens_button`, `lens_table_CellEditCallback`):
  columns are `{spacing, focal_length, diameter, on/off, name, delete-flag}`. `insert_lens_button`
  inserts an element above a chosen row with one of three spacing strategies (preserve spacings by
  halving, add new space, or new front lens). Column 6 == 1 deletes the row. → `Element` dataclass
  + `system.py` insertion logic.
- **Axis / text-offset inputs** (`x_min_input`, …, `text_offset_input`): plot bounds and label
  offset. → `app/` controls; persisted in the config.
- **Save / load / load-demo** (`save_button`, `load_button`, `load_demo_button`): read/write
  `.jboptics` files (see below). → `io.py`.
- **`pop_out_button_ClickedCallback`**: copies an axes into a standalone figure with axis labels
  (`optical axis (mm)`, `height (mm)`). → `plot.py` / `app/` export.
- **Thin-lens calculator** (`calculate_f_button`, `calculate_i_button`, `calculate_o_button`,
  `calculate_L_button`, `get_inputs`): solves the thin-lens equation `1/f = 1/d_i + 1/d_o` and the
  `L = d_i + d_o` constraint for whichever quantity is missing, given any two. Handles the
  quadratic case (solving for d_i or d_o from `f` and `L`), including the `L < 4f` (no real
  solution) and `L = 4f` (unique double root) cases, and asks the user to pick between the two
  roots with their magnifications. → `thinlens.py` (pure functions; the root-choice prompt becomes
  a return of both solutions + magnifications, with selection left to the caller/UI).

### `openjboptics.m`
A tiny "open" handler: when a user double-clicks a `.jboptics` file, it `load`s it as a `.mat` into
the base workspace. → No direct Python equivalent needed; documents the file format only.

### `.jboptics` file format (verified against `demo_4f_reimaging.jboptics`)
A `.jboptics` file is a **MATLAB v5 `.mat` file** with a custom extension (for easy sorting). It
contains a single struct `data` with exactly four fields:

| Field | MATLAB type | Shape | Columns / meaning |
|---|---|---|---|
| `data.ray_data` | cell array | `(n_rays, 5)` | `{height, angle_deg, color, linestyle, delete}` |
| `data.lens_data` | cell array | `(n_elem, 6)` | `{spacing, f, diameter, on, name, delete}` |
| `data.current_axis` | numeric | `(1, 4)` | `[xmin, xmax, ymin, ymax]` |
| `data.text_y` | numeric | `(1, 1)` | label vertical offset |

Read/write with `scipy.io.loadmat` / `savemat` in `io.py`. **Parsing gotchas observed in the real
demo file — handle all of these in `io.py` and cover with tests:**

- `loadmat` returns the struct as `m['data'][0,0]`; access fields by name on that element.
- Every numeric cell comes back **doubly nested** (e.g. `array([[0]])`). Unwrap with `.item()` (or
  `float(np.asarray(v).ravel()[0])`), never by assuming a scalar.
- Per-cell dtypes are **inconsistent**: MATLAB stores `0` and `3` as `uint8` but `-3` and `-1` as
  `int16` in the same column. **Coerce every numeric field to `float`** on read; do not trust the
  stored dtype (a `uint8` view would corrupt negatives in other files).
- `f = inf` (the plane / lens-off case) survives as a float `inf` — preserve it; do not coerce to a
  large finite number or to int.
- String cells (`color`, `linestyle`, `name`) come back as length-1 arrays
  (e.g. `array(['k'])`); unwrap with `str(np.asarray(v).ravel()[0])`.
- On **write**, build cell arrays as `np.empty((rows, cols), dtype=object)` so `savemat` emits a
  MATLAB cell array (not a numeric matrix), matching what the MATLAB GUI expects.

Preserve round-trip compatibility so configs saved by the MATLAB GUI load in the Python tool and
vice versa. Use `demo_4f_reimaging.jboptics` as the canonical regression fixture: it is a 4f
relay (lens `f = 100`, then a flat plane, spacings 200/200) with 9 rays = 3 heights × 3 angles, so
it exercises positive/negative heights, positive/negative angles, a finite lens, and an `inf`
plane in one file.

### Converting the demo files
`demo_optics_files/` will hold the ported demos. **No format conversion is required** — `.jboptics`
files are already valid `.mat` files and `io.py` reads them directly via `scipy.io.loadmat`. The
task is therefore:
1. Copy the existing `.jboptics` files into `demo_optics_files/` unchanged.
2. Write `io.load_jboptics(path)` so it reads them per the gotchas above.
3. Add a round-trip test: load each demo, assert the parsed `OpticalSystem` + rays match expected
   values, save to a temp `.jboptics`, reload, and assert equality.

Only if a *native* Python format is later wanted (e.g. JSON/YAML for git-friendly diffs) should a
converter be added — as an **optional** `scripts/` utility, never replacing `.jboptics` support,
since the MATLAB GUI must keep reading these files.

### `ray_tracer_gui.fig`
The GUIDE layout (binary). Not ported; the Python UI is rebuilt in `app/`. Keep it in
`matlab-ray-tracer-gui/` for reference only.

---

## MATLAB-to-Python translation workflow

1. Read the relevant MATLAB section carefully. Understand the physical model before writing Python.
2. Write the Python equivalent in the appropriate module under `src/raytracergui/`.
3. Write a test in `tests/` that validates the Python output against either:
   - Analytical results (preferred — e.g. a single lens images per the thin-lens equation), or
   - Hardcoded numerical outputs from the MATLAB recurrence (acceptable as a regression test).
4. Mark MATLAB-derived numerical test fixtures with `# MATLAB reference value`.
5. Do **not** delete or modify any file in `matlab-ray-tracer-gui/` — treat it as read-only.
6. Document the numerical tolerance used for comparison in the test docstring.

**Translation priority order:**
1. `trace.py` — the propagate-then-refract engine (from `plot_rays`). This is the core; do it first.
2. `ray.py` / `element.py` — the `Ray` and `Element` data structures (from the two tables).
3. `system.py` — `OpticalSystem` (ordered elements, cumulative positions, insertion logic).
4. `thinlens.py` — the thin-lens-equation solver (from the four `calculate_*` callbacks).
5. `io.py` — `.jboptics` load/save (from `save_button` / `load_button` / `openjboptics.m`).
6. `plot.py` — ray/lens drawing and the zoom-in legend (from `plot_rays`/`plot_lenses`/zoomin).

---

## Interactive GUI (`app/`)

The MATLAB tool was a GUIDE GUI; the Python equivalent lives in `app/`. The simulation/physics in
`src/raytracergui/` must remain **completely UI-agnostic** — importable and testable with no GUI
dependency.

**Architecture rule (one-way dependency):** `app/` imports from `raytracergui`; `raytracergui` must
never import from `app/`, and must never `import panel`/`import param` inside `src/raytracergui/`.

**GUI framework: Panel (HoloViz).** Browser-based — `panel serve app/dashboard.py --show` starts a
local Bokeh server (default `http://localhost:5006`) and opens the GUI in a browser tab; the same
code also runs inline in a Jupyter notebook or headless on a remote machine (no Qt / display server
needed), which suits a Mac Studio or remote setup. The two editable MATLAB tables (rays, lenses)
map onto `Tabulator` widgets backed by lists of the `Ray` and `Element` dataclasses; the axis
inputs and `text_y` map onto a small config object that round-trips through `.jboptics`.

---

## Git workflow

- `main`: stable, tested code only
- `dev`: integration branch for in-progress work
- Feature branches: `feature/<short-description>`

Commit messages: imperative mood, ≤72-character subject line.
Example: `Add paraxial propagate-then-refract trace engine`

Do not commit: `.venv/`, `__pycache__/`, `*.pyc`, `.ipynb_checkpoints/`, large binary files.

---

## What Claude Code should and should not do

**Always:**
- Use `.venv/bin/python` for all Python execution
- Run `pytest` after any non-trivial code change before declaring the task complete
- Keep all files in `matlab-ray-tracer-gui/` untouched (read-only reference)
- Add NumPy-style docstrings with units to every new public function
- Follow the element-ordering and unit conventions in the domain conventions table
- Keep the `u = tan(theta)` slope convention; do not silently switch to small-angle `u ≈ theta`

**Never:**
- Install packages system-wide (`sudo pip` or bare `pip` outside the venv)
- Modify `pyproject.toml` without noting it in the commit message
- Delete or rename existing test files without explicit instruction
- Import GUI libraries (`panel`, `param`, `PyQt`) inside `src/raytracergui/`
- Push directly to `main` without passing tests

---

## Paths on this machine

```
MATLAB source (read-only):  vendored in-repo at ./matlab-ray-tracer-gui/
New Python repo:            /Users/gurudevdutt/CursorProjects/ray-tracer-gui/
```

The original MATLAB source is vendored inside the repo at `matlab-ray-tracer-gui/` and treated as
read-only reference (see the repository-layout and "what Claude should not do" sections).

Claude Code should initialize the git repo if not already initialized, and scaffold the directory
structure in `/Users/gurudevdutt/CursorProjects/ray-tracer-gui/`.

---

## Add Acknowledgements to the repo README

Once the Python code, scaffolding, and README.md exist, include this acknowledgement in README.md.

The paraxial ray-tracing engine, lens-system data structures, and interactive layout in
`ray-tracer-gui` are a Python translation and extension of a MATLAB ray-tracing GUI originally
developed by **Jonny Beaumariage** in the **Dutt Group** (Department of Physics and Astronomy,
University of Pittsburgh). The propagate-then-refract paraxial engine and the `.jboptics`
configuration format derive directly from that work. Gurudev Dutt architected the Python port of ray-tracer-gui — the module structure, paraxial-tracing API, and test strategy — and implemented it using Claude Code, working from the original MATLAB GUI by Jonny Beaumariage.

If you use `ray-tracer-gui` in published research, please consider acknowledging the original
MATLAB codebase and its author.
