# Progreso

**En curso: revisión F — CAD editable, batería rebajada y marco abierto.**

| Hito | Estado | Evidencia / siguiente paso |
|---|---|---|
| Layout de 36 teclas | Comprobado | [Coordenadas](../design/layout.json), fuentes y comprobador incluidos |
| Prototipo anterior, revisión D | Antecedente digital | Una pantalla izquierda y batería lateral; forma descartada |
| Carcasa y stack revF | Estudio editable | Marco 16,6 mm; plate 7,6 mm; sin saliente norte nominal. Cables, tolerancias y retención pendientes |
| Dos pantallas y electrónica modular | Colocación KiCad publicada | Ambas placas sin ruteo; ERC sin incidencias, DRC pendiente. Una pantalla sigue siendo alternativa |
| BOM y archivos para fabricar | Pendiente | Cerrar la revisión modular y publicar fuentes coherentes |
| Impresión y montaje | Pendiente | Cupón Choc, tres keycaps y comprobación de piezas reales |
| Teclado funcionando | Pendiente | 36 teclas, BLE, carga, sueño/despertar y consumo medido |

## 2026-09-21 · Inicio público

Se comparte el layout, la dirección del diseño y la lista de componentes prevista. El trabajo previo pasó de 42 a 36 teclas, recuperó el contorno angular e integró una pantalla. La revisión siguiente busca una bahía más estrecha y acceso independiente a la electrónica.

Filo36 es el nombre provisional; también se consideran Sesgo36 y Brizna36.

## Corrección visual

La carcasa ancha de revD fue descartada. Su render permanece únicamente en el historial del repositorio; no representa la dirección actual. El nuevo CAD revE usa una bahía de 24 mm, dos pantallas sobre los micros y tapa electrónica independiente. La portada y las vistas de detalle se generan desde sus piezas STEP/STL. Se comprobó que las envolventes modeladas no invaden la carcasa ni se solapan entre sí; el cable de batería aún debe resolverse.

La bahía es **28,4% más estrecha**. El ancho máximo de cada mitad queda aproximadamente en 126,2 mm: el pulgar conserva su posición y sigue determinando buena parte de ese máximo. El stack aumenta la altura local de electrónica de 16 mm en la revD izquierda a 19 mm; el plate permanece a 7,6 mm.

## Inspección 3D

Se añade un [visor interactivo por capas](viewer.md), con rotación completa, mitades seleccionables, vistas ortográficas y separación reversible de piezas. El visor actual usa las mallas revF, vinculadas a su CAD. La guía explica las cotas y cómo editarlas; la aceptación física sigue pendiente.

## Revisión F · Edición manual

El [flujo FreeCAD + KiCad + StepUp](freecad.md) es ahora la base del proyecto.
El FCStd conserva croquis, operaciones, parámetros y piezas separadas; las
keycaps están incorporadas. Se comprobó cambiar altura y posición de pantalla,
guardar, cerrar, reabrir y restaurar el diseño.

La batería baja dentro de una abertura real del PCB. El micro se acerca a los
pulgares y la pantalla lo acompaña: el stack completo queda detrás del borde
norte de la keycap vecina en el modelo nominal. El marco pasa de 19 a 16,6 mm,
con laterales abiertos. El ancho máximo sigue en 126,2 mm; la profundidad baja
a unos 94,5 mm. Se conservan las 36 posiciones y ángulos originales.

Esta propuesta **no está lista para fabricar**. La abertura queda a 0,22 mm de
24 pads del micro por mitad frente a la regla actual de 0,5 mm; también quedan
un pad próximo al borde, courtyards y serigrafía por corregir. Ambas placas tienen
104 conexiones sin rutear. No se redujeron reglas ni se ocultaron incidencias.
El cable, la fijación del retenedor, los contactos y las tolerancias necesitan
trabajo antes del primer montaje.
