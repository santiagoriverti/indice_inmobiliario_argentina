"""Actualiza las cifras de Zonaprop: catalogo de PDFs -> descarga -> extraccion.

    python scripts/actualizar_zonaprop.py              # todo (descubre, baja lo nuevo, extrae)
    python scripts/actualizar_zonaprop.py --sin-descubrir   # usa el catalogo versionado
    python scripts/actualizar_zonaprop.py --solo-extraer    # re-lee los PDFs del cache

Escribe data/reference/zonaprop_catalogo.csv y data/reference/zonaprop_valores.csv.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import zonaprop  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--sin-descubrir', action='store_true')
    ap.add_argument('--solo-extraer', action='store_true')
    ap.add_argument('--desde-sitio', default='2024-01',
                    help='primer mes a probar en el sitio actual (antes: solo Wayback)')
    a = ap.parse_args()

    if a.solo_extraer or a.sin_descubrir:
        cat = pd.read_csv(zonaprop.CATALOGO, dtype=str).fillna('')
    else:
        cat = zonaprop.descubrir(desde_sitio=a.desde_sitio)
        cat.to_csv(zonaprop.CATALOGO, index=False)
    print(f'Catalogo: {len(cat)} informes')
    print(cat.groupby('region')['periodo'].agg(['count', 'min', 'max']).to_string())

    if not a.solo_extraer:
        fallas = zonaprop.descargar(cat)
        print(f'Descarga: {len(fallas)} fallas' + (f' -> {fallas}' if fallas else ''))

    val = zonaprop.extraer_todo(cat)
    val.to_csv(zonaprop.VALORES, index=False)
    print(f'Valores: {len(val)} filas -> {zonaprop.VALORES}')
    for var in zonaprop.VARIABLES:
        print(f'  {var}: {val[var].notna().sum()} informes con dato')
    sin = val[val['alquiler_2amb'].isna() | val['venta_usd_m2'].isna()]
    if len(sin):
        print('  Sin alquiler o sin venta:', ', '.join(sin['region'] + ' ' + sin['periodo']))
    ch, emp = zonaprop.chequeos(val)
    print(f'Empalmes por revision de la serie: {len(emp)}')
    if len(emp):
        print(emp.to_string(index=False))
    malos = ch[~ch['ok']] if len(ch) else ch
    print(f'Chequeo derivado vs publicado (empalmados): {len(ch)} comparaciones, '
          f'{len(malos)} fuera de tolerancia')
    if len(malos):
        print(malos.to_string(index=False))


if __name__ == '__main__':
    main()
