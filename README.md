# Índice inmobiliario Argentina

Cuánto pesa la vivienda en el salario: dos indicadores mensuales para **CABA** y el **GBA** (Norte,
Oeste y Sur).

1. **Costo de alquilar**: alquiler de un departamento de 2 ambientes y 50 m² (más expensas, en CABA)
   como porcentaje del salario.
2. **Costo de comprar**: cuántos salarios hacen falta para pagar un m² de departamento.

[![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/santiagoriverti/indice_inmobiliario_argentina/blob/main/notebooks/01_indice_inmobiliario.ipynb)

Proyecto de INECO–UADE. **Versión actual: prueba piloto** con los informes públicos del Zonaprop
Index. La versión definitiva usará un relevamiento propio de INECO de avisos de portales
inmobiliarios (por convenio o *web scraping*); la metodología está en la sección del informe
[`docs/informe_indicadores/seccion_inmobiliario.tex`](docs/informe_indicadores/seccion_inmobiliario.tex).

## Fuentes (prueba piloto)

| Dato | Fuente |
|---|---|
| Alquiler y precio de venta | [Zonaprop Index](https://www.zonaprop.com.ar/blog/) (informes mensuales en PDF; los viejos, del [Internet Archive](https://web.archive.org/)) |
| Salario | Mediana de la remuneración bruta de asalariados privados registrados (SIPA) y RIPTE, vía [datos.gob.ar](https://datos.gob.ar/series) |
| Expensas | Ancla: mediana de expensas en avisos de 2 ambientes (Propio, jun-2026) × IPC GBA de INDEC "Reparaciones y gastos comunes de la vivienda" |
| Dólar | MEP ([argentinadatos](https://argentinadatos.com/)) y oficial A3500 ([BCRA](https://www.bcra.gob.ar/)) |

Método, decisiones, trampas y mapa del código: [`CONTEXTO.md`](CONTEXTO.md). Estado, cifras
vigentes, próximos pasos y cómo seguir desde otra PC: [`ESTADO.md`](ESTADO.md).

## Uso

```bash
pip install -r requirements.txt
python scripts/actualizar_zonaprop.py   # busca y lee los informes nuevos de Zonaprop
python scripts/construir.py --refrescar # baja salarios, IPC y dólar; escribe data/processed y output
python -m pytest tests -q
python scripts/comparar_zip.py <zip>    # compara el ZIP que descarga el notebook de Colab
```

En Windows, correr Python con `PYTHONUTF8=1`.

## Estructura

| Carpeta | Contenido |
|---|---|
| `src/` | código: fuentes por API, Zonaprop (PDFs), cálculo del índice, exportación y gráficos |
| `scripts/` | `actualizar_zonaprop.py`, `construir.py`, `gen_notebooks.py`, `comparar_zip.py` |
| `notebooks/` | `01_indice_inmobiliario.ipynb` (generado por `gen_notebooks.py`) |
| `data/reference/` | catálogo y cifras extraídas de los PDFs de Zonaprop; ancla de expensas |
| `data/processed/` | series mensuales (CSV) |
| `output/` | `indice_inmobiliario.xlsx` y `graficos/` |
| `docs/informe_indicadores/` | sección LaTeX del informe INECO "Propuesta de Indicadores Económicos" |
| `tests/` | tests (`pytest`) |

`data/cache/` (descargas y PDFs) y `_descargas/` (ZIP de los notebooks) no se versionan.

## Limitaciones

- Zonaprop mide **precios publicados** (oferta), no de cierre, y el alquiler es de **contratos
  nuevos** (no lo que pagan los inquilinos con contrato vigente).
- Faltan informes mensuales en el archivo: esos meses se derivan de las variaciones publicadas en
  otros informes o se interpolan (cada dato indica su origen en `tipo_alquiler` / `tipo_venta`).
- Las expensas se estiman solo para CABA y dependen de un único nivel ancla.
- El salario es el de los **asalariados registrados del sector privado** (no incluye informales ni
  cuentapropistas) y es **bruto**.
