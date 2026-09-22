# Colaborar

Ideas, dudas y resultados de pruebas son bienvenidos en Issues.

Para reportar un problema, incluye revisión, pieza afectada, comportamiento esperado y observado. Si es mecánico, añade medidas y parámetros de impresión. Si es firmware, indica micro, versión y pasos para repetirlo.

Las contribuciones deben conservar los centros y ángulos del layout de 36 teclas, salvo que propongan explícitamente otra variante. Separa medidas reales de estimaciones y de renders.

Mantén la documentación breve: qué cambia, por qué y cómo se comprobó. Conserva la procedencia y licencia de cualquier archivo externo. No presentes archivos experimentales como listos para fabricar.

Usamos [FreeCAD + KiCad + StepUp](docs/freecad.md). Guarda las modificaciones
mecánicas en una copia del FCStd y adjunta el archivo editable y sus cotas; un
STL o render solo no conserva el diseño. Trabaja sobre una copia de PCB al probar
StepUp y verifica centros, ángulos, contorno, taladros y DRC después del intercambio.
No ejecutes el generador inicial sobre un FCStd editado a mano.
