# Specialized Sub-Agent Guidance

## Purpose

This document governs specialized sub-agents delegated work on `ray-tracer-gui`. The primary coding
agent owns integration decisions, implementation, and final verification. Sub-agents provide focused
reviews and test design; they do not independently redefine the optics model or write production
code in place of the primary agent.

Before working, every sub-agent must read:

- `CLAUDE.md` (project facts: layout, environment, physics conventions, `.jboptics` format)
- The vendored MATLAB source under `matlab-ray-tracer-gui/` relevant to the module in question

## Installed Claude Agents

The following definitions are expected in `~/.claude/agents`:

- `architect.md`
- `code-reviewer.md`
- `security-reviewer.md`
- `test-writer.md`

## Shared Rules

All sub-agents must enforce these project rules:

- The MATLAB source in `matlab-ray-tracer-gui/` is **read-only reference**. Never edit, move, or
  delete it.
- The paraxial state variable is the **slope `u = tan(theta)`**, not the angle. Do not silently
  switch to the small-angle approximation `u ~= theta`.
- The per-element recurrence must stay identical to the MATLAB loop:
  `y_{j+1} = y_j + u_j * d_j`, then `u_{j+1} = u_j - y_{j+1} / f_j`. A flat plane has `f = inf`
  (refraction term vanishes); the on/off flag gives effective focal `f / on`.
- Element spacings are **relative to the previous element**; absolute positions are the cumulative
  sum. The first spacing is measured from the ray origin at `x = 0`.
- `.jboptics` files are MATLAB v5 `.mat` files. **Never `eval`/`exec` file contents** — the original
  `openjboptics.m` used `evalin('base', 'load(...)')`; the Python port must use
  `scipy.io.loadmat` only. Round-trip compatibility with the MATLAB GUI must be preserved.
- Numeric cells from `.jboptics` are coerced to `float` on read regardless of stored dtype;
  `f = inf` is preserved, never coerced to a finite number.
- The library (`src/raytracergui/`) stays UI-agnostic: it must never import `panel`/`param`, and
  `app/` depends on the library, never the reverse.
- Findings must cite specific files, symbols, or proposed API elements.
- Do not recommend a full geometric ray tracer, aperture clipping, or non-paraxial optics for the
  initial port; this tool is paraxial by design and does not clip rays at apertures.

## Architect

Invoke before:

- Creating the new repository structure.
- Defining or changing the `Ray`, `Element`, or `OpticalSystem` public API.
- Changing dependency direction between `src/raytracergui/`, `app/`, and `io.py`.
- Introducing a new module or splitting an existing one.

The architect must verify:

- Physics (`trace.py`) operates independently from plotting, I/O, and the GUI.
- `plot.py` and `io.py` depend on the domain model, not the reverse.
- The propagation engine is separable from drawing and from `.jboptics` serialization.
- The `u = tan(theta)` slope state is represented explicitly in the `Ray` model.
- Element ordering and relative spacing are modeled explicitly in `OpticalSystem`.
- The thin-lens solver (`thinlens.py`) is pure functions, with root selection left to the caller.
- The proposal remains testable with small deterministic fixtures.

Expected output: `APPROVED` or `NEEDS CHANGES`, with concrete reasons.

## Code Reviewer

Invoke after:

- Any change to the propagation engine, data structures, system assembly, thin-lens solver,
  `.jboptics` I/O, or plotting.
- Changes to the slope/angle convention, sign handling, or `inf` (plane / lens-off) handling.
- Changes affecting element insertion, relative spacing, or cumulative position computation.

The code reviewer must prioritize:

- Faithfulness of the per-element recurrence to the MATLAB loop.
- Correct sign and `tan`/`inf` handling, including diverging lenses and flat planes.
- Relative-vs-absolute spacing consistency.
- Round-trip integrity of `.jboptics` load/save against the MATLAB format.
- Clear error behavior instead of silently discarded rays/elements.
- Tests for every new branch and edge case (empty tables, single element, `inf` plane, negatives).

Expected output: issues grouped by severity, followed by a concise verdict.

## Security Reviewer

Invoke before commits that touch:

- `io.py` or any `.jboptics` (MATLAB `.mat`) reading/writing.
- File path handling for load/save/load-demo.
- Any new external I/O or process invocation.

The security reviewer must verify:

- File contents are never passed to `eval`/`exec`; loading uses `scipy.io.loadmat` only.
- Paths are validated before opening; no execution of loaded data.
- No surprising filesystem writes outside intended save locations.
- No bundled real personal data beyond the intended `demo_optics_files/` configs.

Expected output: `CLEAN` or `VULNERABILITIES FOUND` with severity and locations.

Note: outside `io.py` and path handling, this paraxial library has negligible attack surface; the
physics and plotting modules may be fast-passed.

## Test Writer

Invoke before or alongside implementation of:

- The paraxial propagation engine (`trace.py`).
- The `Ray` / `Element` / `OpticalSystem` data structures.
- The thin-lens equation solver (`thinlens.py`).
- `.jboptics` load/save (`io.py`).

The test writer should derive tests from the physics conventions in `CLAUDE.md` and the MATLAB
recurrence, with small readable fixtures and exact expected values. Mark MATLAB-derived expected
values with `# MATLAB reference value` and state the numerical tolerance in each test docstring.

Required test categories:

- Happy path: multi-lens system propagation matching hand-computed `(y, u)` values.
- Analytic ground truth: a single `f` lens images an on-axis source per `1/f = 1/d_i + 1/d_o`.
- A flat plane (`f = inf`) leaves `(y, u)` unchanged.
- Diverging lens (`f < 0`) bends rays away from the axis with correct sign.
- Boundary/empty: no rays, no elements, single element, single ray.
- Negative heights and negative angles (the demo fixture exercises both).
- Element insertion preserving vs adding spacing; relative-to-absolute position correctness.
- Thin-lens solver: solve for f / d_i / d_o / L from any two inputs.
- Thin-lens degenerate cases: `L < 4f` (no real solution), `L = 4f` (unique double root), and the
  two-root case returning both solutions with magnifications.
- `.jboptics` round-trip: load `demo_4f_reimaging.jboptics`, assert parsed system + rays, save to a
  temp file, reload, assert equality. Parametrize over all files in `demo_optics_files/`.
- `.jboptics` parsing edge cases: doubly-nested scalars, mixed per-cell dtypes coerced to float,
  `f = inf` preserved, string cells unwrapped.

Expected output: test cases first, followed by any ambiguity found in the specification.

## Delegation Sequence

For substantial work, use this sequence per module (in the translation priority order in
`CLAUDE.md`: `trace.py` first, then data structures, `system.py`, `thinlens.py`, `io.py`,
`plot.py`):

1. Primary agent drafts or updates the relevant design note.
2. Architect reviews the design before implementation.
3. Test writer defines executable examples (tests precede implementation).
4. Primary agent implements the module and runs `pytest` + `ruff`.
5. Code reviewer reviews the completed change.
6. Security reviewer reviews changes touching `io.py` or path/external I/O.
7. Primary agent resolves findings and performs final verification.

Sub-agent approval does not replace passing tests or `.jboptics` round-trip reconciliation against
the MATLAB-format demo files.
