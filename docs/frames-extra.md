# Creative frames

Cartridge, Arcade, Mecha and Kintsugi add printable relief to the Smooth frame.
Choose a thumbnail in the [viewer](https://eduarbo.github.io/flan36/), customize
its colors and export your configuration or print kit. See [customization](customize.md)
for the complete workflow.

| Frame | Design | Default palette |
| --- | --- | --- |
| Cartridge | Grip ribs, label plate and contact fingers | Saffron, violet, pale gold, coral |
| Arcade | Stepped marquee, side lights, joystick and three buttons | Midnight, violet, pink, yellow |
| Mecha | Angular armor, hazard bars and reactor | Ivory, slate, orange, cyan |
| Kintsugi | Porcelain islands and raised repair lines | Blue, porcelain, gold, celadon |

The controls are decorative. Each design is one fused solid, with color regions
on its actual faces. STL carries geometry only; assign materials or paint regions
in your slicer. See [themes and printing](themes-printing.md).

## Fit and printing

- Relief rises at most **0.6 mm** above the Smooth roof without widening its footprint.
- The screen opening, service cutouts, underside and mounting interfaces are inherited
  from Smooth. These designs do not lower the electronics stack or change the mounts.
- Some details are **0.45 mm** wide. Inspect the sliced toolpaths before printing.
- Digital validation checks connected solids, closed meshes, preserved interfaces
  and service clearances. **Printed fit remains unqualified; these are prototypes.**

## Edit in FreeCAD

Open [Flan36.FCStd](../mechanical/revI/Flan36.FCStd) and expand `L_ExtraFrames` or
`R_ExtraFrames`. The boxes, cylinders, sketches and Boolean features are native
editable objects; the saved file needs no custom Python classes. Save a copy before
editing. Relief heights follow `Parameters.FrameTop`.

For repeatable changes, edit the [shared recipes](../design/frame-extensions.json)
and regenerate a separate candidate. From the repository root on macOS with
FreeCAD installed:

```sh
frame_dir="$(mktemp -d /tmp/flan36-frames.XXXXXX)"
python3 tools/freecad/run_macos.py tools/freecad/install_extra_frames.py \
  --source mechanical/revI/Flan36.FCStd \
  --output "$frame_dir/Flan36-extra.FCStd" \
  --report "$frame_dir/frame-report.json"
```

The installer refreshes only its four extension designs per half, preserving the
original geometry, appearance and active configuration. It saves and reopens the
candidate before accepting it, using offscreen GUI support to retain face colors.
Review the report and candidate before adopting changes; the source file above is
left untouched. Regenerating recipes replaces edits to extension-owned features.
