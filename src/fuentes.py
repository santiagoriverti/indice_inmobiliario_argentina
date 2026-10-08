"""Descarga (con cache en data/cache/) de las fuentes por API.

- Salarios: mediana y promedio SIPA del sector privado registrado y RIPTE (datos.gob.ar).
- IPC GBA (INDEC) "Reparaciones y gastos comunes de la vivienda" (indice de expensas) e IPC
  nacional nivel general (guia para interpolar los huecos del alquiler).
- Tipo de cambio: MEP (argentinadatos, desde oct-2018) empalmado hacia atras con el CCL (desde
  2013) y oficial A3500 (BCRA API v4, variable 5).

Todas las funciones devuelven series mensuales con indice `pd.PeriodIndex` (freq M).
"""
from __future__ import annotations

import json
import time
import warnings
from pathlib import Path

import pandas as pd
import requests

RAIZ = Path(__file__).resolve().parents[1]
CACHE = RAIZ / 'data' / 'cache'
REFERENCIA = RAIZ / 'data' / 'reference'
PROCESADOS = RAIZ / 'data' / 'processed'
OUTPUT = RAIZ / 'output'

HEADERS = {'User-Agent': 'Mozilla/5.0 (indice_inmobiliario_argentina)'}

URL_SERIES = 'https://apis.datos.gob.ar/series/api/series/'
SERIES = {
    'salario_mediana': '153.1_RNERACIANA_2009_M_20',   # SIPA, bruta, incluye SAC en jun/dic
    'salario_promedio': '153.1_RNERACIDIO_2009_M_21',  # SIPA, bruta, incluye SAC en jun/dic
    'ripte': '158.1_REPTE_0_0_5',                      # sin SAC
    'ipc_gba_gastos_comunes': '104.1_I2C_2016_M_42',   # base abr-2016
    'ipc_nacional': '148.3_INIVELNAL_DICI_M_26',       # base dic-2016
}

URL_ARGENTINADATOS = 'https://api.argentinadatos.com/v1/cotizaciones/dolares/{casa}'
URL_BCRA = 'https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/{id}'
BCRA_A3500 = 5


def _cache(nombre: str) -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    return CACHE / nombre


def _get(url: str, *, params: dict | None = None, verify: bool = True, intentos: int = 3,
         timeout: int = 90) -> requests.Response:
    for i in range(intentos):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=timeout, verify=verify)
            r.raise_for_status()
            return r
        except requests.RequestException:
            if i == intentos - 1:
                raise
            time.sleep(3 * (i + 1))
    raise RuntimeError('inalcanzable')


def series_datos_gob(refrescar: bool = False) -> pd.DataFrame:
    """Todas las series de SERIES en un DataFrame mensual (columnas = claves de SERIES)."""
    archivo = _cache('series_datos_gob.csv')
    if refrescar or not archivo.exists():
        r = _get(URL_SERIES, params={'ids': ','.join(SERIES.values()), 'format': 'csv',
                                     'limit': 5000, 'header': 'ids'})
        archivo.write_bytes(r.content)
    df = pd.read_csv(archivo)
    df['indice_tiempo'] = pd.PeriodIndex(df['indice_tiempo'], freq='M')
    df = df.set_index('indice_tiempo').rename(columns={v: k for k, v in SERIES.items()})
    return df[list(SERIES)]


def _argentinadatos(casa: str, refrescar: bool) -> pd.Series:
    archivo = _cache(f'dolar_{casa}.json')
    if refrescar or not archivo.exists():
        archivo.write_bytes(_get(URL_ARGENTINADATOS.format(casa=casa)).content)
    d = pd.DataFrame(json.loads(archivo.read_text(encoding='utf-8')))
    d['fecha'] = pd.to_datetime(d['fecha'])
    return d.set_index('fecha')['venta'].astype(float).sort_index()


def _bcra(variable: int, refrescar: bool, desde: str = '2010-01-01') -> pd.Series:
    archivo = _cache(f'bcra_{variable}.csv')
    if refrescar or not archivo.exists():
        filas, offset = [], 0
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')  # el certificado del BCRA no valida (verify=False)
            while True:
                r = _get(URL_BCRA.format(id=variable), verify=False,
                         params={'desde': desde, 'limit': 3000, 'offset': offset})
                det = r.json()['results'][0]['detalle']
                filas += det
                if len(det) < 3000:
                    break
                offset += 3000
        pd.DataFrame(filas).to_csv(archivo, index=False)
    d = pd.read_csv(archivo, parse_dates=['fecha'])
    return d.set_index('fecha')['valor'].astype(float).sort_index()


def tipo_de_cambio(refrescar: bool = False) -> pd.DataFrame:
    """Promedios mensuales: `mep` (MEP; antes de oct-2018, CCL empalmado), `oficial` (A3500).

    El empalme multiplica el CCL por el cociente medio MEP/CCL de los primeros 6 meses con ambos
    datos, para no generar un salto en oct-2018. `mep_fuente` dice que serie se uso cada mes.
    """
    mep = _argentinadatos('bolsa', refrescar).resample('MS').mean()
    ccl = _argentinadatos('contadoconliqui', refrescar).resample('MS').mean()
    ofi = _bcra(BCRA_A3500, refrescar).resample('MS').mean()
    mep.index = mep.index.to_period('M')
    ccl.index = ccl.index.to_period('M')
    ofi.index = ofi.index.to_period('M')
    # el primer mes del MEP es parcial (arranca el 29-oct-2018): empalmar desde el segundo
    mep = mep.iloc[1:]
    comunes = mep.index.intersection(ccl.index)[:6]
    factor = float((mep[comunes] / ccl[comunes]).mean())
    antes = ccl[ccl.index < mep.index[0]] * factor
    tc = pd.DataFrame({'mep': pd.concat([antes, mep]), 'oficial': ofi})
    tc['mep_fuente'] = 'MEP'
    tc.loc[tc.index < mep.index[0], 'mep_fuente'] = f'CCL x {factor:.4f}'
    tc.loc[tc['mep'].isna(), 'mep_fuente'] = None
    return tc.sort_index()
