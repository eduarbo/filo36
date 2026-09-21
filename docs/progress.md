# Progreso

**En curso: revisión E — stack estrecho y módulos extraíbles.**

| Hito | Estado | Evidencia / siguiente paso |
|---|---|---|
| Layout de 36 teclas | Comprobado | [Coordenadas](../design/layout.json), fuentes y comprobador incluidos |
| Prototipo anterior, revisión D | Antecedente digital | Una pantalla izquierda y batería lateral; forma descartada |
| Carcasa estrecha y stack | CAD y renders nuevos | Bahía 24 mm; plate 7,6 mm; cubierta 19 mm. Cables y encaje real pendientes |
| Dos pantallas y electrónica modular | En diseño | Actualizar ambas PCB, CAD y firmware; una pantalla sigue siendo alternativa |
| BOM y archivos para fabricar | Pendiente | Cerrar la revisión modular y publicar fuentes coherentes |
| Impresión y montaje | Pendiente | Cupón Choc, tres keycaps y comprobación de piezas reales |
| Teclado funcionando | Pendiente | 36 teclas, BLE, carga, sueño/despertar y consumo medido |

## 2026-09-21 · Inicio público

Se comparte el layout, la dirección del diseño y la lista de componentes prevista. El trabajo previo pasó de 42 a 36 teclas, recuperó el contorno angular e integró una pantalla. La revisión siguiente busca una bahía más estrecha y acceso independiente a la electrónica.

Filo36 es el nombre provisional; también se consideran Sesgo36 y Brizna36.

## Corrección visual

La carcasa ancha de revD fue descartada. Su render permanece únicamente en el historial del repositorio; no representa la dirección actual. El nuevo CAD revE usa una bahía de 24 mm, dos pantallas sobre los micros y tapa electrónica independiente. La portada y las vistas de detalle se generan desde sus piezas STEP/STL. Se comprobó que las envolventes modeladas no invaden la carcasa ni se solapan entre sí; el cable de batería aún debe resolverse.

La bahía es **28,4% más estrecha**. El ancho máximo de cada mitad queda aproximadamente en 126,2 mm: el pulgar conserva su posición y sigue determinando buena parte de ese máximo. El stack aumenta la altura local de electrónica de 16 mm en la revD izquierda a 19 mm; el plate permanece a 7,6 mm.
