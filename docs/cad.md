# Editable CAD and 3D files

**[Editing guide](freecad.md)** · **[3D configurator](https://eduarbo.github.io/filo36/)** · **[Configuration format and examples](customize.md)**

The current mechanical source is [`mechanical/revG/Filo36.FCStd`](../mechanical/revG/Filo36.FCStd). It contains both halves, native sketches/operations, editable parameters and 36 original KLP meshes. Commercial modules are nominal envelopes. RevG retains the unchanged revF PCB studies.

| Nominal measure | revF | revG |
|---|---:|---:|
| Cover maximum height | 16.6 mm, open rails | 16.6 mm, opaque frame |
| Display glass top | 16.1 mm | 16.1 mm |
| Key plate top | 7.6 mm | 7.6 mm |
| Electronics bay | 24 mm | 24 mm |
| Case width × depth, each half | ≈126.2 × 94.5 mm | Unchanged |
| North overhang past adjacent cap | 0 mm nominal | Unchanged |

Heights exclude the illustrative 1.2 mm feet. USB is only 0.045 mm behind the adjacent keycap’s north edge: this is a nominal alignment, not a physical tolerance guarantee.

## Files

- `mechanical/revG/Filo36.FCStd`: editable assembly.
- `mechanical/revG/*-assembly.step`: installed solid parts per half; no KLP mesh bodies.
- `mechanical/revG/*-frame-{smooth,bevel,facet}.{step,stl}`: all interchangeable cover styles.
- `mechanical/revG/*.step`, `*.stl`: individual prototype parts and identified envelopes.
- `keycaps/variants/`: all 38 unchanged Choc-stem KLP files, including unqualified study variants.
- `keycaps/catalog.json`: provenance, actual stem axes, convex envelopes and qualification.
- `design/configurations/`: default and two sculpted preset examples.
- `hardware/revF/`: two KiCad projects, schematic/PCB placement, local libraries and models; **unrouted**.
- `docs/images/revG-*.png`: renders calculated from exported meshes.
- Viewer: self-contained offline HTML, active-configuration GLB and JSON downloads.

Parts retain assembly coordinates. Printing orientation, fit, fastener lengths and final slicing settings are not qualified. Historical revE/revF sources and receipts remain available for comparison. To rebuild an older viewer, use its historical Git commit; the current shared viewer code targets revG.

## Rebuild the reference

These commands overwrite generated revG reference files. **Do not run them over a source you edited by hand.** Use a separate checkout for reconstruction and keep custom FCStd files elsewhere.

Tested tooling: FreeCAD 1.1.3, KiCad 10.0.6, StepUp 13.1.7 (package metadata 11.09.6), Python with `tools/requirements-render.txt`, and Node dependencies fixed in `viewer/package-lock.json`.

```sh
python -m pip install -r tools/requirements-render.txt
npm ci --prefix viewer
python tools/build_keycap_catalog.py
python tools/check_revG_config.py
FILO_QT_PLATFORM=cocoa python3 tools/freecad/run_macos.py tools/freecad/build_revG.py
FILO_QT_PLATFORM=cocoa python3 tools/freecad/run_macos.py tools/freecad/check_revG.py
python tools/render_revG.py
python tools/render_frames.py
python tools/build_viewer_revG.py
node viewer/build.mjs
python tools/check_viewer_revG.py
python3 tools/check_layout.py
node viewer/check.cjs
python3 tools/check_revG_delivery.py
```

The macOS helper uses an existing FreeCAD installation. It disables optional `flatmesh` only in its subprocess because that installed extension crashes on import; it does not modify application preferences. Cocoa is used because that runtime’s offscreen Qt backend failed on mesh recompute. On other systems, run the scripts through the equivalent installed FreeCAD Python environment.

After an authorized publication, `python3 tools/check_public_delivery.py COMMIT_SHA` checks an anonymous full source ZIP against every Git blob and compares public Pages with that commit. Its ZIP and receipt are reproducible under `build/revG/`; it does not publish anything.

The browser check needs Playwright and a Chromium-compatible browser. Set `FILO36_PLAYWRIGHT_MODULE` and `FILO36_BROWSER` if they are not on the usual path. It tests the generated file with HTTP(S) requests blocked; `FILO36_VIEWER_URL` instead selects the published URL.

The native configuration test also uses the scoped subprocess exit after its assertions, file writes and save/reopen readback to avoid the same Qt teardown crash. It does not suppress failed assertions or change installed FreeCAD.

The catalog build verifies SHA-256 and Git blob hashes of every pinned upstream STL. The geometry exporter checks closed printable solids, pair intersections and all three cover variants against components and a nominal USB plug corridor. The separate keycap checker includes complete-configuration envelopes and a travel/plate bound. Source hashes and results are under `validation/revG-*`.

`build/` is ignored and reproducible: native save/reopen trials come from `check_revG.py`; screenshots, test GLB/JSON and UI receipts from `viewer/check.cjs`; the viewer scene from `build_viewer_revG.py`. Source generations should be compared geometrically because STEP/FCStd metadata may vary.

## PCB exchange

RevG does not alter electrical files. The verified StepUp procedure and coordinate alignment are described in [the editing guide](freecad.md#3-inspect-the-pcb-with-stepup). To rerun the historical exchange test on temporary copies:

```sh
FILO_QT_PLATFORM=cocoa python3 tools/freecad/run_macos.py tools/freecad/check_stepup.py
```

Then run `tools/check_stepup_readback.py` with KiCad’s Python. The StepUp harness exits its own GUI subprocess after saving because that runtime crashes during Qt teardown; independent KiCad readback is required. The test must change only the example opening edge, without altering key positions, pads, connectivity or the outer contour.

`tools/sync_pcb_study.py` resets reference placement; it is not an automatic synchronizer for hand-edited designs. Never use it to discard routing. The current electrical receipt remains [revF-electrical.json](../validation/revF-electrical.json).

## Remaining hardware work

The cradle opening has 0.15 mm nominal clearance per side and about 0.22 mm to nearby pads, failing the configured 0.5 mm copper-to-edge rule. Both boards have 104 unconnected items; other edge, courtyard and silkscreen findings remain. Do not lower the rules to turn this into a manufacturing approval.

Cables, precise sockets/contact lengths, retention, printed fits, keycap insertion, screw access with real tools, RF behavior under covers, charging and power consumption still require verification. The new caps/frames do not close those requirements.
