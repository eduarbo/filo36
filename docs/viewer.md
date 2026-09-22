# Explore the assembly

**[Open the 3D viewer →](https://eduarbo.github.io/filo36/)**

The component directory stays visible while you inspect or customize the keyboard. Its 12 entries include **Frame**, **Caps**, **PCB**, **Battery** and **MCU**. Open an entry for its controls or information; use its eye to show or hide that layer. **View**, **Files** and **About** remain available below the directory, or above it on a phone.

![A component connected directly to its sidebar entry](images/viewer-explorer.png)

## Follow a component

Hover or focus a directory entry to highlight its visible parts. Click or tap to keep the selection. You can also select a part directly in 3D. A fine line connects the active visible part to its exact directory entry; there are no floating tags. Hidden or occluded parts keep their directory entries but do not receive a visible-surface line.

**Frame** opens six actual-mesh previews. Choose a half, then click a thumbnail to apply the shape immediately. Shape changes preserve each half’s color; swatches change the finish. **Caps** opens KLP presets and individual key editing. Other entries explain the component and its current limitations.

The arrow beside the directory collapses only the details. Component names and section controls stay visible, including while the details scroll. The mobile directory uses a compact grid; all entries stay visible while the detail area scrolls and the model stays on screen.

Clear a selection with **×** or **Escape**. **Links** hides the connecting line. During a camera gesture, the line pauses; it reconnects after the gesture settles. Expensive surface searches no longer run during every camera update.

## Move and inspect

Drag to orbit, scroll or pinch to zoom, and use two fingers to pan. **3D**, **Top** and **Front** sit beside the model; **View → Camera** includes the remaining views. **Fit** centers visible parts. **Reset view** restores the assembly and keeps your configuration.

**View** also contains Inside, Stack, half selection and Separate layers. Exploded spacing is a viewing aid; it does not alter saved geometry. Dragging or using two fingers does not select components.

## Keep your choices

Open **Files** for Save configuration, Load JSON, Restore default parts, GLB and offline downloads. JSON transfers selections to another browser or [FreeCAD](customize.md#save-a-configuration-for-freecad). Restoring defaults changes parts; resetting the view does not.

**Download offline HTML** includes geometry, previews, code and licenses. It needs no network requests after download. The file remains about 26 MiB because it contains the original supported meshes; first-load time depends on the device and connection.

**Download assembled GLB** exports all installed parts in their assembled positions, with the selected keycaps, frames and colors. Hidden layers, exploded offsets, lines and highlights do not alter the exported assembly. GLB uses meters and retains attribution; use FreeCAD/STEP for solid editing.

This remains a nominal CAD study. See [dimensions and limitations](cad.md), [customization rules](customize.md) and [parts](parts.md). Browser checks distinguish desktop and emulated touch viewports from physical-phone and hardware acceptance.
