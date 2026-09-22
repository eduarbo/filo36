# Revisión del estudio editable

**Alcance:** CAD editable y visualización revF. No aprobación de fabricación.
Dos revisiones independientes examinaron geometría, flujo CAD/ECAD y riesgos;
una segunda ronda contrastó la batería rebajada y el marco abierto.

| Hallazgo | Resolución / estado |
|---|---|
| Mover el micro sin bajar la batería cruza el USB con la celda | Se rebaja la cuna dentro de una abertura real del PCB; separación nominal celda/USB 1,4 mm |
| Pantalla, header, JST y apoyos pueden cruzarse al alinearlos | Soportes reconstruidos desde el PCB; JST, reset e interruptor recolocados; sin intersecciones entre sólidos modelados |
| Importar STEP no entrega una carcasa paramétrica | FCStd con croquis, operaciones y tabla de parámetros; edición, guardado y reapertura probados |
| Márgenes pequeños de abertura y cobre | 0,15 mm cuna/abertura; 0,22 mm pad/borde. DRC detecta incumplimiento de la regla de 0,5 mm. Se conserva y publica como pendiente |
| No confundir marco corto con menor ancho total | Ancho máximo ≈126,2 mm; profundidad ≈94,5 mm; marco 16,6 mm |
| Saliente cero sin margen de tolerancias | USB sólo 0,045 mm detrás de la keycap vecina en planta; alineación nominal, no garantía física |
| Retenedor y piezas extraíbles sin prueba de servicio | Fijación, cable, recorridos de extracción y encaje siguen pendientes |

Las recomendaciones coincidieron en permitir el estudio local y su publicación
con evidencia digital y límites explícitos. Las objeciones de fabricación no
quedan resueltas por la publicación. Las revisiones fueron de lectura; los ocho
archivos del baseline se conservaron durante ambas rondas antes de las ediciones
atribuibles del autor.

## Corrección y prevención acotada

El conjunto STEP anterior permitía ver piezas, pero no cubría la edición manual
paramétrica que ahora necesita el proyecto. RevF incorpora la fuente FCStd y
comprobaciones de edición y reapertura. Portada, visor y archivos se vinculan por
hashes para detectar una representación antigua. La PCB y el CAD se comparan
mediante importación real, sin convertir un DRC fallido en aprobación de hardware.
