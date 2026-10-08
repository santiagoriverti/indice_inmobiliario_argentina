"""Compara el ZIP que descarga el notebook de Colab con los CSV versionados en data/processed/.

    python scripts/comparar_zip.py "C:/Users/.../Downloads/indice_inmobiliario.zip"

Para cada CSV del ZIP (carpeta csv/) informa filas en comun, filas que estan solo en uno de los dos
lados (esperable si Colab bajo datos mas nuevos con --refrescar) y la mayor diferencia relativa en
las columnas numericas de las filas en comun. Muestra la version del repo con la que corrio Colab
(LEEME.txt). Sale con codigo 1 si alguna diferencia supera la tolerancia.
"""
from __future__ import annotations

import io
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
PROCESADOS = RAIZ / 'data' / 'processed'
TOLERANCIA = 1e-9
# columnas que identifican cada fila (las tablas sin clave larga usan la primera columna)
CLAVES = {'indice_mensual.csv': ['region', 'periodo'], 'zonaprop_series.csv': ['region', 'periodo']}


def comparar(zip_path: Path) -> bool:
    z = zipfile.ZipFile(zip_path)
    if 'LEEME.txt' in z.namelist():
        version = [ln for ln in z.read('LEEME.txt').decode('utf-8').splitlines() if 'Version' in ln]
        print(version[0] if version else 'LEEME.txt sin version')
    ok = True
    for nombre in sorted(n for n in z.namelist() if n.startswith('csv/') and n.endswith('.csv')):
        archivo = nombre.split('/', 1)[1]
        local = PROCESADOS / archivo
        if not local.exists():
            print(f'{archivo}: no existe en data/processed')
            ok = False
            continue
        a = pd.read_csv(io.BytesIO(z.read(nombre)))
        b = pd.read_csv(local)
        clave = CLAVES.get(archivo, [a.columns[0]])
        m = a.merge(b, on=clave, how='outer', suffixes=('_zip', '_local'), indicator=True)
        solo_zip = int((m['_merge'] == 'left_only').sum())
        solo_local = int((m['_merge'] == 'right_only').sum())
        comun = m[m['_merge'] == 'both']
        peor, col_peor, filas_dif = 0.0, '', set()
        for c in a.columns:
            if c in clave or c not in b.columns or not pd.api.types.is_numeric_dtype(a[c]):
                continue
            x, y = comun[f'{c}_zip'].astype(float), comun[f'{c}_local'].astype(float)
            ambos_nan = x.isna() & y.isna()
            dif = (x - y).abs() / y.abs().where(y != 0, 1.0)
            dif = dif[~ambos_nan].fillna(np.inf)   # NaN de un solo lado = diferencia
            filas_dif |= set(dif[dif > TOLERANCIA].index)
            if len(dif) and dif.max() > peor:
                peor, col_peor = float(dif.max()), c
        estado = 'OK' if peor <= TOLERANCIA else 'DIFERENCIA'
        ok &= peor <= TOLERANCIA
        print(f'{archivo}: {len(comun)} filas en comun, {solo_zip} solo en el ZIP, {solo_local} solo '
              f'en local; mayor dif. relativa {peor:.2e} {col_peor} -> {estado}')
        if filas_dif:
            claves = comun.loc[sorted(filas_dif), clave].astype(str).agg(' '.join, axis=1).tolist()
            print(f'    filas con diferencias ({len(claves)}): {", ".join(claves[:8])}'
                  + (' ...' if len(claves) > 8 else ''))
    return ok


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(0 if comparar(Path(sys.argv[1])) else 1)
