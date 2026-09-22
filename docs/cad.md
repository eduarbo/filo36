# CAD editable y archivos 3D

**[Guía FreeCAD + KiCad + StepUp](freecad.md)** · **[Visor 3D](https://eduarbo.github.io/filo36/)**

La fuente mecánica actual es [`mechanical/revF/Filo36.FCStd`](../mechanical/revF/Filo36.FCStd).
Contiene ambas mitades, parámetros, croquis y operaciones nativas; también las
36 keycaps KLP Lamé como mallas y componentes comerciales como referencias nominales.
No necesita CadQuery ni un módulo Python propio para reabrir y recalcular.

| Medida nominal | revE | revF |
|---|---:|---:|
| Altura de cubierta/marco | 19 mm | 16,6 mm |
| Altura del vidrio de pantalla | 18,3 mm | 16,1 mm |
| Altura hasta el plate | 7,6 mm | 7,6 mm |
| Bahía electrónica | 24 mm | 24 mm |
| Ancho máximo de carcasa por mitad | ≈126,2 mm | ≈126,2 mm |
| Fondo máximo de carcasa | ≈97,7 mm | ≈94,5 mm |
| Saliente electrónico norte sobre tecla vecina | 13,9 mm | 0 mm nominales |

El ancho total sigue condicionado por el pulgar. Las alturas excluyen las patas
ilustrativas de 1,2 mm. El USB es el elemento electrónico más al norte en revF:
queda sólo **0,045 mm detrás** del borde nominal de la tecla vecina; esa alineación
no tiene aún margen de tolerancia física. No equivale a una holgura entre piezas.

## Archivos

- `mechanical/revF/Filo36.FCStd`: conjunto completo editable.
- `mechanical/revF/*-assembly.step`: sólidos por mitad para otros CAD; no incluyen las mallas KLP.
- `mechanical/revF/*.step` y `*.stl`: piezas del estudio y envolventes identificadas.
- `hardware/revF/`: dos proyectos KiCad, esquemáticos y PCB **sin rutas**; bibliotecas y modelos locales.
- `docs/images/revF-*.png`: vistas calculadas desde las mallas exportadas.
- Visor: descarga HTML offline o GLB con keycaps y objetos separados.

Las piezas mantienen coordenadas de montaje. La orientación, tolerancias, soporte
y parámetros del laminador no están validados para impresión.

## Reproducir la referencia

Para editar normalmente, guarda el FCStd. Los siguientes comandos son para
reconstruir la referencia desde cero; **sobrescriben los artefactos revF** y no
deben ejecutarse sobre cambios manuales que quieras conservar.

Entorno comprobado: FreeCAD 1.1.3, KiCad 10.0.6 y StepUp 13.1.7 (metadatos del complemento: 11.09.6) en macOS arm64.
El helper usa las aplicaciones ya instaladas; no instala dependencias ni cambia
preferencias permanentes. La versión Mac usa una ventana Cocoa para la API GUI;
el backend Qt offscreen de esa instalación falló al recomputar mallas. El helper
omite la extensión opcional de desplegado `flatmesh` sólo en su propio proceso:
ese módulo produjo un fallo al importarse desde el Python empaquetado de FreeCAD.

```sh
FILO_QT_PLATFORM=cocoa python3 tools/freecad/run_macos.py tools/freecad/build_native.py
FILO_QT_PLATFORM=cocoa python3 tools/freecad/run_macos.py tools/freecad/check_native.py
```

`build_native.py` usa `design/revF-profiles.json`, los taladros y el layout. El
exportador verifica sólidos, mallas cerradas e intersecciones nominales. El
comprobador abre una copia, cambia altura y posición de pantalla, guarda, reabre
y restaura; también exporta envolventes STEP locales para los footprints.

`tools/sync_pcb_study.py` es un reinicio explícito de la colocación: no es un
sincronizador de tus cambios manuales. Se niega a eliminar rutas existentes sin
un argumento explícito. El trabajo cotidiano entre aplicaciones usa StepUp sobre
copias y comparación posterior de centros, ángulos, contornos y taladros.

Para renders y visor, instala `tools/requirements-render.txt` en un entorno Python
propio y usa Node con `npm ci --prefix viewer`:

```sh
python tools/render_revF.py
python tools/build_viewer_revF.py
node viewer/build.mjs
python tools/check_viewer_revF.py
python tools/check_revF.py
node viewer/check.cjs
```

Las capturas y pruebas temporales se escriben en `build/`, ignorado por Git.
Los recibos de `validation/revF-*` vinculan fuentes y resultados. Una regeneración
puede variar metadatos STEP/FCStd; las comparaciones deben incluir geometría.

## Límites del estudio

La abertura deja 0,15 mm alrededor de la cuna y 0,22 mm nominales hasta pads del
micro: incumple la regla actual de cobre a borde de **0,5 mm**. Falta resolver tolerancias de fresado, margen de cobre, cables, contactos,
fijación del retenedor, resistencia y extracción física. La electrónica no tiene
aceptación de funcionamiento ni de fabricación.

RevE permanece en `mechanical/revE/`, `design/revE.json` y sus cuatro imágenes.
Su fuente histórica sigue siendo CadQuery (`tools/build_case.py`); no es la
revisión editable recomendada ni corresponde al PCB revF.

Para comprobar el intercambio real (sólo modifica copias bajo `build/`):

```sh
FILO_QT_PLATFORM=cocoa python3 tools/freecad/run_macos.py tools/freecad/check_stepup.py
```

El harness de StepUp evita la finalización de Qt únicamente al salir de su
subproceso: esa combinación falla al destruir la GUI después de guardar. Todos
los archivos se cierran antes; la aceptación exige el readback independiente en
KiCad, no sólo el código de salida. FreeCAD instalado no se modifica.

La prueba usa el cargador de PCB normal de StepUp, incluye los modelos virtuales
y compara los sólidos tras alinear el origen. Para booleanas entre contornos
redondeados por KiCad se emplea tolerancia numérica de 0,00001 mm. El readback
en KiCad debe confirmar el cambio de 0,5 mm del ejemplo y ningún cambio de
footprints, pads, conexiones, taladros ni contorno exterior.

En macOS, el readback y la comprobación eléctrica usan el Python de KiCad:

```sh
KCLI=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
KPY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
for side in left right; do
  "$KCLI" sch export netlist --format kicadxml -o "build/$side-netlist.xml" "hardware/revF/filo36-$side.kicad_sch"
  "$KCLI" sch erc --format json -o "build/erc-$side.json" "hardware/revF/filo36-$side.kicad_sch"
  "$KCLI" pcb drc --format json -o "build/drc-$side.json" "hardware/revF/filo36-$side.kicad_pcb"
done
"$KPY" tools/check_pcb_study.py
"$KPY" tools/check_stepup_readback.py
```

El DRC **debe seguir mostrando los pendientes documentados** hasta corregirlos;
que los archivos y el intercambio sean válidos no significa que el circuito esté
terminado. En otros sistemas, usa los ejecutables de tu instalación equivalente.
