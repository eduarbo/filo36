# Construcción

La guía paso a paso se publicará con la primera revisión modular comprobada. Este repositorio todavía no entrega Gerbers, STL de carcasa ni UF2 finales de esa revisión.

El orden previsto es:

1. Comprobar la BOM y las dimensiones de los componentes recibidos.
2. Imprimir un cupón Choc y tres KLP Lamé; probar ajuste, retorno y comodidad.
3. Soldar y revisar las PCB, medir continuidad y comprobar polaridad.
4. Programar cada mitad con su firmware y probar las 36 teclas.
5. Montar batería, micro, pantalla y tapas, sin forzar cables ni vidrio.
6. Comprobar BLE, carga, sueño/despertar y consumo; registrar resultados.

## Explorar el layout ahora

`design/layout.json` contiene centros, ángulos y referencias de las 18 teclas de cada mitad, en milímetros. Los originales de Piantor y su commit están en `sources/` y `ATTRIBUTION.md`.

Con Python 3, sin dependencias adicionales:

```sh
python3 tools/check_layout.py
python3 tools/render_layout.py
```

El primer comando compara las 36 posiciones y rotaciones con las PCB originales. El segundo regenera el diagrama de portada. Los archivos KiCad en `sources/piantor/` son las fuentes **cableadas originales**, incluidas para verificar procedencia; no son las PCB inalámbricas de Filo36.
