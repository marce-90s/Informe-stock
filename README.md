# Informe de stock · Portfolio Power BI

Caso de inventario **simulado** (catálogo y pedidos de ejemplo). Corte: **31/12/2017**. No representa stock real.

## Ver el reporte

**[📄 Informe completo en PDF](docs/Informe-stock.pdf)** — exportación de las tres páginas.

| Página | Contenido |
| --- | --- |
| 01 · Stock al cierre | Existencias, valorización, cobertura y posiciones bajo mínimo al corte |
| 02 · Movimientos | Entradas y salidas simuladas, saldo y conciliación contra el stock físico |
| 03 · Pedidos originales | Pedidos históricos del dataset de origen, analizados por separado |

## Capturas

Vistas de las tres páginas (o abrir el [PDF](docs/Informe-stock.pdf) para el detalle):

<!-- Al dejar los PNG en docs/img/, descomentar estas líneas:
![01 · Stock al cierre](docs/img/01-stock-al-cierre.png)
![02 · Movimientos](docs/img/02-movimientos.png)
![03 · Pedidos originales](docs/img/03-pedidos-originales.png)
-->

## Contexto

El dataset trae inventario a una fecha de corte y pedidos históricos que no cuadran con ese inventario. El informe los trata como dos dominios distintos: fotografía de stock por un lado, historial de pedidos por otro, sin mezclarlos en las mismas métricas.

## Datos

400 productos, 9 depósitos, 307.802 movimientos y 12 cierres mensuales. CSV preparados incluidos en `data/prepared/`.

La procedencia y licencia de los CSV no están verificadas. La utilidad `scripts/download_inventory_data.py` se conserva pero no se usa ni acredita el origen. Los campos de contacto originales se excluyen del modelo analítico. Se usa **UM** (unidad monetaria) porque la fuente no identifica moneda.

## Modelo

- Esquema en estrella: **15 tablas**, **17 relaciones**, **17 medidas DAX**.
- Depósitos repetidos consolidados con una tabla de correspondencias (`WarehouseMapping`).
- Cierres mensuales conciliados contra movimientos; no se suman entre meses.
- Medidas agrupadas en carpetas de visualización por tabla de origen: **Stock actual**, **Movimientos simulados**, **Cierre mensual**, **Conciliacion**, **Historico de pedidos**.

## Validación

Se verifican claves, relaciones, saldos y reservas. Valores esperados al corte: **61.276 unidades físicas**, **56.430 disponibles**, **109.630.923,09 UM**. Detalle en `data/prepared/manifest.json` y [`docs/validacion-powerbi.json`](docs/validacion-powerbi.json).

## Reproducir

1. Clonar el repositorio.
2. `python scripts/build_inventory.py` — regenera los datos y **escribe el parámetro `DataRoot` con la ruta absoluta de `data/prepared` en esta máquina**.
3. Abrir `Informe stock.pbip` en Power BI Desktop.
4. Actualizar y guardar para importar los datos a la caché local.

`scripts/build_report.py` regenera y sobrescribe las medidas DAX y las páginas PBIR.

> Power BI no resuelve rutas relativas de forma fiable, así que `DataRoot` necesita una ruta absoluta. En el repo se versiona el valor neutro `data/prepared`; el script de arriba lo reemplaza por la ruta local. Si tras guardar en Desktop aparece esa línea como modificada, no la commitees.

## Estructura

- `archive/` — siete fuentes originales, sin cambios de contenido.
- `data/prepared/` — datos normalizados, simulación y manifiesto de validación.
- `scripts/build_inventory.py` — simulación determinista, controles y modelo TMDL.
- `scripts/build_report.py` — medidas DAX y páginas PBIR.
- `scripts/validate_model.ps1`, `scripts/validate_live_model.ps1` — controles sobre el modelo publicado.
- `Informe stock.SemanticModel/` — tablas, parámetro y relaciones.
- `Informe stock.Report/` — páginas, visuales y tema.
- [`docs/inventario-simulado.md`](docs/inventario-simulado.md) — diseño, supuestos y diccionario de datos.

## Tecnologías

Power BI Desktop, Power Query, DAX, TMDL, PBIR, Python (librería estándar) y Git.

## Licencia

Código y documentación bajo licencia [MIT](LICENSE). No cubre los CSV de `archive/` ni `data/`: su procedencia y licencia no están verificadas (ver **Datos**).
