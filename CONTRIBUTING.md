# Contributing

Ideas, questions and physical test results are welcome in Issues.

Include the revision, affected part, expected behavior and observed result. For mechanical issues, add measurements and print settings; for firmware, include the controller, version and reproduction steps.

Preserve the 36-key centers and angles unless explicitly proposing a different layout. Distinguish measurements, estimates and renders. Keep documentation in English, concise and focused on what changed, why and how it was checked. Preserve upstream authorship and licenses. Do not label experimental files as manufacturing-ready.

Use [FreeCAD + KiCad + StepUp](docs/freecad.md). Save mechanical work in a copy of the FCStd and include that editable source with its dimensions; STL or a render alone loses the design history. Test StepUp on a PCB copy and compare centers, angles, outlines, holes and DRC afterward. Never run the reference generator over a hand-edited FCStd.

For keycap/frame contributions, include the complete configuration, source hashes and clearance results. A visually plausible combination must also pass the configuration checker. New frame geometry requires a new collision check and updated exported/viewer meshes.
