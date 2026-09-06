# Informe de stock · Portfolio Power BI

Caso de inventario **simulado** basado en un catálogo y pedidos de ejemplo. Corte: **31/12/2017**. No representa stock real.

Incluye 400 productos, 9 depósitos, 307.802 movimientos y 12 cierres mensuales. Tres páginas: **Stock al cierre**, **Movimientos** y **Pedidos originales**. Modelo de 15 tablas, 17 relaciones y 17 medidas DAX.

## Abrir

1. Clonar el repositorio.
2. Ejecutar `python scripts/build_inventory.py` para reproducir datos y configurar la ruta local.
3. Abrir `Informe stock.pbip` en Power BI Desktop.
4. Actualizar y guardar para importar los datos en la caché local.

Los CSV preparados están incluidos. Sin Python, ajustar el parámetro **DataRoot** a la ruta absoluta de `data/prepared`. `python scripts/build_report.py` regenera y sobrescribe las páginas y medidas generadas.

## Estructura

- `archive/`: siete fuentes originales conservadas sin cambios de contenido.
- `data/prepared/`: datos normalizados, simulación y manifiesto de validación.
- `scripts/build_inventory.py`: simulación determinista, controles y modelo TMDL.
- `scripts/build_report.py`: medidas DAX y páginas PBIR.
- `Informe stock.SemanticModel/`: tablas, parámetro y relaciones.
- `Informe stock.Report/`: páginas, visuales y tema.
- [Diseño, supuestos y diccionario](docs/inventario-simulado.md).

## Criterios

El inventario y los pedidos históricos se analizan por separado. Los depósitos repetidos se consolidan con una tabla de correspondencias. Los cierres se concilian con movimientos y no se suman entre meses. Se usa **UM** porque la fuente no identifica moneda.

La procedencia/licencia de los CSV no está verificada. La utilidad previa `scripts/download_inventory_data.py` se conserva, pero no se usa ni acredita el origen de este caso. Los campos de contacto originales se excluyen del modelo analítico.

## Validación

Se verifican claves, relaciones, saldos y reservas. Esperado: **61.276 unidades físicas**, **56.430 disponibles** y **109.630.923,09 UM**. Detalles en `data/prepared/manifest.json`.

Tecnologías: Power BI Desktop, Power Query, DAX, TMDL, PBIR, Python estándar y Git.
