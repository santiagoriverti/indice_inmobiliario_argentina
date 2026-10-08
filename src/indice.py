"""Calculo del indice: alquiler + expensas como % del salario y salarios necesarios por m2.

Entradas (todas mensuales, indice PeriodIndex):
- `zp`: niveles de Zonaprop por region (`zonaprop.series`): alquiler de 2 ambientes ($/mes) y
  precio de venta (USD/m2).
- `sal`: salarios (`salarios`): mediana y promedio SIPA sin aguinaldo y RIPTE.
- `exp`: expensas de un 2 ambientes ($/mes) por region (`expensas`).
- `tc`: tipo de cambio MEP y oficial (`fuentes.tipo_de_cambio`).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import fuentes

SALARIOS = {'mediana': 'Mediana SIPA (privados registrados)', 'ripte': 'RIPTE'}
DOLARES = {'mep': 'MEP', 'oficial': 'oficial A3500'}


def sin_aguinaldo(s: pd.Series, guia: pd.Series) -> pd.Series:
    """Saca el SAC de junio y diciembre de una serie SIPA (la publicada lo incluye).

    Junio/diciembre = media geometrica del mes anterior y el posterior. Si todavia no se publico
    el mes posterior, mes anterior x variacion de `guia` (RIPTE, que no incluye SAC).
    """
    s = s.dropna().copy()
    out = s.copy()
    for p in s.index[(s.index.month == 6) | (s.index.month == 12)]:
        ant, pos = p - 1, p + 1
        if ant in s.index and pos in s.index:
            out[p] = np.sqrt(s[ant] * s[pos])
        elif ant in s.index and p in guia.index and ant in guia.index:
            out[p] = s[ant] * guia[p] / guia[ant]
        else:
            out[p] = np.nan
    return out


def salarios(series: pd.DataFrame) -> pd.DataFrame:
    ripte = series['ripte'].dropna()
    return pd.DataFrame({
        'mediana': sin_aguinaldo(series['salario_mediana'], ripte),
        'promedio_sipa': sin_aguinaldo(series['salario_promedio'], ripte),
        'ripte': ripte,
    })


def expensas(series: pd.DataFrame, ancla: pd.DataFrame | None = None) -> pd.DataFrame:
    """Expensas de un 2 ambientes por region = monto ancla x indice IPC GBA "Reparaciones y gastos
    comunes de la vivienda" (t) / indice (mes del ancla). Solo regiones con ancla."""
    if ancla is None:
        ancla = pd.read_csv(fuentes.REFERENCIA / 'expensas_ancla.csv')
    idx = series['ipc_gba_gastos_comunes'].dropna()
    out = {}
    for _, a in ancla.iterrows():
        p = pd.Period(a['periodo'], freq='M')
        out[a['region']] = float(a['monto_2amb']) * idx / idx[p]
    return pd.DataFrame(out)


def calcular(zp: pd.DataFrame, sal: pd.DataFrame, exp: pd.DataFrame, tc: pd.DataFrame
             ) -> pd.DataFrame:
    """Tabla larga: una fila por (periodo, region) con niveles e indicadores.

    `zp` es largo: columnas periodo, region, alquiler_2amb, venta_usd_m2 (+ tipo_*).
    """
    filas = []
    for reg, z in zp.groupby('region'):
        z = z.set_index('periodo').sort_index()
        d = pd.DataFrame(index=z.index)
        d['region'] = reg
        d['alquiler_2amb'] = z['alquiler_2amb']
        d['tipo_alquiler'] = z['tipo_alquiler']
        d['expensas_2amb'] = exp[reg].reindex(d.index) if reg in exp else np.nan
        d['alquiler_mas_expensas'] = d['alquiler_2amb'] + d['expensas_2amb']
        d['venta_usd_m2'] = z['venta_usd_m2']
        d['tipo_venta'] = z['tipo_venta']
        for k in DOLARES:
            d[f'venta_m2_pesos_{k}'] = d['venta_usd_m2'] * tc[k].reindex(d.index)
        for s in SALARIOS:
            w = sal[s].reindex(d.index)
            d[f'salario_{s}'] = w
            d[f'pct_alquiler_{s}'] = 100 * d['alquiler_2amb'] / w
            d[f'pct_alquiler_expensas_{s}'] = 100 * d['alquiler_mas_expensas'] / w
            for k in DOLARES:
                d[f'salarios_por_m2_{s}_{k}'] = d[f'venta_m2_pesos_{k}'] / w
        filas.append(d)
    out = pd.concat(filas).reset_index().rename(columns={'index': 'periodo'})
    return out.sort_values(['region', 'periodo']).reset_index(drop=True)
