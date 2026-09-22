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

## Revision H — continuous edge and printable themes

The user’s red-line reference replaces the old display notch and thumb wing with one straight inner case flank. The case is approximately **8.1 mm narrower**, keeping every switch center and angle. Sixteen intentional corners use a common **1.2 mm radius**.

Handheld, Retro TV and Cyberpunk add actual roof relief within the same bay. Plain styles remain available. The high cover ends before the thumb; base and plate continue the aligned edge. Both KiCad contours match the new CAD reference without moving footprints or changing nets. There are still **26 DRC violations and 104 unconnected items per half**.

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
