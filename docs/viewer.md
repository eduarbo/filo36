# Explorar Filo36 en 3D

**[Abrir el visor →](https://eduarbo.github.io/filo36/)**

Funciona en navegador, sin instalar CAD. Contiene el ensamblaje revE actual, con las mismas mallas del render y las KLP Lamé.

1. **Arrastra** para girar. Rueda o pellizco para acercar; dos dedos para mover.
2. Pulsa **Ver interior**, o desmarca **Tapas**, **Bases** y **Plates** en **Capas**. Puedes ocultar también keycaps, switches, PCB, baterías, micros, pantallas, conectores y soportes.
3. Usa **Sólo stack** y **Separar piezas** para ver batería → micro → pantalla. Elige izquierda, derecha o ambas mitades.
4. **Vista** ofrece superior, frontal, laterales, trasera e inferior. **Restablecer todo** recupera cámara, capas, ambas mitades y posiciones originales.

La separación es una ayuda visual; aún no acredita una secuencia real de desmontaje. La PCB no está ruteada y la electrónica usa envolventes nominales. Cables, contactos detallados, retención y ajuste físico siguen pendientes.

## Sin conexión o en otro programa

- **Navegador de escritorio:** dentro del visor, pulsa **Descargar HTML offline** y abre el archivo `.html` con Chrome, Safari o Firefox con WebGL 2. Incluye código, geometría y licencias; no necesita servidor ni CDN. En móvil, abrir HTML descargado depende del sistema: usa preferentemente el enlace web.
- **Blender u otro visor glTF:** pulsa **Descargar GLB ensamblado**. Incluye las dos mitades completas, todos los objetos por separado y sus nombres, aunque en pantalla hayas ocultado capas o separado piezas. El GLB usa metros, según glTF; el visor y CAD usan milímetros. Es una malla para inspección, no CAD paramétrico.
- **FreeCAD:** descarga [conjunto izquierdo](../mechanical/revE/left-assembly.step) y [conjunto derecho](../mechanical/revE/right-assembly.step). En GitHub usa **Download raw file**. Abre un STEP, despliega el árbol, selecciona `electronics-lid`, `tray` o `key-plate` y pulsa **Espacio** para ocultarlo. Si el importador agrupa todo en un único objeto, desactiva la fusión de compuestos STEP en las preferencias de importación y vuelve a importar. Los STEP contienen carcasa y volúmenes internos; las keycaps y proxies visuales del visor no forman parte de esos conjuntos.

Fuentes: [visibilidad en FreeCAD](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Std_ToggleVisibility.md), [preferencias de importación STEP](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Import_Export_Preferences.md). La previsualización STL de GitHub permite girar una pieza, pero el visor de este proyecto aporta el ensamblaje y sus filtros.

## Por qué sobresale arriba

En planta, la tapa llega **6,9 mm más arriba** que la KLP de la columna más adelantada y **13,9 mm** respecto a la columna vecina. Esa extensión pertenece a la cubierta electrónica, con el micro y USB debajo; la pantalla comienza más abajo. En altura, el vidrio llega a **18,3 mm**, la cubierta a un máximo de **19 mm** y el plate a **7,6 mm**. Esto describe el CAD actual; no se modificó la carcasa para generar el visor.

## Regenerar y verificar

Desde la raíz, con el entorno CAD de [cad.md](cad.md):

```sh
.venv/bin/python tools/build_viewer_scene.py
npm ci --prefix viewer --ignore-scripts
npm run build --prefix viewer
.venv/bin/python tools/check_viewer.py
```

El resultado es `docs/index.html`; GitHub Pages sirve `main:/docs` sin Jekyll ni un sistema de compilación remoto. `viewer/package-lock.json` fija Three.js y esbuild; sus integridades las comprueba npm. [Recibo de fuentes y geometría](../validation/revE-viewer.json).

`viewer/check.cjs` prueba el archivo con Playwright: carga sin red, los 12 filtros, mitades, rotación, vista inferior, reset visual idéntico y exportación GLB. Admite `FILO36_PLAYWRIGHT_MODULE` y `FILO36_BROWSER` para usar una instalación existente; `FILO36_VIEWER_URL` permite comprobar la URL publicada. Los resultados y capturas se generan en `build/`. La vista de 390 × 844 es emulación, no una prueba en un teléfono físico.
