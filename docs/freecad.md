# Design with free tools

**KiCad for the circuit. FreeCAD for the case. StepUp to bring them together.**

## Start here

1. Download the [complete repository ZIP](https://github.com/eduarbo/filo36/archive/refs/heads/main.zip) and unzip it.
2. Install [FreeCAD](https://www.freecad.org/downloads.php) and [KiCad](https://www.kicad.org/download/).
3. In FreeCAD’s Addon Manager, install [KiCad StepUp](https://github.com/easyw/kicadStepUpMod).
4. Open [`mechanical/revG/Filo36.FCStd`](../mechanical/revG/Filo36.FCStd). Importing STEP instead loses the editable history.

The source opens and recomputes without StepUp, CadQuery or custom Python proxies. StepUp is only needed for exchange with KiCad. KLP keycaps are meshes; commercial components are approximate envelopes.

## Navigate the assembly

The tree contains **Parameters**, **Left** and **Right**. Select a part and press **Space** to hide or show it. Expand **Construction** for sketches and operations. Each half has an **ActiveFrame** link to one of three cover bodies; hidden alternatives do not represent extra installed parts.

For keycaps, frame styles and colors, use the [configurator and companion macro](customize.md#save-a-configuration-for-freecad). Keep a personal copy with **File → Save As** before editing dimensions.

## Three editing examples

### 1. Change the cover

In **Parameters**, change `FrameTop` from **16.6 to 17.2 mm** and recompute. All cover styles extend to the new top height. Save, close and reopen to confirm the change, then restore 16.6 mm.

`FrameRoof` controls roof thickness and `WindowMargin` the clearance around the glass. Start from 1.2 and 0.4 mm respectively. The supplied dimensions were checked as a nominal assembly; arbitrary edits are not automatically cleared for fit or printing. For new frame shapes, edit the upper loft sections while preserving the shared cavity and mounts.

### 2. Move the display

Hide the active frame and keycaps. Change `DisplayShiftY` from **2.4 to 3.4 mm**. The complete display, sled and window move together; do not drag the glass alone. Restore 2.4 mm before comparison with the published PCB.

`MCUShiftY`, `MCUBottom`, `BatteryShiftY`, `BatteryBottom` and plate dimensions provide other study controls. **Moving a part in FreeCAD does not update KiCad footprints or traces.**

### 3. Inspect the PCB with StepUp

Open `hardware/revF/filo36-left.kicad_pro` in KiCad. RevG keeps these PCB studies unchanged. Switches are locked to preserve the layout; both boards remain unrouted.

In StepUp, enable **Virtual models**, keep **Grid Origin**, include holes from **0 mm**, and apply no outline tolerance. The boards’ grid origin is explicitly **(10, 10) mm**. In a new FreeCAD document, use **Load KiCad PCB**.

Work on a copy for **Pull Sketch from PCB** / **Push Sketch to PCB**. The tested example moves only the battery opening’s rear edge from KiCad **Y 46.95 to 47.45 mm**, along with its two connecting segments. Reopen the copy in KiCad and verify that switch centers, angles, pads, connectivity and the outer contour are unchanged. This demonstrates exchange, not an approved battery-opening improvement.

The native assembly uses **X = KiCad X, Y = −KiCad Y**, with PCB top at **Z 5.4 mm**. To overlay a StepUp import for inspection, move its complete group by **X +10, Y −10, Z +5.4 mm**. Preserve the original import for pushing back. The right half’s **161 mm X separation** in the assembly is visual only and must never be written to its PCB.

## Export the right file

| Format | Use |
|---|---|
| FCStd | Editable mechanical source and assembly history |
| KiCad project / schematic / PCB | Editable circuit, layout and routing |
| STEP | Solid geometry for other CAD tools; no full feature history or KLP meshes |
| STL | Individual part for slicing; check orientation and fit first |
| GLB from the viewer | Visual assembly with selected keycaps and frames, in meters |
| Configuration JSON | Keycap variants/rotations and frame styles/colors; not manual shape edits |

Select a part and use **File → Export**. Store exports outside the reference folders and keep the edited FCStd. The generation scripts rebuild the reference from scratch and overwrite its files; do not run them over manual work.

The project remains a digital prototype. Cable routing, contact geometry, retainer fastening, printed tolerances, RF and power measurements are unresolved. The battery opening leaves only **0.22 mm nominal pad clearance**, failing the current **0.5 mm** copper-edge rule. [CAD reproduction and validation](cad.md).
