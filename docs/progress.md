# Progress

**Current mechanical revision: H. Overall keyboard: partial digital prototype.**

| Outcome | State | Evidence / next step |
|---|---|---|
| 36 Piantor key centers and angles | Checked | [Layout](../design/layout.json), upstream files and checker |
| Editable source and CAD exchange | Available | Native FCStd, parameters and [FreeCAD/StepUp examples](freecad.md) |
| KLP catalog and themed frames | RevH digital study | 38 source variants, 28 with qualified positions; six frame styles, configuration export/import |
| Wireless electronics and displays | Placement only | Unrouted revH PCBs; unresolved DRC and connector dimensions |
| Final BOM and manufacturing files | Pending | Close routing, clearances, retention and exact supplied parts |
| Printing and assembly | Pending | Fit coupon, sample caps and actual component measurements |
| Working keyboard | Pending | All keys, BLE, charging, sleep/wake and measured consumption |

## Multicolor frame previews

Handheld, Retro TV and Cyberpunk now use distinct body, detail and accent colors on the existing raised faces. Larger upright previews show the corresponding meshes and palettes; one click applies both. Body-color overrides remain independent per half and survive JSON export/import. The shared palette also drives the GLB materials, FreeCAD configuration import and frame comparison image.

The former thumbnails referenced different STL files, but used one green material and a distant oblique view. Their distinct-image test did not establish readable design details. Current checks identify actual left/right raised features, preserve every original vertex/normal/triangle and verify the exported material colors. Geometry and manufacturing status remain unchanged.

Verified on the public viewer, including mobile emulation, JSON and GLB; all 579 published source files matched the tested commit. FreeCAD applied four colors per native theme/half and preserved them through save/reopen. The 4× CPU benchmark retained a 16.7 ms orbit p95 and 57.5 ms theme-change p95.

[Color and print guide](customize.md#print-a-themed-display-frame) · [Checks](../validation/viewer-multicolor.json) · [Public readback](../validation/viewer-multicolor-publication.json) · [Correction scope](../design/viewer-multicolor-workflow.json).

## Persistent component sidebar

All 12 component entries remain visible while their details scroll or collapse. Hover, focus or select a part to highlight it; the connecting line ends at its own sidebar entry. Frame previews still apply in one click. Desktop, 390 px and 320 px touch layouts, short landscape, configuration and exact GLB export passed local and public checks.

The previous floating-tag iteration passed functional tests but missed the intended sidebar relationship and had no latency acceptance. Its anchor search could run up to 192 full-scene intersection queries per camera update. Surface searching now pauses during gestures and resolves only the active component afterward; rendering is coalesced and highlights are reused.

On the same Chromium 152 setup at 1200 × 800 with 4× CPU throttling, **p95 orbit frame interval fell from 1,616.5 to 16.8 ms**, with 59 long tasks reduced to zero. **Frame-change p95 fell from 1,692.4 to 59.0 ms**. These are local benchmark results; physical-phone performance remains untested.

[Usage guide](viewer.md) · [Checks and measurements](../validation/viewer-sidebar.json) · [Public readback](../validation/viewer-sidebar-publication.json), including all 571 source-commit files · [Correction scope](../design/viewer-sidebar-workflow.json). Historical acceptance of the first visual explorer remains in its [original receipt](../validation/viewer-ux-publication.json).

## Revision H — continuous edge and printable themes

The user’s red-line reference replaces the old display notch and thumb wing with one straight inner case flank. The case is approximately **8.1 mm narrower**, keeping every switch center and angle. Sixteen intentional corners use a common **1.2 mm radius**.

Handheld, Retro TV and Cyberpunk add actual roof relief within the same bay. Plain styles remain available. The high cover ends before the thumb; base and plate continue the aligned edge. Both KiCad contours match the new CAD reference without moving footprints or changing nets. There are still **26 DRC violations and 104 unconnected items per half**.

Publication verified: all **561 source files** matched the anonymous archive. Public HTML and the browser-loaded scene matched the tested source; layers, orbit, all three themes, JSON, selected GLB geometry and narrow-screen emulation passed. Actual phone and hardware tests remain pending. [Publication receipt](../validation/revH-publication.json).

[Revision review](revH-review.md) · [Keycap checks](../validation/revH-keycaps.json) · [Mechanical checks](../validation/revH-mechanical.json).

## Revision G — keycaps and frames

Opaque covers replace revF’s side rails. The separate display sled stays in place. Smooth, beveled and faceted styles share the same mounting centers, inner cavity and service openings. Bay width and top height remain 24 and 16.6 mm.

The viewer selects KLP variants by position/orientation, checks complete combinations and writes a JSON configuration used by the FreeCAD macro. GLB exports carry the active configuration. The cap check is separate from solid-part collision checks, which did not include KLP meshes in revF.

Documentation, current CAD labels, viewer and new render captions are in English. The [parts guide](parts.md) separates references from alternatives and adds technical links, supplier photos and Typeractive pack quantities. Conflicting part numbers and missing exact datasheets are kept visible.

Publication verified: an anonymous archive matched all **404 files** of the design commit; public viewer bytes matched the tested source. Keycap/frame selection, JSON round trip, exact selected GLB vertices, layers, rotation and narrow-screen behavior passed on the public URL. [Publication receipt](../validation/revG-publication.json).

[Review and limits](revG-review.md) · [Keycap checks](../validation/revG-keycaps.json) · [Mechanical checks](../validation/revG-mechanical.json).

## Earlier revisions

- **RevD:** wide side-by-side electronics and one display; visual direction discarded. The render survives only in Git history.
- **RevE:** 24 mm stacked bay, two displays and a 19 mm cover. CAD-derived images replaced the stale revD render.
- **RevF:** recessed battery opening, moved controller/display and 16.6 mm open rails. Native FreeCAD source added. Approximate case depth became 94.5 mm; width remained 126.2 mm because the thumb layout stayed unchanged.

RevF’s CAD/StepUp exchange, anonymous source download and public viewer were checked; physical acceptance was not. [Historical review](revF-review.md) · [publication receipt](../validation/revF-publication.json).

Filo36 remains a provisional name; Sesgo36 and Brizna36 were earlier candidates. Changing the project’s presentation does not retire unfinished electrical or physical requirements.
