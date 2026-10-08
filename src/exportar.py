"""Exportacion: CSV (data/processed), Excel + graficos PNG (output) y ZIP para los notebooks.

- `exportar(R, dir_salida, dir_datos)`: escribe indice_inmobiliario.xlsx y graficos/ en dir_salida
  y los CSV en dir_datos. `scripts/construir.py` lo usa con output/ y data/processed/ (versionados).
- `zip_resultados(R, nombre)`: lo que llaman los notebooks al final. Exporta todo a
  _descargas/<nombre>/ (ignorado por git) y lo comprime en _descargas/<nombre>.zip.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from . import fuentes, graficos

DESCARGAS = fuentes.RAIZ / '_descargas'

NOTAS = [
    ('Alquiler', 'Zonaprop Index: alquiler medio publicado de un departamento de 2 ambientes y 50 m2 '
                 '(precio de oferta de contratos nuevos, sin expensas).'),
    ('Venta', 'Zonaprop Index: precio medio publicado de departamentos, USD por m2.'),
    ('Expensas', 'Solo CABA. Ancla: mediana de expensas de avisos de 2 ambientes (Propio, jun-2026), '
                 'llevada al resto de los meses con el IPC GBA de INDEC "Reparaciones y gastos comunes '
                 'de la vivienda" (desde abr-2016).'),
    ('Salario mediano', 'Remuneracion bruta mediana de asalariados registrados del sector privado (SIPA). '
                        'Junio y diciembre sin aguinaldo (media geometrica de los meses vecinos).'),
    ('RIPTE', 'Remuneracion imponible promedio de los trabajadores estables (sin aguinaldo).'),
    ('Dolar', 'MEP promedio mensual (argentinadatos; antes de nov-2018, CCL empalmado). Oficial: A3500 BCRA.'),
    ('tipo_*', 'publicado = cifra del informe del mes; derivado_* = calculado desde la cifra y la variacion '
               'que publica otro informe; interpolado = hueco completado (alquiler: siguiendo el IPC '
               'nacional nivel general; venta: log-lineal).'),
]


def _sin_period(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for c in df.columns:
        if isinstance(df[c].dtype, pd.PeriodDtype):
            df[c] = df[c].astype(str)
    if isinstance(df.index, pd.PeriodIndex):
        df.index = df.index.astype(str)
    return df


def version_repo() -> str:
    try:
        return subprocess.run(['git', '-C', str(fuentes.RAIZ), 'log', '-1', '--format=%h %ci'],
                              capture_output=True, text=True, timeout=10).stdout.strip() or 'sin git'
    except (OSError, subprocess.SubprocessError):
        return 'sin git'


def ultimo_dato(tabla: pd.DataFrame) -> pd.DataFrame:
    """Ultimo mes con alquiler y salario mediano de cada region (para el resumen)."""
    cols = ['region', 'periodo', 'alquiler_2amb', 'expensas_2amb', 'salario_mediana',
            'pct_alquiler_mediana', 'pct_alquiler_expensas_mediana', 'venta_usd_m2',
            'salarios_por_m2_mediana_mep', 'salarios_por_m2_mediana_oficial',
            'pct_alquiler_ripte', 'salarios_por_m2_ripte_mep']
    t = tabla.dropna(subset=['pct_alquiler_mediana'])
    return t.groupby('region').tail(1)[cols].reset_index(drop=True)


def tablas_csv(R: dict) -> dict[str, tuple[pd.DataFrame, bool]]:
    return {
        'indice_mensual.csv': (R['indice'], False),
        'zonaprop_series.csv': (R['zonaprop'], False),
        'salarios.csv': (R['salarios'], True),
        'tipo_de_cambio.csv': (R['tc'], True),
        'expensas.csv': (R['expensas'], True),
    }


def exportar(R: dict, dir_salida: Path, dir_datos: Path) -> None:
    dir_salida.mkdir(parents=True, exist_ok=True)
    dir_datos.mkdir(parents=True, exist_ok=True)
    for archivo, (t, con_indice) in tablas_csv(R).items():
        _sin_period(t).to_csv(dir_datos / archivo, index=con_indice, encoding='utf-8')
    with pd.ExcelWriter(dir_salida / 'indice_inmobiliario.xlsx') as xw:
        _sin_period(ultimo_dato(R['indice'])).to_excel(xw, sheet_name='Resumen', index=False)
        _sin_period(R['indice']).to_excel(xw, sheet_name='Indice_mensual', index=False)
        _sin_period(R['zonaprop']).to_excel(xw, sheet_name='Zonaprop', index=False)
        _sin_period(R['salarios']).to_excel(xw, sheet_name='Salarios')
        _sin_period(R['tc']).to_excel(xw, sheet_name='Tipo_de_cambio')
        _sin_period(R['expensas']).to_excel(xw, sheet_name='Expensas')
        notas = pd.DataFrame(NOTAS + [('Version del repo', version_repo())], columns=['Tema', 'Nota'])
        notas.to_excel(xw, sheet_name='Notas', index=False)
    dir_g = dir_salida / 'graficos'
    dir_g.mkdir(exist_ok=True)
    for nombre, fig in graficos.todos(R['indice']).items():
        fig.savefig(dir_g / f'{nombre}.png', bbox_inches='tight')
        plt.close(fig)


def zip_resultados(R: dict, nombre: str = 'indice_inmobiliario') -> Path:
    destino = DESCARGAS / nombre
    if destino.exists():
        shutil.rmtree(destino)
    exportar(R, destino, destino / 'csv')
    (destino / 'LEEME.txt').write_text(
        'Indice inmobiliario Argentina\nVersion del repo: ' + version_repo() + '\n\n'
        + '\n'.join(f'{t}: {n}' for t, n in NOTAS) + '\n', encoding='utf-8')
    return Path(shutil.make_archive(str(destino), 'zip', destino))
