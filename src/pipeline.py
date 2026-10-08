"""Arma todo el indice a partir de las fuentes (lo usan construir.py y los notebooks)."""
from __future__ import annotations

import pandas as pd

from . import fuentes, indice, zonaprop


def valores_zonaprop() -> pd.DataFrame:
    """Cifras extraidas de los PDFs (versionadas en data/reference: no hace falta bajar PDFs)."""
    return pd.read_csv(zonaprop.VALORES, dtype={'periodo': str})


def construir(refrescar: bool = False) -> dict:
    series = fuentes.series_datos_gob(refrescar)
    tc = fuentes.tipo_de_cambio(refrescar)
    sal = indice.salarios(series)
    exp = indice.expensas(series)
    # guia para los huecos del alquiler: IPC nivel general (el IPC "Alquiler de la vivienda" mide
    # contratos vigentes, con saltos por ajustes anuales: abr-2024 +40% en un mes)
    zp = zonaprop.series(valores_zonaprop(), guia_alquiler=series['ipc_nacional'].dropna())
    tabla = indice.calcular(zp, sal, exp, tc)
    return {'indice': tabla, 'zonaprop': zp, 'salarios': sal, 'tc': tc, 'expensas': exp,
            'series': series}
