# CAD revE y renders

La revisión E sustituye la carcasa ancha del render anterior. Los archivos actuales son **un estudio mecánico nominal**, para revisar forma y disposición; aún no un kit listo para fabricar.

| Cota del modelo | Valor |
|---|---:|
| Bahía electrónica | 24 mm, antes 33,52 mm |
| Ancho máximo por mitad | ≈126,2 mm |
| Fondo máximo | ≈97,7 mm |
| Altura hasta el plate | 7,6 mm |
| Cubierta electrónica | 19 mm |
| Patas dibujadas | +1,2 mm |

Se conserva el exterior escalonado y los ángulos del layout. El máximo de anchura también depende del pulgar; no equivale al ancho de la bahía.

## Archivos

- [`mechanical/revE/`](../mechanical/revE): STEP/STL de bases, plates, tapas, cunas, separadores y soportes; STEP de conjunto. Las piezas conservan sus coordenadas de montaje, no una orientación validada de impresión.
- [`design/revE.json`](../design/revE.json): cotas, contornos, componentes y hashes de mallas.
- [`validation/revE-mechanical.json`](../validation/revE-mechanical.json): comprobaciones de volúmenes nominales.
- [`validation/revE-render.json`](../validation/revE-render.json): correspondencia de imágenes, CAD y mallas KLP.
- [`keycaps/`](../keycaps): originales KLP Lamé Choc Stem + Choc Size, con su procedencia y licencia.

Las piezas identificadas como batería, MCU, display, sockets, JST, slider, reset y PCB son **envolventes de referencia, no piezas imprimibles ni modelos exactos del fabricante**. Tornillos, patas, cuerpos de switch, contenido de pantalla y altura de asiento de keycaps son ilustrativos.

## Reproducir

Comprobado con Python 3.12.14, CadQuery 2.6.1 y VTK 9.3.1 en macOS arm64. Instalar en un entorno propio, desde la raíz del repo:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r tools/requirements-render.txt
.venv/bin/python tools/check_layout.py
.venv/bin/python tools/build_case.py
.venv/bin/python tools/render_assembled.py
.venv/bin/python tools/check_artifacts.py
```

El generador sobrescribe sólo los archivos revE que produce. Los renders se calculan desde las mallas exportadas; no se retocan ni se estrechan en la imagen. Una regeneración puede cambiar metadatos STEP y bytes según plataforma; verificar geometría y reportes, no prometer igualdad binaria entre entornos.

`check_artifacts.py` detecta imágenes antiguas, cambios en las fuentes del CAD, mallas o renderizador y la restauración accidental de la imagen revD. El generador comprueba que las mallas de piezas prototipo estén cerradas y sin aristas no manifold. Las comprobaciones no sustituyen la prueba física.

## Qué falta

Resolver los 105 mm del cable original de cada batería, confirmar huellas y alturas de conectores, fijación de cuna/soportes, tolerancias y recorrido de extracción. Después integrar PCB ruteada y firmware, imprimir cupones y probar montaje, BLE, carga y consumo. Los reportes nominales no cubren esos puntos.
