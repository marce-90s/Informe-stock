# Informe de Stock

Proyecto de portfolio desarrollado en Power BI para analizar informacion de stock y documentar el proceso de construccion de un informe empresarial desde su estructura inicial hasta sus futuras mejoras.

## Objetivo del proyecto

El objetivo es construir un tablero que permita visualizar, controlar y analizar informacion relacionada con stock, con foco en la organizacion del modelo de datos, la claridad del reporte y la trazabilidad del trabajo realizado.

Este repositorio tambien funciona como evidencia del proceso de desarrollo: cada cambio relevante se registra mediante Git, permitiendo ver la evolucion del informe paso a paso.

## Alcance inicial

El informe parte de una fuente de datos base y una estructura de proyecto Power BI en formato PBIP. A partir de esta base se iran incorporando visualizaciones, medidas, ajustes de modelo y mejoras de presentacion orientadas al analisis de stock.

## Contenido del repositorio

- `Informe stock.pbip`: archivo principal del proyecto Power BI.
- `Informe stock.Report`: definicion visual del reporte.
- `Informe stock.SemanticModel`: modelo semantico, tablas, relaciones y medidas.
- `Customer.csv`: archivo de datos utilizado como fuente inicial.

## Tecnologias utilizadas

- Power BI Desktop
- Modelo semantico en formato TMDL
- Git y GitHub para control de versiones
- Python y KaggleHub para descarga de datos

## Estado del proyecto

Proyecto en desarrollo. El repositorio se actualizara progresivamente con nuevas paginas, medidas DAX, mejoras visuales y documentacion del proceso.

## Fuente de datos

El proyecto contempla la descarga de datos desde la competencia `inventory-optimization` de Kaggle mediante KaggleHub.

Para descargar los archivos localmente:

```bash
pip install -r requirements.txt
python scripts/download_inventory_data.py
```

Los archivos descargados se guardan en `data/raw/inventory-optimization/`. Esa carpeta esta excluida del control de versiones para evitar subir datos externos o archivos pesados al repositorio.
