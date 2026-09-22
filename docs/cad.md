# Editable CAD and 3D files

**[Editing guide](freecad.md)** · **[3D configurator](https://eduarbo.github.io/filo36/)** · **[Configuration format and examples](customize.md)**

The current mechanical source is [`mechanical/revI/Filo36.FCStd`](../mechanical/revI/Filo36.FCStd). It contains both halves, native sketches/operations, editable parameters and 36 original KLP meshes. Commercial modules are nominal envelopes. The matching revI KiCad studies use the chosen contour and internal battery/magnet clearances. Five auxiliary/mounting footprints move; all key transforms and nets are preserved.

| Nominal measure | Revision I |
|---|---:|
| Frame maximum height | 16.6 mm plain / 17.2 mm themed |
| Display glass top | 16.1 mm |
| Key plate top | 7.6 mm |
| Electronics bay | 24 mm |
| Case width × depth, each half | 117 × 92.85 mm |
| Case control corners / radius | 20 / R0.8 mm |
| Battery aperture | 12.5 × 33.6 mm |
| North overhang past adjacent cap | 0 mm nominal |

Heights exclude the illustrative 1.2 mm feet. USB is only 0.045 mm behind the adjacent keycap’s north edge: this is a nominal alignment, not a physical tolerance guarantee.

## Files

- `mechanical/revI/Filo36.FCStd`: editable assembly.
- `mechanical/revI/*-assembly.step`: installed solid parts per half; no KLP mesh bodies.
- `mechanical/revI/*-frame-{smooth,bevel,facet,handheld,tv,cyberpunk}.{step,stl}`: all interchangeable cover styles.
- `mechanical/revI/*.step`, `*.stl`: individual prototype parts and identified envelopes.
- `mechanical/revI/*-battery-{adafruit-1570,301230}.stl`: selectable nominal cell envelopes.
- `mechanical/revI/coupon-*.{step,stl}`: actual magnetic/thread interface samples.
- `keycaps/variants/`: all 38 unchanged Choc-stem KLP files, including unqualified study variants.
- `keycaps/catalog.json`: provenance, actual stem axes, convex envelopes and qualification.
- `design/configurations/`: default and two sculpted preset examples.
- `hardware/revI/`: two KiCad projects, schematic/PCB placement, local libraries and models; **unrouted**.
- `docs/images/revI-*.png`: renders calculated from exported meshes.
- Viewer: self-contained offline HTML, active-configuration GLB and JSON downloads.

Parts retain assembly coordinates. Screw envelopes and nominal engagement are modeled; physical fits, printing orientation and final slicing settings are not qualified. Historical revE/revF/revG/revH sources and receipts remain available for comparison. To rebuild an older viewer, use its historical Git commit; the current shared viewer code targets revI.

## Rebuild the reference

These commands overwrite generated revI reference files. **Do not run them over a source you edited by hand.** Use a separate checkout for reconstruction and keep custom FCStd files elsewhere.

Tested tooling: FreeCAD 1.1.3, KiCad 10.0.6, StepUp 13.1.7 (package metadata 11.09.6), Python with `tools/requirements-render.txt`, and Node dependencies fixed in `viewer/package-lock.json`.

```sh
python -m pip install -r tools/requirements-render.txt
npm ci --prefix viewer
python tools/build_revI_profiles.py
python tools/build_revI_wire.py
python tools/build_keycap_catalog.py
python tools/check_revI_config.py
FILO_QT_PLATFORM=cocoa python3 tools/freecad/run_macos.py tools/freecad/build_revI.py
FILO_QT_PLATFORM=cocoa python3 tools/freecad/run_macos.py tools/freecad/check_revI_service.py
FILO_QT_PLATFORM=cocoa python3 tools/freecad/run_macos.py tools/freecad/check_revI.py
FILO_QT_PLATFORM=cocoa python3 tools/freecad/run_macos.py tools/freecad/check_finishes.py
python tools/render_revI.py
python tools/render_frames.py
python tools/build_viewer_revI.py
node viewer/build.mjs
python tools/check_viewer_revI.py
python3 tools/check_layout.py
node viewer/check.cjs
python3 tools/check_parts_links.py
python3 tools/check_revI_delivery.py
```

For a fresh PCB reconstruction, run `python3 tools/build_revI_pcb.py` only when `hardware/revI/` does not exist. Run KiCad CLI DRC for both boards with JSON outputs at `build/revI/drc-left.json` and `drc-right.json`, then run `tools/check_revI_pcb.py` with KiCad Python. It checks the explicitly allowed footprint changes, preserved keys/nets and exact new outline, and writes the actual pad polygons. Then run `python tools/check_revI_outline.py` to measure every pad-to-edge clearance. Run these PCB checks before the final delivery check.

The macOS helper uses an existing FreeCAD installation. It disables optional `flatmesh` only in its subprocess because that installed extension crashes on import; it does not modify application preferences. Cocoa is used because that runtime’s offscreen Qt backend failed on mesh recompute. On other systems, run the scripts through the equivalent installed FreeCAD Python environment.

After an authorized publication, `python3 tools/check_public_delivery.py COMMIT_SHA` checks an anonymous full source ZIP against every Git blob and compares public Pages with that commit. Its ZIP and receipt are reproducible under `build/revI/`; it does not publish anything.

The browser check needs Playwright and a Chromium-compatible browser. Set `FILO36_PLAYWRIGHT_MODULE` and `FILO36_BROWSER` if they are not on the usual path. It tests the generated file with HTTP(S) requests blocked; `FILO36_VIEWER_URL` instead selects the published URL.

The native configuration test also uses the scoped subprocess exit after its assertions, file writes and save/reopen readback to avoid the same Qt teardown crash. It does not suppress failed assertions or change installed FreeCAD.

The catalog build verifies SHA-256 and Git blob hashes of every pinned upstream STL. The geometry exporter checks closed printable solids, pair intersections, both cell variants and all six cover variants against components and a nominal USB plug corridor. The separate keycap checker includes complete-configuration envelopes and a travel/plate bound. The service checker samples frame lift, checks closed insert capture, cage capture and the cell-motion bound against lead paths. These tests do not measure force or print tolerances. Source hashes and results are under `validation/revI-*`.

`build/` is ignored and reproducible: native save/reopen trials come from `check_revI.py`; screenshots, test GLB/JSON and UI receipts from `viewer/check.cjs`; the viewer scene from `build_viewer_revI.py`. Source generations should be compared geometrically because STEP/FCStd metadata may vary. DRC JSON and pad polygons regenerate with the PCB checks above; service coupons regenerate with `check_revI_service.py`. Temporary failed drafts were removed. `viewer/performance.cjs` regenerates the current interaction timing receipt under `build/viewer-sidebar/`; `viewer/finishes-check.cjs` checks triangle/material identity. The native finish checker saves its current readback under `build/viewer-multicolor/freecad.json`.

## PCB exchange

RevI updates the board contour, battery opening and magnetic-station cutouts. `tools/build_revI_pcb.py` copies the historical unrouted source and refuses to overwrite existing work. Readback permits only H3/H4/H5, J1 and SW1 to move; it checks preserved pad/net/drill/UUID/model data and all 36 locked keys. The verified StepUp procedure and coordinate alignment are described in [the editing guide](freecad.md#3-inspect-the-pcb-with-stepup). To rerun the historical exchange test on temporary copies:

```sh
FILO_QT_PLATFORM=cocoa python3 tools/freecad/run_macos.py tools/freecad/check_stepup.py
```

Then run `tools/check_stepup_readback.py` with KiCad’s Python. The StepUp harness exits its own GUI subprocess after saving because that runtime crashes during Qt teardown; independent KiCad readback is required. The test must change only the example opening edge, without altering key positions, pads, connectivity or the outer contour.

`tools/sync_pcb_study.py` resets reference placement; it is not an automatic synchronizer for hand-edited designs. Never use it to discard routing. The current contour/DRC receipt is [revI-electrical.json](../validation/revI-electrical.json); the full schematic/netlist validation is retained as historical [revF-electrical.json](../validation/revF-electrical.json).

## Remaining hardware work

The battery opening now leaves approximately **0.524 mm minimum measured pad clearance**, above the configured 0.5 mm rule. Both boards have **zero geometric DRC violations and 104 unconnected items each**. They remain unrouted; do not order them as finished PCBs.

Exact cable terminals, sockets/contact lengths, magnetic retention, printed fits, keycap insertion, screw access with real tools, RF, charging and consumption still need verification. [Revision review](revI-review.md).
