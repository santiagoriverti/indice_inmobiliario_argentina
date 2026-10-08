# Índice inmobiliario Argentina

Cuánto pesa la vivienda en el salario: dos indicadores mensuales para **CABA** y el **GBA** (Norte,
Oeste y Sur).

1. **Costo de alquilar**: alquiler de un departamento de 2 ambientes y 50 m² (más expensas, en CABA)
   como porcentaje del salario.
2. **Costo de comprar**: cuántos salarios hacen falta para pagar un m² de departamento.

[![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/santiagoriverti/indice_inmobiliario_argentina/blob/main/notebooks/01_indice_inmobiliario.ipynb)

## Fuentes

| Dato | Fuente |
|---|---|
| Alquiler y precio de venta | [Zonaprop Index](https://www.zonaprop.com.ar/blog/) (informes mensuales en PDF; los viejos, del [Internet Archive](https://web.archive.org/)) |
| Salario | Mediana de la remuneración bruta de asalariados privados registrados (SIPA) y RIPTE, vía [datos.gob.ar](https://datos.gob.ar/series) |
| Expensas | Ancla: mediana de expensas en avisos de 2 ambientes (Propio, jun-2026) × IPC GBA de INDEC "Reparaciones y gastos comunes de la vivienda" |
| Dólar | MEP ([argentinadatos](https://argentinadatos.com/)) y oficial A3500 ([BCRA](https://www.bcra.gob.ar/)) |

Método, decisiones y trampas: [`CONTEXTO.md`](CONTEXTO.md). Estado y cifras vigentes:
[`ESTADO.md`](ESTADO.md).

## Uso

```bash
pip install -r requirements.txt
python scripts/actualizar_zonaprop.py   # busca y lee los informes nuevos de Zonaprop
python scripts/construir.py --refrescar # baja salarios, IPC y dólar; escribe data/processed y output
python -m pytest tests -q
```

Salidas versionadas: `data/processed/*.csv` (series) y `output/indice_inmobiliario.xlsx` +
`output/graficos/`. El notebook de Colab arma todo y descarga un ZIP con Excel, CSV y gráficos.

## Limitaciones

- Zonaprop mide **precios publicados** (oferta), no de cierre, y el alquiler es de **contratos
  nuevos** (no lo que pagan los inquilinos con contrato vigente).
- Faltan informes mensuales en el archivo: esos meses se derivan de las variaciones publicadas en
  otros informes o se interpolan (cada dato indica su origen en `tipo_alquiler` / `tipo_venta`).
- Las expensas se estiman solo para CABA y dependen de un único nivel ancla.
- El salario es el de los **asalariados registrados del sector privado** (no incluye informales ni
  cuentapropistas) y es **bruto**.
