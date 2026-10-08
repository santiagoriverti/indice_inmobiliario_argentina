"""Genera los notebooks de notebooks/ (no editarlos a mano: editar este script y regenerar).

Uso:  python scripts/gen_notebooks.py
"""
from __future__ import annotations

import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

SETUP = r'''# Configuracion: en Colab clona (o actualiza) el repo; en local usa la carpeta del repo
import os, sys, subprocess, importlib
REPO = 'https://github.com/santiagoriverti/indice_inmobiliario_argentina.git'
if 'google.colab' in sys.modules:
    RAIZ = '/content/indice_inmobiliario_argentina'
    if os.path.exists(RAIZ):
        # Trae la ultima version de GitHub y descarta cambios locales (la copia de Colab es descartable)
        subprocess.run(['git', '-C', RAIZ, 'fetch', '-q', '--depth', '1', 'origin', 'main'], check=True)
        subprocess.run(['git', '-C', RAIZ, 'reset', '-q', '--hard', 'FETCH_HEAD'], check=True)
    else:
        subprocess.run(['git', 'clone', '-q', '--depth', '1', REPO, RAIZ], check=True)
else:  # subir desde la carpeta actual hasta encontrar el repo
    RAIZ = os.getcwd()
    while not os.path.exists(os.path.join(RAIZ, 'src', 'pipeline.py')) and os.path.dirname(RAIZ) != RAIZ:
        RAIZ = os.path.dirname(RAIZ)
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)
# Si el notebook ya se corrio en esta sesion, olvidar los modulos de src cargados (pueden ser viejos)
for m in [m for m in sys.modules if m == 'src' or m.startswith('src.')]:
    del sys.modules[m]
importlib.invalidate_caches()
v = subprocess.run(['git', '-C', RAIZ, 'log', '-1', '--format=%h (%ad) %s', '--date=short'],
                   capture_output=True, text=True).stdout.strip()
print('Version del repo:', v or 'sin git')

import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display, Markdown
from src import pipeline, graficos, exportar
pd.set_option('display.float_format', lambda x: f'{x:,.2f}')
pd.set_option('display.max_columns', 30)'''


def md(texto: str) -> dict:
    return {'cell_type': 'markdown', 'metadata': {}, 'source': texto.strip('\n').splitlines(keepends=True)}


def code(texto: str) -> dict:
    return {'cell_type': 'code', 'metadata': {}, 'execution_count': None, 'outputs': [],
            'source': texto.strip('\n').splitlines(keepends=True)}


def descarga(nombre: str) -> list[dict]:
    """Celdas finales comunes: exportan todo y, en Colab, descargan el ZIP."""
    return [
        md(r'''
## Descargar todos los resultados

ZIP con el Excel (una hoja por tabla), los gráficos en PNG (`graficos/`) y las tablas en CSV
(`csv/`). En Colab se descarga solo; en la PC queda en la carpeta `_descargas/` del repo.
'''),
        code(f'''from src.exportar import zip_resultados
zip_path = zip_resultados(R, '{nombre}')
print('ZIP:', zip_path)
if 'google.colab' in sys.modules:
    from google.colab import files
    files.download(str(zip_path))'''),
    ]


def guardar(nombre: str, celdas: list[dict]) -> None:
    nb = {'cells': celdas, 'metadata': {
        'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
        'language_info': {'name': 'python'}, 'colab': {'provenance': []}},
        'nbformat': 4, 'nbformat_minor': 5}
    ruta = RAIZ / 'notebooks' / nombre
    ruta.parent.mkdir(exist_ok=True)
    ruta.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('escrito', ruta.relative_to(RAIZ))


# ------------------------------------------------------------------------------------------------
NB01 = [
    md(r'''
# 01 · Índice inmobiliario: alquiler y m² medidos en salarios

[![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/santiagoriverti/indice_inmobiliario_argentina/blob/main/notebooks/01_indice_inmobiliario.ipynb)

Dos indicadores mensuales para CABA y el GBA (Norte, Oeste y Sur):

1. **Costo de alquilar**: alquiler de un 2 ambientes de 50 m² (+ expensas, solo CABA) como % del salario.
2. **Costo de comprar**: cuántos salarios hacen falta para pagar un m² (precio en USD pasado a pesos).

Salario principal: **mediana** de la remuneración bruta de los asalariados privados registrados (SIPA),
sin aguinaldo. Alternativa: **RIPTE** (promedio). Dólar principal: **MEP**; el oficial va como comparación.
Precios: **Zonaprop Index** (precios publicados en avisos, no de cierre). Detalle en `CONTEXTO.md`.
'''),
    code(SETUP),
    code(r'''R = pipeline.construir(refrescar=True)   # baja salarios, IPC y dolar; Zonaprop viene del repo
T = R['indice']'''),
    md(r'''
## Último dato por región
'''),
    code(r'''display(exportar.ultimo_dato(T))'''),
    md(r'''
## Alquiler como % del salario

Línea llena: solo alquiler. Línea punteada: alquiler + expensas (CABA).
'''),
    code(r'''fig = graficos.pct_salario(T, 'mediana'); plt.show()
fig = graficos.pct_salario(T, 'ripte'); plt.show()'''),
    md(r'''
## Salarios necesarios para comprar un m²
'''),
    code(r'''fig = graficos.salarios_m2(T, 'mediana'); plt.show()
fig = graficos.salarios_m2(T, 'ripte'); plt.show()'''),
    md(r'''
## Promedios anuales (CABA)
'''),
    code(r'''cols = ['pct_alquiler_mediana', 'pct_alquiler_expensas_mediana', 'salarios_por_m2_mediana_mep',
        'salarios_por_m2_mediana_oficial', 'pct_alquiler_ripte', 'salarios_por_m2_ripte_mep']
caba = T[T['region'] == 'CABA'].copy()
caba['anio'] = caba['periodo'].dt.year
display(caba.groupby('anio')[cols].mean().round(2))'''),
    md(r'''
## De dónde sale cada dato de Zonaprop

`publicado` = cifra del informe de ese mes; `derivado_*` = calculado con la variación que publica otro
informe; `interpolado` = hueco completado (ver `CONTEXTO.md`).
'''),
    code(r'''display(R['zonaprop'].groupby(['region', 'tipo_alquiler']).size().unstack(fill_value=0))
display(R['zonaprop'].groupby(['region', 'tipo_venta']).size().unstack(fill_value=0))'''),
    *descarga('indice_inmobiliario'),
]


if __name__ == '__main__':
    guardar('01_indice_inmobiliario.ipynb', NB01)
