"""Graficos PNG (matplotlib). Un color fijo por region (paleta categorica validada, orden fijo)."""
from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

COLORES = {'CABA': '#2a78d6', 'GBA_NORTE': '#eb6834', 'GBA_OESTE': '#1baf7a', 'GBA_SUR': '#eda100'}
NOMBRES = {'CABA': 'CABA', 'GBA_NORTE': 'GBA Norte', 'GBA_OESTE': 'GBA Oeste', 'GBA_SUR': 'GBA Sur'}
TINTA, TINTA_2, GRILLA, EJE = '#0b0b0b', '#52514e', '#e1e0d9', '#c3c2b7'


def _estilo(ax, titulo: str, subtitulo: str, ylabel: str) -> None:
    ax.set_title(titulo, loc='left', fontsize=12, color=TINTA, pad=22)
    ax.text(0, 1.02, subtitulo, transform=ax.transAxes, fontsize=9, color=TINTA_2)
    ax.set_ylabel(ylabel, color=TINTA_2, fontsize=9)
    ax.grid(axis='y', color=GRILLA, linewidth=0.8)
    ax.set_axisbelow(True)
    for lado in ('top', 'right', 'left'):
        ax.spines[lado].set_visible(False)
    ax.spines['bottom'].set_color(EJE)
    ax.tick_params(colors=TINTA_2, labelsize=8, length=0)


def _x(d: pd.DataFrame):
    return d['periodo'].dt.to_timestamp() if hasattr(d['periodo'], 'dt') else d['periodo']


def _etiqueta_final(ax, x, y, texto: str, color: str) -> None:
    """Punto en el ultimo dato; el texto se ubica despues con `_ubicar_etiquetas` (sin pisarse)."""
    ax.plot(x.iloc[-1], y.iloc[-1], 'o', ms=4, color=color)
    ax._etiquetas = getattr(ax, '_etiquetas', []) + [(x.iloc[-1], float(y.iloc[-1]), texto)]


def _ubicar_etiquetas(ax, separacion: float = 0.045) -> None:
    """Escribe las etiquetas finales separandolas verticalmente (fraccion del rango del eje y)."""
    items = sorted(getattr(ax, '_etiquetas', []), key=lambda e: e[1])
    lo, hi = ax.get_ylim()
    paso = separacion * (hi - lo)
    pos = []
    for _, y, _ in items:
        pos.append(max(y, pos[-1] + paso) if pos else y)
    for (x, _, texto), yp in zip(items, pos):
        ax.text(x, yp, '  ' + texto, fontsize=8, color=TINTA, va='center', ha='left', clip_on=False)


def pct_salario(tabla: pd.DataFrame, salario: str = 'mediana') -> plt.Figure:
    fig, ax = plt.subplots(figsize=(10, 5.2), dpi=130)
    for reg, d in tabla.groupby('region', sort=False):
        d = d.dropna(subset=[f'pct_alquiler_{salario}'])
        if d.empty:
            continue
        x, c = _x(d), COLORES[reg]
        y = d[f'pct_alquiler_{salario}']
        ax.plot(x, y, color=c, lw=2, label=f'{NOMBRES[reg]}: alquiler')
        _etiqueta_final(ax, x, y, f'{y.iloc[-1]:.0f}%', c)
        ye = d[f'pct_alquiler_expensas_{salario}']
        if ye.notna().any():
            de = d[ye.notna()]
            ax.plot(_x(de), ye[ye.notna()], color=c, lw=2, ls='--',
                    label=f'{NOMBRES[reg]}: alquiler + expensas')
            _etiqueta_final(ax, _x(de), ye[ye.notna()], f'{ye.dropna().iloc[-1]:.0f}%', c)
    nombre = 'salario mediano' if salario == 'mediana' else 'RIPTE'
    _estilo(ax, f'Alquiler de un 2 ambientes como % del {nombre}',
            'Alquiler medio publicado de un 2 ambientes de 50 m2 (Zonaprop); salario bruto sin aguinaldo',
            '% del salario')
    ax.set_ylim(bottom=0)
    _ubicar_etiquetas(ax)
    ax.legend(frameon=False, fontsize=8, loc='upper left', ncol=2)
    fig.tight_layout()
    return fig


def salarios_m2(tabla: pd.DataFrame, salario: str = 'mediana') -> plt.Figure:
    fig, ax = plt.subplots(figsize=(10, 5.2), dpi=130)
    for reg, d in tabla.groupby('region', sort=False):
        col = f'salarios_por_m2_{salario}_mep'
        d = d.dropna(subset=[col])
        if d.empty:
            continue
        x, c = _x(d), COLORES[reg]
        ax.plot(x, d[col], color=c, lw=2, label=f'{NOMBRES[reg]} (dolar MEP)')
        _etiqueta_final(ax, x, d[col], f'{d[col].iloc[-1]:.1f}', c)
        if reg == 'CABA':
            col_o = f'salarios_por_m2_{salario}_oficial'
            do = d.dropna(subset=[col_o])
            ax.plot(_x(do), do[col_o], color=c, lw=1.2, ls=':', label='CABA (dolar oficial)')
    nombre = 'salarios medianos' if salario == 'mediana' else 'salarios RIPTE'
    _estilo(ax, f'Cuantos {nombre} cuesta un m2',
            'Precio medio publicado de departamentos (USD/m2, Zonaprop) pasado a pesos; salario bruto sin aguinaldo',
            f'{nombre} por m2')
    ax.set_ylim(bottom=0)
    _ubicar_etiquetas(ax)
    ax.legend(frameon=False, fontsize=8, loc='upper left', ncol=2)
    fig.tight_layout()
    return fig


def todos(tabla: pd.DataFrame) -> dict[str, plt.Figure]:
    return {
        'G01_alquiler_pct_salario_mediano': pct_salario(tabla, 'mediana'),
        'G02_alquiler_pct_ripte': pct_salario(tabla, 'ripte'),
        'G03_salarios_por_m2_mediano': salarios_m2(tabla, 'mediana'),
        'G04_salarios_por_m2_ripte': salarios_m2(tabla, 'ripte'),
    }
