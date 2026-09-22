# Diseña Filo36 con herramientas gratuitas

**KiCad para el circuito. FreeCAD para la carcasa. StepUp para reunirlos.**

Este es el flujo que usamos y promovemos. No necesitas Fusion ni una suscripción.
El conjunto revF es un estudio editable: electrónica nominal y PCB sin ruteo.

## Empieza aquí

1. Descarga el repositorio completo: **Code → Download ZIP** y descomprímelo.
2. Instala [FreeCAD](https://www.freecad.org/downloads.php) y [KiCad](https://www.kicad.org/download/).
3. En FreeCAD, abre el administrador de complementos e instala **KiCad StepUp**;
   reinicia FreeCAD si lo solicita. [Complemento y documentación](https://github.com/easyw/kicadStepUpMod).
4. Abre [`mechanical/revF/Filo36.FCStd`](../mechanical/revF/Filo36.FCStd).
   No importes el STEP si quieres conservar los parámetros de la carcasa.

El FCStd se abre y recomputa sin StepUp, CadQuery ni scripts propios. StepUp se
necesita para intercambiar cambios con KiCad. Las keycaps incluidas son mallas
KLP Lamé; los componentes comerciales son envolventes, no CAD certificado.

## Encuentra las piezas

El árbol contiene **Parámetros**, **Izquierda** y **Derecha**. Dentro de cada mitad
están base, plate, PCB, batería, cuna, retenedor, micro, sockets, pantalla y marco.
Selecciona una pieza y pulsa **Espacio** para mostrarla u ocultarla. Selecciona
ambas mitades y encuadra para recuperar la vista completa.

**Construcción** conserva los croquis y operaciones nativas. Están ocultos para
no tapar el resultado; despliega el historial de una pieza para inspeccionarlos.

## Tres ejemplos para aprender

Trabaja primero con **Archivo → Guardar como**, por ejemplo `Filo36-mi-variante.FCStd`.

### 1. Cambiar una cota

Abre **Parámetros** y cambia `FrameTop` de **16,6 a 17,2 mm**. Recalcula el documento:
los largueros del marco cambian de altura. Guarda, cierra y vuelve a abrir para
comprobar que la modificación permanece. Vuelve a 16,6 mm para restaurarla.

`PlateThickness` cambia el espesor del plate. `MCUShiftY` y `DisplayShiftY` desplazan
los módulos hacia los pulgares; sus soportes y agujeros asociados los acompañan.
Estos controles sirven para estudiar alternativas: un valor editable no implica
que tenga holgura suficiente. Las teclas conservan sus centros y ángulos.

### 2. Probar otra posición de pantalla

Oculta el marco y las keycaps. Cambia `DisplayShiftY` de **2,4 a 3,4 mm**, recalcula
y observa la pantalla junto con su soporte. No arrastres sólo el vidrio: forma
parte de un módulo que incluye placa y componentes inferiores.

Restaura 2,4 mm antes de comparar con la PCB publicada. **Mover el modelo en
FreeCAD no actualiza por sí solo las pistas o los footprints de KiCad.**

### 3. Revisar la placa con StepUp

Abre `hardware/revF/filo36-left.kicad_pro` en KiCad. Los switches están bloqueados
para conservar el layout. La placa incluye la abertura real de batería y los
taladros; las conexiones pendientes aparecen como líneas de conexión.

En las preferencias de **KiCad StepUp**, activa **Virtual models**, conserva
**Grid Origin** como referencia de colocación, usa taladros desde **0 mm** y
no apliques tolerancia al contorno. Los PCB incluyen un origen de rejilla
explícito en **(10, 10) mm**; no lo cambies durante estos ejemplos.

En un documento nuevo de FreeCAD, usa **KiCad StepUp → Load KiCad PCB** y elige
`filo36-left.kicad_pcb`. Trabaja siempre sobre una copia al probar los comandos
**Pull Sketch from PCB** y **Push Sketch to PCB**. StepUp intercambia contornos y
colocaciones, pero no enruta el circuito ni sincroniza todo automáticamente.

Ejemplo probado: selecciona el croquis del PCB importado, edita el borde trasero
de la abertura de batería de **Y KiCad 46,95 a 47,45 mm** y devuelve el croquis con
**Push Sketch to PCB**. Reabre la copia en KiCad: sólo ese borde y los dos segmentos
que lo unen deben cambiar; switches y conexiones deben mantenerse. Es un ejercicio,
no una mejora aprobada de la abertura. No modifiques el contorno exterior en este ejemplo.

El conjunto nativo usa **X = X de KiCad, Y = −Y de KiCad**, PCB superior a
**Z = 5,4 mm**. StepUp coloca respecto al origen de rejilla: para superponer su
importación al conjunto nativo, desplaza el **grupo completo** en
**X +10, Y −10, Z +5,4 mm**. Usa una copia para inspección; conserva la importación
original en su documento para devolver el contorno a KiCad. La mitad
derecha del ensamblaje tiene una separación visual de **161 mm en X** que nunca
debe trasladarse a su PCB.

Antes de aceptar un intercambio, compara los 18 switches de esa mitad, los
ángulos, el contorno exterior, la abertura de batería y el espesor. Los modelos
de componentes viajan con el repositorio mediante `${KIPRJMOD}/models`.

## Qué archivo editar y qué exportar

| Archivo | Uso |
|---|---|
| `.FCStd` | Fuente editable de carcasa, soportes y ensamblaje |
| `.kicad_pro`, `.kicad_sch`, `.kicad_pcb` | Proyecto, circuito y placa editables |
| `.step` | Compartir sólidos y ensamblajes con otros CAD; no conserva todo el historial |
| `.stl` | Llevar una pieza al laminador; revisar orientación y tolerancias |
| `.glb` del visor | Compartir el conjunto visual con piezas separadas; no es CAD paramétrico |

Para exportar manualmente una pieza, selecciónala en el árbol y usa
**Archivo → Exportar**. Guarda tus archivos en otra carpeta para conservar la
referencia publicada. Guarda también tu FCStd: un STL no sustituye la fuente.

## El diseño abierto del stack

RevF estudia una batería rebajada en una abertura del PCB, micro sobre apoyos
independientes y pantalla encima. El marco deja visibles parte de la electrónica
y el USB. La celda conserva cuna aislante y un retenedor propuesto; no recibe
presión del micro. La fijación del retenedor y el cable original siguen pendientes
de prototipo físico.

La abertura deja **0,15 mm por lado** alrededor de la cuna y aproximadamente
**0,22 mm** hasta los pads cercanos del micro. Son márgenes nominales pequeños.
La separación de cobre ya falla la regla actual de **0,5 mm**: hay que ajustar
abertura, pads o arquitectura antes de pedir PCB. El informe también detecta
un pad del interruptor próximo al borde y courtyards superpuestos; ver
[comprobación eléctrica](../validation/revF-electrical.json). La altura de las keycaps sigue siendo ilustrativa.

## Fuentes y reproducción

La construcción inicial está en `tools/freecad/build_native.py`; usa croquis,
extrusiones y booleanas nativas. **No la ejecutes sobre tus cambios manuales:**
regenera la referencia desde cero. Los cambios cotidianos se guardan en el FCStd.
RevE queda conservada para comparar.

Referencias: [StepUp](https://www.kicad.org/external-tools/stepup/),
[parámetros con Spreadsheet](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Spreadsheet_Workbench.md).
