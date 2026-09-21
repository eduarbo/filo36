# Créditos y licencias

Filo36 es un proyecto derivado, desarrollado por Eduardo Ruiz. Su identidad, carcasa y electrónica inalámbrica se desarrollan aquí; la distribución de teclas procede de Piantor. No implica afiliación o certificación por beekeeb ni por los fabricantes de componentes.

| Material | Autor y fuente | Licencia y cambios |
|---|---|---|
| `sources/piantor/*.kicad_pcb` | beekeeb / Leo, [Piantor](https://github.com/beekeeb/piantor), commit `cd847afb4f9a86e8c1c8e36f243140644013afb2` | GPL-3.0; copias originales sin cambios |
| Footprints Choc `keyswitches:Kailh_socket_PG1350_optional` | daprice, [keyswitches.pretty](https://github.com/daprice/keyswitches.pretty) | CC-BY-SA-4.0; aviso conservado en `LICENSES/Keyswitches.md` |
| Footprint `Keebio-Parts:TRRS-PJ-320A` | [Keebio](https://github.com/keebio/Keebio-Parts.pretty), commit `063565dcba9a8ee807d49772de0ed75ecaedcc26` | MIT; copyright y permiso completos en [LICENSES/Keebio-MIT.txt](LICENSES/Keebio-MIT.txt) |
| Footprint `RPi_Pico:RPi_Pico_SMD_TH` | [TPCWare / Nicola Carandini](https://github.com/ncarandini/KiCad-RP-Pico), commit `dc6f9b9f213dc36eebce626aa9ee72a333fa0db3` | [TPCWare KiCad Library License](LICENSES/TPCWare-KiCad.txt), CC-BY-SA-4.0 con excepción para diseños; no impone relicenciar la PCB |
| Footprint estándar `Resistor_SMD:R_1206_3216Metric_Pad1.30x1.75mm_HandSolder` | [Bibliotecas KiCad](https://www.kicad.org/libraries/license/) | [CC-BY-SA-4.0 con excepción para diseños](LICENSES/KiCad-Libraries.md) |
| `design/layout.json` y `docs/images/layout.svg` | Derivados de las coordenadas de Piantor | GPL-3.0; se elimina la columna exterior de cada mitad y se traslada el origen, sin cambiar centros relativos ni ángulos |
| `docs/images/revE-*.png` y `keycaps/*.stl` | Render del prototipo derivado; keycaps [KLP Lamé de braindefender](https://github.com/braindefender/KLP-Lame-Keycaps), commit `4a67a824232d3054c61599ea047c56a340faaba2` | CC-BY-SA-4.0; mallas Choc Stem + Choc Size sin modificar, dispuestas y coloreadas en los renders. Hashes y rutas originales en [keycaps/sources.json](keycaps/sources.json) |
| CAD derivado, herramientas y documentación propias | Eduardo Ruiz / colaboradores de Filo36 | GPL-3.0-or-later, salvo los materiales identificados arriba |
| Motor 3D incluido en `docs/index.html` | [Three.js](https://github.com/mrdoob/three.js), versión 0.180.0 | MIT; aviso completo en [LICENSES/Three-MIT.txt](LICENSES/Three-MIT.txt) y dentro del HTML descargable |

El visor incorpora las mallas Piantor derivadas y KLP Lamé con las mismas licencias indicadas arriba. El HTML contiene los avisos completos y la exportación GLB conserva créditos y enlaces a fuentes/licencias en sus metadatos. El código propio del visor está en `viewer/`, bajo GPL-3.0-or-later; esbuild es una herramienta de compilación fijada en el lockfile.

El texto GPL está en [LICENSE](LICENSE); CC-BY-SA-4.0 está en [LICENSES/CC-BY-SA-4.0.txt](LICENSES/CC-BY-SA-4.0.txt). Los hashes de las fuentes originales figuran en [sources/manifest.json](sources/manifest.json).

ZMK, Zephyr, nice!nano y nice!view se mencionan como dependencias o componentes, con sus nombres y licencias propios. Esta primera publicación no distribuye sus binarios ni código. Los enlaces a fabricantes no indican patrocinio.
