> Para modificar cotas y circuitería, empieza por la [guía FreeCAD + KiCad + StepUp](freecad.md).

# Explorar Filo36 en 3D

**[Abrir el visor →](https://eduarbo.github.io/filo36/)**

Funciona en navegador, sin instalar CAD. Contiene el ensamblaje revF actual, con las mismas mallas del render y las KLP Lamé.

1. **Arrastra** para girar. Rueda o pellizco para acercar; dos dedos para mover.
2. Pulsa **Ver interior**, o desmarca **Marco / tapas**, **Bases** y **Plates** en **Capas**. Puedes ocultar también keycaps, switches, PCB, baterías, micros, pantallas, conectores y soportes.
3. Usa **Sólo stack** y **Separar piezas** para ver batería → micro → pantalla. Elige izquierda, derecha o ambas mitades.
4. **Vista** ofrece superior, frontal, laterales, trasera e inferior. **Restablecer todo** recupera cámara, capas, ambas mitades y posiciones originales.

La separación es una ayuda visual; aún no acredita una secuencia real de desmontaje. La PCB no está ruteada y la electrónica usa envolventes nominales. Cables, contactos detallados, retención y ajuste físico siguen pendientes.

## Sin conexión o en otro programa

- **Navegador de escritorio:** dentro del visor, pulsa **Descargar HTML offline** y abre el archivo `.html` con Chrome, Safari o Firefox con WebGL 2. Incluye código, geometría y licencias; no necesita servidor ni CDN. En móvil, abrir HTML descargado depende del sistema: usa preferentemente el enlace web.
- **Blender u otro visor glTF:** pulsa **Descargar GLB ensamblado**. Incluye las dos mitades completas, todos los objetos por separado y sus nombres, aunque en pantalla hayas ocultado capas o separado piezas. El GLB usa metros, según glTF; el visor y CAD usan milímetros. Es una malla para inspección, no CAD paramétrico.
- **FreeCAD:** abre el [FCStd editable](../mechanical/revF/Filo36.FCStd), con piezas independientes y parámetros. Selecciona una pieza y pulsa **Espacio** para ocultarla. Los STEP por mitad son una alternativa para otros CAD, sin el historial paramétrico ni las keycaps. [Guía de edición](freecad.md).

Fuentes: [visibilidad en FreeCAD](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Std_ToggleVisibility.md), [preferencias de importación STEP](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Import_Export_Preferences.md). La previsualización STL de GitHub permite girar una pieza, pero el visor de este proyecto aporta el ensamblaje y sus filtros.

## Qué cambió en revF

El marco abierto sustituye la cubierta alta: **16,6 mm** frente a 19 mm. La pantalla llega a **16,1 mm** y el plate permanece a **7,6 mm**. En planta, el stack completo incluido el USB queda 0,045 mm detrás del borde norte nominal de la tecla vecina. Es una alineación del modelo, sin tolerancia física validada. La batería ocupa una abertura real del PCB.

## Regenerar y verificar

Desde la raíz, con el entorno CAD de [cad.md](cad.md):

```sh
.venv/bin/python tools/build_viewer_revF.py
npm ci --prefix viewer --ignore-scripts
npm run build --prefix viewer
.venv/bin/python tools/check_viewer_revF.py
```

El resultado es `docs/index.html`; GitHub Pages sirve `main:/docs` sin Jekyll ni un sistema de compilación remoto. `viewer/package-lock.json` fija Three.js y esbuild; sus integridades las comprueba npm. [Recibo de fuentes y geometría](../validation/revF-viewer.json).

`viewer/check.cjs` prueba el archivo con Playwright: carga sin red, los 12 filtros, mitades, rotación, vista inferior, reset visual idéntico y exportación GLB. Admite `FILO36_PLAYWRIGHT_MODULE` y `FILO36_BROWSER` para usar una instalación existente; `FILO36_VIEWER_URL` permite comprobar la URL publicada. Los resultados y capturas se generan en `build/`. La vista de 390 × 844 es emulación, no una prueba en un teléfono físico.
