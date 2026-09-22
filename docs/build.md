# Build status

The current design is an inspectable digital prototype. Final Gerbers, a closed BOM and tested UF2 firmware are not available yet. Do not order the unrouted PCB studies as finished boards.

The intended sequence is:

1. Close the BOM and measure the actual components.
2. Print a Choc fit coupon and three KLP Lamé samples. Check stem fit, return and comfort before printing the full set.
3. After electrical layout passes review and DRC, assemble the PCBs and check continuity and polarity.
4. Flash each half and test all 36 keys.
5. Install the supported battery, controller, display and frames without loading the pouch or glass.
6. Verify BLE, charging, sleep/wake and measured power use.

PLA Basic and PETG HF are available for prototype trials; ABS is another case material. No filament/profile is qualified for the final parts yet. Print orientation and stem tolerances need physical tests. [Parts and alternatives](parts.md).

## Inspect the layout now

`design/layout.json` contains each half’s 18 key centers and angles in millimeters. The original Piantor boards and provenance are under `sources/` and [ATTRIBUTION.md](../ATTRIBUTION.md).

```sh
python3 tools/check_layout.py
python3 tools/render_layout.py
```

The checker compares all 36 positions/rotations with the original boards. The renderer regenerates the layout diagram. `sources/piantor/` contains the original **wired** reference boards, not Filo36’s wireless PCB designs.
