"""Construye el indice y actualiza los archivos versionados (data/processed/ y output/).

    python scripts/construir.py              # usa el cache de data/cache/
    python scripts/construir.py --refrescar  # baja de nuevo salarios, IPC y dolar

Las cifras de Zonaprop salen de data/reference/zonaprop_valores.csv: para actualizarlas,
correr antes `python scripts/actualizar_zonaprop.py`.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use('Agg')  # sin ventanas: solo se guardan PNG
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import exportar, fuentes, pipeline  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--refrescar', action='store_true')
    a = ap.parse_args()
    R = pipeline.construir(refrescar=a.refrescar)
    exportar.exportar(R, fuentes.OUTPUT, fuentes.PROCESADOS)
    res = exportar.ultimo_dato(R['indice'])
    print(res.to_string(index=False, float_format=lambda x: f'{x:,.2f}'))
    cob = (R['zonaprop'].groupby(['region', 'tipo_alquiler']).size().unstack(fill_value=0))
    print('\nOrigen de los datos de alquiler por region (meses):')
    print(cob.to_string())


if __name__ == '__main__':
    main()
