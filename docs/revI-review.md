# Revision I review

**Chosen Contour outline, magnetic frames and two battery profiles. Digital prototype only.**

The source reference requested a stepped finger outline, rectangular pinky foot, shallow recess and continuous thumb fan. The actual CAD and PCB now use that contour while preserving all 36 Piantor key transforms. Internal fasteners and magnetic stations add no perimeter lobes.

Two independent read-only reviews covered geometry/serviceability and failure modes before the magnetic design was adopted. The recorded source snapshots stayed unchanged during their review. [Decision record](../validation/revI-design-review.json).

## Corrections made during verification

- H3 was outside the new recess: it moved into existing material. H4/H5 moved below the electronics, with short screws and underside head reliefs.
- The earlier wide battery opening violated the copper-edge rule: the saddle now stays below the board, with only the cell/cage crossing a 12.5 mm opening.
- An initial magnet position cut a K25 pad: actual pad polygons exposed the conflict. Stations moved south; J1 and SW1 moved to preserve clearance. The power switch also moved inward. No key moved.
- The battery cage touched the controller support: the rear support bridge moved clear of the cage.

Both KiCad studies have **0 geometric violations and 104 unconnected items per half**. This is not a routed-board DRC pass or fabrication release. The original 0.5 mm copper-edge rule remains in force; measured minimum pad clearance is approximately 0.524 mm.

- A frame could fit at rest yet catch the MCU while lifting. Its internal relief now opens to the lower rim; sampled extraction checks cover all six styles.
- A FreeCAD link dropped a battery box's placement. Each battery variant now has a native compound wrapper, and independent bounds checks verify the active link, exported mesh and configuration swap.

## Physical work still open

Magnetic holding force, north-edge peel, closed-pocket print capture, actual magnet temperature, printed M2 threads and cycling need coupons. Both battery fits use supplier nominal dimensions; wrapping, insulation, protection electronics, cable terminals and connector polarity must be checked on delivered parts. Socket heights, hot-swap assembly, firmware, charging, BLE and consumption remain unverified.

The wire study reserves two 105 mm paths with 1.5 mm bends and 0.6 mm insulation diameter. It is not a terminal-complete harness. Sampled frame lifts are nominal collision checks, not a continuous tolerance analysis or a physical extraction test.

[Mechanical](../validation/revI-mechanical.json) · [Outline and clearances](../validation/revI-outline.json) · [Electrical](../validation/revI-electrical.json) · [Service and coupons](../validation/revI-service.json) · [Build sequence](build.md).
