# Piezas y alternativas

Lista de planificación para **un teclado completo de 36 teclas**. La revisión modular todavía no tiene una BOM cerrada: tamaños de conectores, pines y tornillos dependen del encaje final. No incluye precios ni disponibilidad verificados.

| Pieza | Cantidad | Base prevista | Alternativa / diferencia |
|---|---:|---|---|
| PCB | 1 izquierda + 1 derecha | Diseño propio, 2 capas | La Piantor RP2040 comercial no sustituye estas PCB |
| Micro | 2 | nice!nano v2 original | Clones requieren comprobar pinout, carga y consumo; XIAO exige rediseño |
| Switches | 36; comprar 40 da repuestos | Kailh Choc v1 Pro Red, 35 gf | Pro Pink, 20 gf: más ligero; Red, 50 gf: más resistencia; Ambients: silenciosos |
| Sockets de switch | 36; 40 con repuestos | Kailh CPG135001S30 para Choc | Sockets MX no son compatibles |
| Diodos | 36; 50 con repuestos | 1N4148W, SOD-123 | Otro encapsulado requiere otro footprint |
| Batería | 2 | Adafruit 1570, protegida, 1S 3,7 V, 100 mAh | Otra celda requiere revisar medidas, protección, polaridad y carga admisible |
| Pantalla | 2 previstas | nice!view | 1 en izquierda reduce piezas; OLED/e-paper requieren adaptación |
| Socket de micro | 4 tiras de 12 | Mill-Max 315-43-112-41-003000 | Otro socket cambia altura y pin compatible |
| Pines de micro | 48 + repuestos | Redondos de 0,5 mm | Longitud por cerrar con el separador; no usar pines cuadrados en sockets torneados |
| Conector de pantalla | 2 filas de 5 + 10 pines | Sockets y pines redondos, altura guiada | Los sockets nice!view de 7 mm no se asumen válidos para el stack elevado |
| Conector de batería | 2 | JST-PH de 2 pines compatible con la batería | Orientación y footprint por cerrar; conservar el cable de fábrica |
| Interruptor | 2 | C&K PCM12SMTR | Revisar huella y acceso de cualquier sustituto |
| Reset | 2 | E-Switch TL3342F160QG | Revisar altura y huella |
| Tornillería | Por cerrar | M2, tapa de servicio independiente | La longitud depende del stack definitivo |
| Patas | 8 | Goma adhesiva, 1–1,5 mm | Se suman a la altura del teclado |
| Aislamiento y retención | Poco material | Poliimida y fijación removible de la cuna | Sin presión sobre la bolsa de la batería |
| Keycaps | 36 | KLP Lamé: 28 normales, 2 homing y 6 thumb | Choc Stem + Choc Size; no variante MX |
| Piezas impresas | 1 juego | Bases, plates, tapas, cunas y separadores | Cantidades finales junto al CAD |
| USB-C de datos | 1–2 | Carga y programación | Verificar el tamaño del enchufe contra la abertura |

También hacen falta soldador de punta fina, estaño, flux, pinzas, alicate de corte y multímetro. La X2D puede producir carcasa y keycaps; la PCB se encarga a un fabricante.

Para los primeros ensayos ya sirven PLA Basic y PETG HF. ABS es otra opción para carcasa, con mayor exigencia de impresión. La orientación, el encaje del vástago y la tolerancia importan más que elegir un filamento por nombre: primero un cupón y tres teclas, después el juego completo.

Referencias: [nice!nano](https://nicekeyboards.com/nice-nano/), [nice!view](https://nicekeyboards.com/nice-view/), [Adafruit 1570](https://www.adafruit.com/product/1570), [Kailh Choc](https://www.kailhswitch.com/info/kailh-switches-introduction-list-27266403.html), [Ambients](https://lowprokb.ca/products/ambients-silent-choc-switches), [KLP Lamé](https://github.com/braindefender/KLP-Lame-Keycaps).
